from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Test different sites
test_sites = [
    "https://ca.jooble.org/SearchResult?ukw=data+science+intern&rgns=Ottawa%2C+ON",
    "https://www.glassdoor.ca/Job/ottawa-data-science-intern-jobs-SRCH_IL.0,6_IC2281069_KO7,26.htm",
    "https://workopolis.com/jobsearch/find-jobs?ak=data+science+intern&l=ottawa%2C+on",
]

for i, url in enumerate(test_sites):
    try:
        print(f"\n🧪 Testing site {i + 1}: {url}")
        driver.get(url)
        time.sleep(3)

        print(f"Title: {driver.title}")

        # Look for common job listing indicators
        job_indicators = [
            "div[class*='job']",
            "article[class*='job']",
            "[data-testid*='job']",
            ".job-card",
            ".listing"
        ]

        total_jobs = 0
        for selector in job_indicators:
            jobs = driver.find_elements(By.CSS_SELECTOR, selector)
            total_jobs = max(total_jobs, len(jobs))

        print(f"Potential job elements found: {total_jobs}")

        if "blocked" not in driver.page_source.lower() and "captcha" not in driver.page_source.lower():
            print("✅ Site seems accessible!")
        else:
            print("❌ Site has protection")

    except Exception as e:
        print(f"❌ Error: {e}")

driver.quit()