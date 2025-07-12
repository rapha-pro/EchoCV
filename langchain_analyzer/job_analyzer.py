import os
import pandas as pd
from pathlib import Path
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain.output_parsers import ResponseSchema, StructuredOutputParser


# Load environment variables
load_dotenv()


class JobAnalyzer:
    def __init__(self):
        """Initialize the job analyzer with Groq and output parser"""
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.1
        )

        # Define the response schema
        self.response_schemas = [
            ResponseSchema(name="title", description="Clean job title without dates, locations, or extra details"),
            ResponseSchema(name="company",
                           description="Standardized company name (e.g., 'Advanced Micro Devices' → 'AMD')"),
            ResponseSchema(name="location", description="Standardized location format: City, Province/State, Country"),
            ResponseSchema(name="salary", description="Clean salary range without extra text"),
            ResponseSchema(name="duration", description="Duration if specified (e.g., '4 months', '8 months', 'not_specified')"),
            ResponseSchema(name="start_season", description="Start season/time (e.g., 'Fall 2025', 'Summer 2024', 'not_specified')"),
            ResponseSchema(name="work_arrangement", description="Work arrangement (remote/hybrid/onsite/not_specified)"),
            ResponseSchema(name="technical_skills", description="List of technical skills required", type="list"),
            ResponseSchema(name="experience_level", description="Required experience level: entry/internship/junior/mid/senior"),
            ResponseSchema(name="job_type", description="Type of position: internship/co-op/full-time/contract"),
            ResponseSchema(name="education_requirements", description="Specific degree or education requirements"),
            ResponseSchema(name="key_responsibilities", description="Main job responsibilities", type="list"),
            ResponseSchema(name="company_culture_indicators", description="Indicators of company culture", type="list"),
            ResponseSchema(name="internship_fit_score", description="Job fit score for 3rd year student (1-10)",
                           type="int"),
            ResponseSchema(name="reasons_for_score", description="Explanation for the fit score")
        ]

        # Create output parser
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        self.analysis_chain = self._create_analysis_chain()

        print("Job Analyzer initialized")


    def _create_analysis_chain(self):
        """Create the job analysis chain"""

        prompt_template = PromptTemplate(
            input_variables=["title", "company", "location", "salary", "description"],
            template="""
            Analyze this job posting for a 3rd year university student (who hasn't started 3rd year yet)
            seeking data science internships. As a little bit of my skills, I completed the data science module of a data science certification
            with statistics, data analysis, visualization with matplotlib, pandas, numpy, python

            JOB TITLE: {title}
            COMPANY: {company}
            LOCATION: {location}
            SALARY: {salary}
            DESCRIPTION: {description}

            Focus on extracting concrete information. If something isn't mentioned, look up the company online, and answer
            to your best knowledge. If you still don't figure it out after searching, use "not_specified".
            Return output only in a clean JSON format

            {format_instructions}
            """,
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

        return LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            output_parser=self.output_parser,
            verbose=True
        )


    def analyze_single_job(self, job_data):
        """Analyze a single job using the chain"""

        try:
            # Run the analysis chain
            result = self.analysis_chain.run(
                title=job_data['title'],
                company = job_data['company'],
                location = job_data['location'],
                salary = job_data['salary'],
                description = job_data.get('description')
            )

            return result

        except Exception as e:
            print(f"❌ Chain execution failed: {e}")
            return None


    def analyze_multiple_jobs(self, jobs_data, max_jobs=3):
        """Analyze multiple jobs using the chain"""
        results = []

        if max_jobs is None:
            max_jobs = len(jobs_data)

        print(f"🔗 Running analysis chain on {max_jobs} jobs")

        for i, job in enumerate(jobs_data[:max_jobs]):
            print(f"\nJob {i + 1}/{max_jobs}: {job['title'][:50]}")

            analysis = self.analyze_single_job(job)
            if analysis:
                results.append(analysis)
                print(f"Scored: {analysis['internship_fit_score']}/10")

        return results




def test_single_job_analysis():
    """Test the chain-based analyzer"""

    # Load data
    data_dir = Path(__file__).parent.parent / "data" / "scrapped_data"
    csv_files = list(data_dir.glob("glassdoor_jobs_*.csv"))

    if not csv_files:
        print("No job data found! CSV file does not exist")
        return

    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    df = pd.read_csv(latest_file)

    if len(df) == 0:
        print("❌ No jobs found in dataframe")
        return

    # Test chain
    analyzer = JobAnalyzer()
    first_job = df.iloc[0].to_dict()
    print(f"Printing first job from df\nTo dict:\n{json.dumps(first_job, indent=4, sort_keys=True)}")

    print(f"\n🔗 Testing LangChain analysis...")
    analysis = analyzer.analyze_single_job(first_job)

    if analysis:
        print(f"\n🎯 Chain Results: {json.dumps(analysis, indent=4, sort_keys=True)}")



if __name__ == "__main__":
    test_single_job_analysis()