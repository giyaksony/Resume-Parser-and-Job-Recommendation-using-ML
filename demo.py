import pandas as pd
import ast
from pyresparser import ResumeParser
# import nltk
# nltk.download('stopwords')

# This part is triggered by a user's action in the UI.
# The 'uploaded_resume_file' would be the file sent from the browser.
def process_resume_and_match_jobs(uploaded_resume_file):
    # Step 1: Parse the uploaded resume to get skills
    resume_data = ResumeParser(uploaded_resume_file).get_extracted_data()
    resume_skills = resume_data.get("skills", [])
    
    # Step 2: Load the dataset and convert the 'Skill List' column
    df = pd.read_csv('cleaned_no_identifiers.csv')
    df['Skill List'] = df['Skill List'].apply(ast.literal_eval)

    # Step 3: Match resume skills to job skills
    def calculate_match_score(job_skills, resume_skills):
        job_skills_set = set(job_skills)
        resume_skills_set = set(resume_skills)
        matched_skills = job_skills_set.intersection(resume_skills_set)
        return len(matched_skills)

    # Apply the function to each row to get the match score
    if resume_skills:
        df['match_score'] = df['Skill List'].apply(lambda x: calculate_match_score(x, resume_skills))

        # Sort and get the top 5 matches
        top_matches = df.sort_values(by='match_score', ascending=False).head(5)
        
        # Return the results to be displayed in the UI
        return top_matches[['Job Title', 'match_score', 'Key Skills']]
    else:
        return "No skills were extracted from the resume. Cannot perform job matching."
    
    