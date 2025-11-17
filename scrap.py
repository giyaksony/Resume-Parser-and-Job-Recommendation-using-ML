from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

# ---------------------------
# Step 1: Candidate Summary
# ---------------------------
# This should come from your resume parser
candidate_skills = ["python", "machine learning", "django", "data analysis", "sql"]
candidate_experience_years = 3  # Example, from resume
resume_summary = " ".join(candidate_skills) + f" {candidate_experience_years} years"

# ---------------------------
# Step 2: Selenium Setup
# ---------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

# ---------------------------
# Step 3: Construct search URL
# ---------------------------
job_title_input = "python developer"  # Optional: dynamic based on resume
location_input = ""  # Optional
base_url = f"https://www.indeed.co.in/jobs?q={job_title_input.replace(' ','+')}&l={location_input}&start="

job_titles = []
job_descriptions = []
max_pages = 3  # Scrape top 3 pages

for page in range(max_pages):
    url = base_url + str(page * 10)
    driver.get(url)
    time.sleep(2)

    # Accept cookies if popup exists
    try:
        driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
    except:
        pass

    # Scrape job titles
    try:
        jobs_on_page = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2.jobTitle span"))
        )
        for job in jobs_on_page:
            title = job.text.strip()
            if title and title not in job_titles:
                job_titles.append(title)
    except TimeoutException:
        print(f"No jobs found on page {page+1}")

    # Scrape job descriptions (short snippet)
    try:
        descriptions_on_page = driver.find_elements(By.CSS_SELECTOR, "div.job-snippet")
        for desc in descriptions_on_page:
            text = desc.text.strip().replace("\n", " ")
            if text and text not in job_descriptions:
                job_descriptions.append(text)
    except:
        job_descriptions.extend([""] * len(jobs_on_page))  # If description missing

driver.quit()

# ---------------------------
# Step 4: TF-IDF + Cosine Similarity
# ---------------------------
if len(job_titles) == 0:
    print("❌ No jobs scraped from Indeed")
else:
    # Combine job title + description
    all_job_texts = [f"{t} {d}" for t, d in zip(job_titles, job_descriptions)]
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_summary] + all_job_texts)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Top 5 recommendations
    top_indices = similarities.argsort()[-5:][::-1]

    print("\n🎯 Top 5 Job Recommendations:\n")
    for i in top_indices:
        print(f"{job_titles[i]} — {similarities[i]*100:.2f}% match")
