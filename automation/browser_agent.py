import os
import sys
from pathlib import Path
import asyncio
import time
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))

from integration.job_rag_integration import JobRAGIntegration
from utility.text_styles import Colors, success, error, warning, info, question, header

load_dotenv()


import asyncio
from playwright.async_api import async_playwright
from pathlib import Path


class JobApplicationAgent:
    def __init__(self):
        """Initialize intelligent job application agent"""
        print("🤖 Initializing Job Application Agent")

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Setup logs directory
        self.logs_dir = Path(__file__).parent.parent / "logs" / "screenshots"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        print("Job Application agent ready")


    async def start_browser(self, headless=False):
        """Start the browser with optimal settings"""

        print(info("Starting browser..."))

        self.playwright = await async_playwright().start()

        # Launch browser with human-like settings
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-first-run',    # skip chrome's first-time setup wizard to prevent pop-ups
                '--disable-blink-features=AutomationControlled',   # removes the flag "Chrome is being controlled by automated software"
                '--disable-web-security',   # disables CORS. allow to interact with forms across domains
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ]
        )

        # Create context with human-like behavior
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Create page
        self.page = await self.context.new_page()

        print(success("Browser started successfully"))


    async def apply_to_job(self, job_url, job_data):
        """Main method: Navigate to job and attempt to apply"""

        print(f"\n{header('Starting Job Application Process')}")
        print(f"Job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
        print(f"URL: {job_url}")

        try:
            await self._navigate_to_job(job_url)

            apply_success = await self._find_and_click_apply()

            if not apply_success:
                return {"success": False, "error": "Could not find apply button"}

            # Fill out the application form
            form_success = await self._fill_application_form(job_data)

            if not form_success:
                return {"success": False, "error": "Could not fill application form"}

            # Review application (doesn't submit automatically)
            await self._review_application()

            return {"success": True, "message": "Application completed and ready for review"}

        except Exception as e:
            return {"success": False, "error": f"Application failed: {str(e)}"}


    def _get_screenshot_path(self, filename):
        """Get full path for screenshot file"""
        return str(self.logs_dir / filename)


    async def _take_screenshot(self, filename, description=""):
        """Take screenshot with consistent path and logging"""
        screenshot_path = self._get_screenshot_path(filename)
        await self.page.screenshot(path=screenshot_path)

        if description:
            print(info(f"{description} - Screenshot saved: {filename}"))
        else:
            print(info(f"Screenshot saved: {filename}"))

        return screenshot_path


    async def _navigate_to_job(self, job_url):
        """Navigate to the job posting page"""

        print(info(f"Navigating to: {job_url}"))

        # networkidle waits for all network request to finish
        # ideal of modern websites. Waits for all content to load
        await self.page.goto(job_url, wait_until='networkidle')

        # extra time for dynamic content to load
        await asyncio.sleep(2)

        # Take screenshot using helper method
        await self._take_screenshot("job_page.png", "Job page loaded")



# basic setup
async def test_advanced_browser():
    """Test the advanced browser setup"""
    agent = JobApplicationAgent()

    print("Testing advanced browser with anti-detection features...")

    # Start browser
    await agent.start_browser(headless=False)

    # Navigate to a site that detects automation
    print(info("Navigating to automation detection test site..."))
    await agent.page.goto('https://bot.sannysoft.com/')

    # Wait so we can see the results
    print("Check the browser window - how many red warnings do you see?")
    await asyncio.sleep(10)

    # Close browser
    await agent.close_browser()


if __name__ == "__main__":
    asyncio.run(test_advanced_browser())