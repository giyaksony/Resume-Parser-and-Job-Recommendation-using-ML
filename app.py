import os
import re
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, session
from werkzeug.utils import secure_filename
from pyresparser import ResumeParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Load job dataset
df = pd.read_csv('datasets/cleaned_no_identifiers.csv')


# -------------------- Helper Functions --------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def extract_full_name(file_path, extracted_name):
    """Extracts a cleaner name using PDF text or OCR."""
    try:
        text = extract_text(file_path)

        if text and extracted_name:
            first_lines = text.split("\n")[:7]
        else:
            print("⚠️ Using OCR for name extraction...")
            pages = convert_from_path(file_path, first_page=1, last_page=1)
            if not pages:
                return extracted_name

            ocr_text = pytesseract.image_to_string(pages[0])
            first_lines = ocr_text.split("\n")[:7]

        def normalize(s):
            return ''.join(c.lower() for c in s if c.isalnum())

        target_norm = normalize(extracted_name.split()[0]) if extracted_name else ""

        for line in first_lines:
            line_norm = normalize(line)
            if target_norm and target_norm in line_norm:
                return line.strip()

        return extracted_name

    except Exception as e:
        print("Error extracting name:", e)
        return extracted_name


# -------------------- KNN Class --------------------
class KNN:
    def __init__(self, k):
        self.k = k

    def fit(self, X, y):
        self.X_train = X
        self.y_train = y

    def predict(self, X):
        top_jobs = []
        for x in X:
            distances = np.sqrt(((self.X_train - x) ** 2).sum(axis=1))
            top_k_idx = distances.argsort()[:self.k]
            top_jobs.append([self.y_train[i] for i in top_k_idx])
        return top_jobs


# -------------------- Routes --------------------
@app.route('/')
def index():
    return render_template("index1.html")


@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        file = request.files.get('resume')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)

            # Extract resume details
            resume = ResumeParser(file_path).get_extracted_data()
            resume_name = extract_full_name(file_path, resume.get("name", "Not Found"))
            skills = resume.get('skills', [])

            if not skills:
                skills = ["No Skills Found"]

            session['skillsList'] = skills

            # -------------------- Job Matching --------------------
            jobDesc = df['Key Skills'].fillna('').str.replace('|', ' ').str.lower().values
            resume_text = " ".join(skills).lower()

            # TF-IDF Vectorization
            vectorizer = TfidfVectorizer(analyzer='word')
            job_vecs = vectorizer.fit_transform(jobDesc)
            resume_vec = vectorizer.transform([resume_text])

            # Step 1: Cosine similarity to filter top 20
            similarities = cosine_similarity(resume_vec, job_vecs).flatten()

            top_n = 20
            top_n_indices = similarities.argsort()[-top_n:][::-1]

            candidate_vecs = job_vecs[top_n_indices].toarray()
            candidate_titles = df.iloc[top_n_indices]['Job Title'].values

            # Step 2: Apply KNN
            knn_model = KNN(k=5)
            knn_model.fit(candidate_vecs, candidate_titles)
            final_jobs = knn_model.predict(resume_vec.toarray())[0]

            # Attach similarity scores
            final_matches = []
            for job in final_jobs:
                idx = df.index[df['Job Title'] == job][0]
                score = round(similarities[idx] * 100, 2)
                final_matches.append([job, score])

            final_matches.sort(key=lambda x: x[1], reverse=True)

            return render_template(
                "joblist.html",
                name=resume_name,
                skills=skills,
                joblist=final_matches,
                resume_path=file_path
            )

        else:
            return "Invalid file format. Please upload a PDF.", 400

    return render_template("joblist.html")


# -------------------- Main --------------------
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
