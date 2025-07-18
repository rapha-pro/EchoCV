import asyncio
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.llm import ChatGroq
from pathlib import Path
import sys
import os

sys.path.append(str(Path(__file__).parent.parent))
from utility.document_manager import DocumentManager
from utility.text_styles import header, success, info, warning, error


load_dotenv()

async def main():
    agent = Agent(
        task="go to this website and extract all the input fields and print it out: https://boards.greenhouse.io/embed/job_app?token=6642169003&utm_source=Simplify&ref=Simplify",
        llm=ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")
    )
    await agent.run()

asyncio.run(main())


class PersonalInfo:
    """Manages personal information from environment variables"""

    def __init__(self):
        # Basic personal info
        self.first_name = os.getenv("PERSONAL_FIRST_NAME", "")
        self.last_name = os.getenv("PERSONAL_LAST_NAME", "")
        self.email = os.getenv("PERSONAL_EMAIL", "")
        self.phone = os.getenv("PERSONAL_PHONE", "")
        self.address = os.getenv("PERSONAL_ADDRESS", "")
        self.linkedin = os.getenv("PERSONAL_LINKEDIN", "")
        self.github = os.getenv("PERSONAL_GITHUB", "")
        self.portfolio = os.getenv("PERSONAL_PORTFOLIO", "")
        self.years_experience = os.getenv("PERSONAL_YEARS_EXPERIENCE", "")
        self.current_title = os.getenv("PERSONAL_CURRENT_TITLE", "")
        self.availability = os.getenv("PERSONAL_AVAILABILITY", "")
        self.salary_expectation = os.getenv("PERSONAL_SALARY_EXPECTATION", "")

        # Education info
        self.graduation_year = os.getenv("PERSONAL_GRADUATION_YEAR", "")
        self.graduation_month = os.getenv("PERSONAL_GRADUATION_MONTH", "")
        self.school_name = os.getenv("PERSONAL_SCHOOL_NAME", "")
        self.degree = os.getenv("PERSONAL_DEGREE", "")
        self.degree_program = os.getenv("PERSONAL_DEGREE_PROGRAM", "")
        self.gpa = os.getenv("PERSONAL_GPA", "")

        # Resume file
        self.resume_path = os.getenv("PERSONAL_RESUME_PATH", "data/personal_data/Tech_resume.pdf")

        self.validate_info()

    def validate_info(self):
        """Validate that required personal info is provided"""

        required_fields = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone
        }

        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            print(warning(f"Missing personal info in .env: {', '.join(missing_fields)}"))
            print("Please update your .env file with personal information")
        else:
            print(success("✅ Personal information loaded from .env"))

    def get_full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self):
        """Convert to dictionary for easy access"""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.get_full_name(),
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
            "years_experience": self.years_experience,
            "current_title": self.current_title,
            "availability": self.availability,
            "salary_expectation": self.salary_expectation,
            "graduation_year": self.graduation_year,
            "graduation_month": self.graduation_month,
            "school_name": self.school_name,
            "degree": self.degree,
            "degree program": self.degree_program,
            "gpa": self.gpa,
            "resume_path": self.resume_path

        }




class SimpleJobAgent:
    """Simple job application agent - building step by step"""

    def __init__(self):
        print(header("Initializing Simple Job Agent"))

        # Load personal info and document manager
        self.personal_info = PersonalInfo()
        self.doc_manager = DocumentManager()

        # Setup LLM with correct model
        self.llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct"
        )

        print(success("✅ Simple Job Agent Ready"))

    async def fill_basic_form(self, url):
        """
        Step 1: Navigate to URL, fill basic personal info fields, take screenshot
        This is our first method - keeping it simple
        """

        print(f"\n{header('Step 1: Fill Basic Form')}")
        print(f"🔗 URL: {url}")
        print(f"👤 Applicant: {self.personal_info.get_full_name()}")

        # Get personal info
        personal_data = self.personal_info.to_dict()

        # Create the task for browser_use
        fill_task = f"""
        Go to this website: {url}

        When the page loads:
        1. Take a screenshot first (before filling anything)

        2. Look for input fields and fill them with this personal information 
            corresponding it's appropriate key from this dict:
           {personal_data}
           
        3. Make sure to fill every input which matches any key above.
           For the resume, upload/attach the resume from the resume path given
           to you in the dict given above

        4. Take another screenshot after filling the fields

        5. DO NOT submit the form or click any submit buttons

        6. Report back what fields you found and filled

        Important: fill the fields,  but do not submit anything.
        """

        try:
            print(info("🤖 Starting form filling..."))

            # Create agent with the task
            agent = Agent(
                task=fill_task,
                llm=self.llm
            )

            # Run the agent
            result = await agent.run()

            print(success("✅ Form filling completed"))
            print(f"Agent report: {result}")

            return {
                "success": True,
                "message": "Form filled with personal information",
                "agent_report": result
            }

        except Exception as e:
            print(error(f"Form filling failed: {e}"))
            return {
                "success": False,
                "error": str(e)
            }


async def test_basic_form_filling():
    """Test the basic form filling functionality"""

    print(header("Testing Basic Form Filling"))

    # Test URL
    test_url = "https://boards.greenhouse.io/embed/job_app?token=6642169003&utm_source=Simplify&ref=Simplify"

    # Create agent
    agent = SimpleJobAgent()

    # Test personal info loading
    print(f"\nPersonal Info:")
    personal_data = agent.personal_info.to_dict()
    print(personal_data)

    # Ask user if they want to proceed
    # proceed = input(f"\n{info('Proceed with form filling test? (y/n): ')}").strip().lower()
    proceed = 'y'

    if proceed == 'y':
        print(f"\n{header('Starting Form Fill Test')}")

        # Run the form filling test
        result = await agent.fill_basic_form(test_url)

        print(f"\n{header('Test Results:')}")
        print(f"Success: {result['success']}")

        if result['success']:
            print(f"✅ Message: {result['message']}")
            print(f"📋 Details: {result['agent_report']}")
        else:
            print(f"❌ Error: {result['error']}")

        print(f"\n{info('Check your browser window to see the filled form!')}")
        print(f"{warning('The form was NOT submitted - review it manually')}")

    else:
        print(info("Skipping form filling test"))


if __name__ == "__main__":
    asyncio.run(test_basic_form_filling())