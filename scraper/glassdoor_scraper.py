from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from pathlib import Path
import time



class GlassdoorScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with stealth options"""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        if headless:
            self.chrome_options.add_argument("--headless")  # Run without GUI

        self.service = Service(ChromeDriverManager().install())
        self.driver = None
        self.wait = None

    def start_driver(self):
        """Start the Chrome driver"""
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)  # 10-second timeout
        print("✅ Driver started")

    def scrape_jobs(self, query, location, max_jobs=20):
        """Scrape jobs from Glassdoor"""
        if not self.driver:
            self.start_driver()

        # Build URL
        base_url = "https://www.glassdoor.ca/Job/jobs.htm"
        search_url = f"{base_url}?sc.keyword={query}&locT=C&locId=2281069&locKeyword={location}"

        print(f"🔍 Searching for: {query} in {location}")
        self.driver.get(search_url)

        # Wait for job listings to load
        try:
            job_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-test='jobListing']"))
            )
            print(f"✅ Found {len(job_elements)} job listings")
        except:
            print("❌ No jobs found or page didn't load properly")
            return []

        jobs_data = []

        for i, job in enumerate(job_elements[:max_jobs]):
            try:
                job_data = self._extract_job_data(job, i + 1)
                if job_data:
                    jobs_data.append(job_data)

            except Exception as e:
                print(f"❌ Error extracting job {i + 1}: {e}")

        return jobs_data

    def _extract_job_data(self, job_element, job_num):
        """Extract data from a single job element"""
        try:
            # Job title
            title_elem = job_element.find_element(By.CSS_SELECTOR, "a[data-test='job-title']")
            title = self._clean_text(title_elem.text)
            job_url = title_elem.get_attribute('href')

            # Company name
            company_elem = job_element.find_element(By.CSS_SELECTOR, "span.EmployerProfile_compactEmployerName__9MGcV")
            company = self._clean_text(company_elem.text)

            # Location
            location_elem = job_element.find_element(By.CSS_SELECTOR, "div[data-test='emp-location']")
            location = self._clean_text(location_elem.text)

            # Salary (optional)
            try:
                salary_elem = job_element.find_element(By.CSS_SELECTOR, "div[data-test='detailSalary']")
                salary = self._clean_text(salary_elem.text)
            except:
                salary = "Not specified"

            # Job description snippet and skills
            try:
                desc_elem = job_element.find_element(By.CSS_SELECTOR, "div[data-test='descSnippet']")
                full_desc = self._clean_text(desc_elem.text)

                # Extract skills
                skills = self._extract_skills(desc_elem)

                # Clean description
                if "Skills:" in full_desc:
                    description = full_desc.split("Skills:")[0].strip()[:200] + "..."
                else:
                    description = full_desc[:200] + "..."

            except:
                description = "No description available"
                skills = "Not specified"

            job_data = {
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'skills': skills,
                'description': description,
                'url': job_url
            }

            print(f"✅ Extracted job {job_num}: {title} at {company}")
            if skills != "Not specified":
                print(f"   🛠️  Skills: {skills}")

            return job_data

        except Exception as e:
            print(f"❌ Failed to extract job {job_num}: {e}")
            return None

    def _extract_skills(self, desc_element):
        """Extract skills from job description element"""
        try:
            # Look for the skills section specifically
            skill_divs = desc_element.find_elements(By.XPATH, ".//div[contains(., 'Skills:')]")

            if skill_divs:
                skills_text = skill_divs[0].text
                # Extract everything after "Skills:"
                if "Skills:" in skills_text:
                    skills_part = skills_text.split("Skills:")[1].strip()
                    return skills_part

            # Alternative: look for bold "Skills:" tag
            try:
                skills_bold = desc_element.find_element(By.XPATH, ".//b[text()='Skills:']")
                # Get the next sibling or parent text
                parent = skills_bold.find_element(By.XPATH, "./..")
                skills_text = parent.text
                if "Skills:" in skills_text:
                    return skills_text.split("Skills:")[1].strip()
            except:
                pass

            return "Not specified"

        except Exception as e:
            return "Not specified"

    def _clean_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""

        # Remove extra whitespace and newlines
        cleaned = " ".join(text.split())

        # Remove common unwanted characters
        cleaned = cleaned.replace('\n', ' ').replace('\t', ' ')

        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()

        return cleaned

    def save_to_csv(self, jobs_data, filename="jobs.csv"):
        """Save jobs data to CSV file"""
        if not jobs_data:
            print("❌ No data to save")
            return

        # Get the project root (one directory up from scraper/)
        current_file = Path(__file__)
        project_root = current_file.parent.parent
        data_dir = project_root / "data"  # /jobflow/data/

        # Create data directory if it doesn't exist
        data_dir.mkdir(exist_ok=True)
        print(f"📁 Using data directory: {data_dir}")

        # Save to CSV
        df = pd.DataFrame(jobs_data)
        filepath = data_dir / filename
        df.to_csv(filepath, index=False)
        print(f"✅ Saved {len(jobs_data)} jobs to {filepath}")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✅ Browser closed")



if __name__ == "__main__":
    scraper = GlassdoorScraper()

    try:
        jobs = scraper.scrape_jobs(
            query="data science intern",
            location="canada",
            max_jobs=10
        )

        for job in jobs:
            print(f"\nTitle:\t\t {job['title']}")
            print(f"Company:\t {job['company']}")
            print(f"Location:\t {job['location']}")
            print(f"Salary:\t\t {job['salary']}")

        # Save to CSV
        scraper.save_to_csv(jobs, "glassdoor_jobs.csv")

    finally:
        scraper.close()