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


    async def close_browser(self):
        """Clean up browser resources"""

        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        print(success("Browser closed"))


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
        """Navigate to job page with multiple fallback strategies"""

        print(info(f"\nNavigating to: {job_url}"))

        # try 1: Standard approach
        try:
            print(info("\ntry 1: Standard navigation"))
            await self.page.goto(job_url, wait_until='domcontentloaded', timeout=10000)
            await self._wait_for_page_stability()
            print(success("> Standard navigation successful"))
            return True

        except Exception as e1:
            print(warning(f"try 1 failed: {e1}"))

        # retry 2: Faster loading
        try:
            print(info("retry 2: Fast loading"))
            await self.page.goto(job_url, wait_until='load', timeout=10000)
            await asyncio.sleep(3)
            print(success("> Fast loading successful"))
            return True

        except Exception as e2:
            print(warning(f"retry 2 failed: {e2}"))

        # retry 3: Minimal wait
        try:
            print(info("retry 3: Minimal wait"))
            await self.page.goto(job_url, wait_until='commit', timeout=8000)
            await asyncio.sleep(3)  # Manual wait
            print(success("> Minimal wait successful"))
            return True

        except Exception as e3:
            print(error(f"All navigation strategies failed after 3 retries: {e3}"))
            return False


    async def _wait_for_page_stability(self):
        """Wait for the page to become stable"""

        print(info("Waiting for page stability"))

        try:
            await self.page.wait_for_load_state('networkidle', timeout=5000)
            print(success("Page reached network idle"))
        except:
            print(info("Network idle timeout, using manual wait"))
            await asyncio.sleep(2)

        # take a screenshot for debugging
        await self._take_screenshot("job_page.png", "Job page loaded")
        print(info("Screenshot saved for debugging"))


    async def _find_and_click_apply(self):
        """Find and click the apply button"""

        print(info("Looking for apply button"))

        # Take screenshot before searching
        await self._take_screenshot("before_apply_search.png", "Before searching for apply button")

        # Common apply button selectors
        apply_selectors = [
            'button:has-text("Apply")',
            'a:has-text("Apply")',
            'button:has-text("Apply Now")',
            'a:has-text("Apply Now")',
            '[data-test*="apply"]',
            '.apply-button',
            '#apply-button',
            'button[class*="apply"]',
            'a[class*="apply"]'
        ]

        for selector in apply_selectors:
            try:
                apply_button = self.page.locator(selector).first

                if await apply_button.is_visible():
                    print(success(f"Found apply button: {selector}"))
                    await apply_button.click()
                    await asyncio.sleep(2)  # to wait for form to load
                    await self._take_screenshot("after_apply_click.png", "After clicking apply button")
                    return True
                else:
                    print(warning(f"Element found but not visible: {selector}"))

            except Exception as e:
                continue

        await self._take_screenshot("no_apply_button.png", "No apply button found")
        print(error("No apply button found with any selector"))

        return False



# basic setup
async def test_apply_button_finder():
    """Test the apply button finder on a real job site"""

    agent = JobApplicationAgent()

    try:
        # Start browser
        await agent.start_browser(headless=False)

        # Navigate to a job site (you can replace with a real job URL)
        test_url = input("Enter a job URL to test apply button finder (or press Enter to skip): ").strip()

        if not test_url:
            print(info("Creating a test page with apply button..."))
            # Create a simple test page
            test_html = """
            <html>
            <body>
                <h1>Test Job Posting</h1>
                <button class="apply-button">Apply Now</button>
                <a href="#" data-test="apply-link">Easy Apply</a>
            </body>
            </html>
            """
            await agent.page.set_content(test_html)
        else:
            await agent._navigate_to_job(test_url)

        # Test the apply button finder
        print(f"\n{info('Testing apply button finder...')}")
        found = await agent._find_and_click_apply()

        if found:
            print(success("Apply button test passed!"))
        else:
            print(error("Apply button test failed!"))

        # Keep browser open to see results
        print("Check the browser and screenshots. Browser will close in 10 seconds...")
        await asyncio.sleep(10)

    finally:
        await agent.close_browser()


if __name__ == "__main__":
    asyncio.run(test_apply_button_finder())