from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Step 1: Selenium setup
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without showing browser
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

# Step 2: Open Indeed India homepage
driver.get("https://in.indeed.com/jobs?q=python+developer&l=India&from=searchOnHP%2Cwhatautocomplete%2CwhatautocompleteSourceStandard%2Cwhereautocomplete&vjk=16367f7e0f49f1a6")
time.sleep(2)  # Wait for the page to load

# Step 3: Enter job title and location, then click search
search_box = driver.find_element(By.ID, "text-input-what")
search_box.send_keys("Python Developer")
location_box = driver.find_element(By.ID, "text-input-where")
location_box.clear()  # Clear default location
location_box.send_keys("India")
location_box.send_keys(Keys.RETURN)  # Press Enter to search
time.sleep(3)  # Wait for results to load

# Step 4: Scroll down to load more jobs (simulate user scrolling)
for _ in range(3):  # Adjust the range for more/less scrolling
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(2)

# Step 5: Extract job titles
job_titles = []
try:
    job_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2.jobTitle span"))
    )
    job_titles = [job.text.strip() for job in job_elements if job.text.strip() != ""]
except Exception as e:
    print(f"Error extracting job titles: {e}")

# Step 6: Print the number of jobs found
print(f"✅ Crawled {len(job_titles)} jobs from Indeed India")

# Step 7: Close the browser
driver.quit()
