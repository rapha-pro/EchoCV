
import os
import sys
from pathlib import Path
# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_analyzer.job_analyzer import JobAnalyzer
from rag_system.personal_rag import PersonalRAG
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from question_router import QuestionRouter
from dotenv import load_dotenv
from utility.text_styles import Colors, EXIT_CODES, success, error, warning, info, highlight, question, header, dim


load_dotenv()


class JobRAGIntegration:
    def __init__(self):
        """Initialize complete job application response system"""

        print("Initializing Complete Job-RAG Integration System...")

        # Initialize core components
        self.job_analyzer = JobAnalyzer()
        self.personal_rag = PersonalRAG()
        self.question_router = QuestionRouter()

        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.3
        )

        # Load all integration prompts from files
        self.prompts = self._load_all_integration_prompts()

        print("✅ Complete Job-RAG Integration System ready!")
        print(f"📚 Loaded {len(self.prompts)} prompt templates")

    def _load_all_integration_prompts(self):
        """Load all prompt templates from external files"""

        # Define prompt files in the main prompts directory
        prompt_files = {
            "why_work_here": "why_work_here.txt",
            "experience_match": "experience_match.txt",
            "cover_letter": "cover_letter.txt",
            "flexible": "flexible.txt"
        }

        prompts = {}

        print("Loading job application prompt templates...")

        for name, filename in prompt_files.items():
            template = self._load_prompt_template(filename)
            prompts[name] = template
            print(f"   Loaded: {name}")

        return prompts


    def _load_prompt_template(self, filename):
        """Load a single prompt template from the main prompts directory"""

        try:
            # Load from main prompts directory (jobflow/prompts/)
            prompts_dir = Path(__file__).parent.parent / "prompts" / "integration"
            prompt_file = prompts_dir / filename

            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()

            return template

        except Exception as e:
            print(f"❌ Error loading prompt template {filename}: {e}")
            return self._get_fallback_prompt(filename)


    def _get_fallback_prompt(self, filename):
        """Provide fallback prompts if files are missing"""

        fallbacks = {
            "why_work_here.txt": """
            Answer why you want to work at {company} for the role of {job_title}.

            Use this background: {personal_background}

            Be genuine and enthusiastic.
            """,
            "experience.txt": """
            Explain how your experience relates to this role requiring {technical_skills}.

            Your background: {personal_background}
            """,
            "cover_letter.txt": """
            Write a cover letter for {job_title} at {company}.

            Your background: {personal_background}
            """,
            "flexible.txt": """
            Answer this question: {question}

            Job context: {company} - {job_title}
            Your background: {personal_background}

            Be professional and genuine.
            """
        }

        return fallbacks.get(filename, "Answer this question professionally: {question}")


    def answer_job_question(self, question, job_data):
        """Answer ANY job-related question using both job info and personal background"""

        print(f"> Generating personalized response for: {question}")

        # Classify the question using the router
        classification = self.question_router.classify_question(question)

        question_type = classification.get("question_type", "flexible")
        confidence = classification.get("confidence", "medium")
        reasoning = classification.get("reasoning", "")

        print(f"> Classification: {question_type} (confidence: {confidence})")
        if reasoning:
            print(f"    Reasoning: {reasoning}")

        # Get relevant personal background for this question
        personal_background = self.personal_rag.search_knowledge(question, n_results=6)
        background_text = "\n".join(personal_background['documents'][0]) if personal_background['documents'][
            0] else "No relevant background found in knowledge base."

        print(f"> Found relevant background: {len(background_text)} characters")


        if question_type in ["why_work_here", "experience_match", "cover_letter"]:
            # Use specialized template for common questions that need specific job context
            return self._generate_specialized_response(question_type, job_data, background_text)
        else:
            # Use flexible template for ANY other question
            return self._generate_flexible_response(question, job_data, background_text)


    def _generate_specialized_response(self, question_type, job_data, personal_background):
        """Handle specialized questions using dedicated templates"""

        print(f"> Using specialized template: {question_type}")

        if question_type == "why_work_here":
            return self._generate_why_work_here(job_data, personal_background)
        elif question_type == "experience_match":
            return self._generate_experience_match(job_data, personal_background)
        elif question_type == "cover_letter":
            return self._generate_cover_letter(job_data, personal_background)


    def _generate_why_work_here(self, job_data, personal_background):
        """Generate 'Why do you want to work here?' response"""

        prompt_template = PromptTemplate(
            input_variables=["company", "job_title", "job_description", "company_culture", "personal_background"],
            template=self.prompts["why_work_here"]
        )

        chain = prompt_template | self.llm

        try:
            result = chain.invoke({
                "company": job_data.get("company", "the company"),
                "job_title": job_data.get("title", "this position"),
                "job_description": job_data.get("description", "")[:500],  # Limit length
                "company_culture": ", ".join(job_data.get("company_culture_indicators", ["Not specified"])),
                "personal_background": personal_background
            })

            return result.content

        except Exception as e:
            return f"Error generating 'why work here' response: {e}"


    def _generate_experience_match(self, job_data, personal_background):
        """Generate experience matching response"""

        prompt_template = PromptTemplate(
            input_variables=["technical_skills", "experience_level", "responsibilities", "personal_background"],
            template=self.prompts["experience_match"]
        )

        chain = prompt_template | self.llm

        try:
            result = chain.invoke({
                "technical_skills": ", ".join(job_data.get("technical_skills", ["Not specified"])),
                "experience_level": job_data.get("experience_level", "not specified"),
                "responsibilities": ", ".join(job_data.get("key_responsibilities", ["Not specified"])),
                "personal_background": personal_background
            })

            return result.content

        except Exception as e:
            return f"Error generating experience match response: {e}"


    def _generate_cover_letter(self, job_data, personal_background):
        """Generate full cover letter"""

        prompt_template = PromptTemplate(
            input_variables=["company", "job_title", "technical_skills", "job_type", "personal_background"],
            template=self.prompts["cover_letter"]
        )

        chain = prompt_template | self.llm

        try:
            result = chain.invoke({
                "company": job_data.get("company", "the company"),
                "job_title": job_data.get("title", "this position"),
                "technical_skills": ", ".join(job_data.get("technical_skills", ["Not specified"])),
                "job_type": job_data.get("job_type", "position"),
                "personal_background": personal_background
            })

            return result.content

        except Exception as e:
            return f"Error generating cover letter: {e}"

    def _generate_flexible_response(self, question, job_data, personal_background):
        """Handle ANY question using the flexible template"""

        print("Using flexible template for general question")

        prompt_template = PromptTemplate(
            input_variables=["question", "company", "job_title", "technical_skills", "job_type", "experience_level",
                             "personal_background"],
            template=self.prompts["flexible"]
        )

        chain = prompt_template | self.llm

        try:
            result = chain.invoke({
                "question": question,
                "company": job_data.get("company", "the company"),
                "job_title": job_data.get("title", "this position"),
                "technical_skills": ", ".join(job_data.get("technical_skills", ["Not specified"])),
                "job_type": job_data.get("job_type", "position"),
                "experience_level": job_data.get("experience_level", "not specified"),
                "personal_background": personal_background
            })

            return result.content

        except Exception as e:
            return f"Error generating flexible response: {e}"


    def analyze_and_respond_to_job(self, job_data, questions_list):
        """Complete workflow: analyze job and answer multiple questions"""

        print(f"Complete Job Application Response Generation")
        print(f"Company: {job_data.get('company', 'Unknown')}")
        print(f"Position: {job_data.get('title', 'Unknown')}")
        print(f"Questions to answer: {len(questions_list)}")
        print("-" * 25)

        responses = {}

        for i, question in enumerate(questions_list, 1):
            print(f"\n🔄Processing question {i}/{len(questions_list)}")

            response = self.answer_job_question(question, job_data)
            responses[question] = response

            print(f"Generated response ({len(response)} characters)")

        return responses




def test_complete_integration():
    """Test the complete integration system with enhanced presentation"""

    num_of_seperation_chars = 70
    print(header("Complete Job-RAG Integration System Test"))
    print("=" * num_of_seperation_chars)

    # Initialize system
    print("Initializing system...")
    integration = JobRAGIntegration()

    # Sample job data
    sample_job = {
        "company": "Tesla",
        "title": "Machine Learning Intern",
        "technical_skills": ["Python", "TensorFlow", "Computer Vision", "PyTorch"],
        "experience_level": "entry",
        "job_type": "internship",
        "key_responsibilities": ["Develop ML models", "Work with autonomous driving team", "Data analysis"],
        "company_culture_indicators": ["Innovation", "Sustainability", "Fast-paced", "Cutting-edge technology"],
        "description": "Join Tesla's Autopilot team to develop cutting-edge machine learning models for autonomous driving."
    }

    # Display job info
    print(f"\n{warning('Job Details:')}")
    print(f"Company: {highlight(sample_job['company'])}")
    print(f"Position: {highlight(sample_job['title'])}")
    print(f"Skills Required: {', '.join(sample_job['technical_skills'])}")

    # Test questions
    test_questions = [
        "Why do you want to work at Tesla?",
        "How does your experience relate to this machine learning role?",
        "Generate a cover letter for this position",
        "Describe a challenging project you completed",
        "What's your greatest strength?",
        "How do you handle working under pressure?",
        "Tell me about a time you failed and what you learned",
        "What programming languages are you most comfortable with?",
        "Where do you see yourself in 5 years?",
        "How do you stay updated with new technologies?"
    ]

    print(f"\n{info('Available Questions:')}")
    for i, q in enumerate(test_questions, 1):
        print(f"{dim(f'{i:2d}.')} {q}")

    print(f"\n{warning('Instructions:')}")
    print("- Press Enter to continue")
    print("- Type 'a' for batch mode")
    print(f"- Type any of {error(', '.join(EXIT_CODES))} to exit")

    # Test questions
    for i, q in enumerate(test_questions, 1):
        print(f"\n" + "=" * num_of_seperation_chars)
        print(question(f"Question {i}: {q}"))
        print("-" * num_of_seperation_chars)

        try:
            response = integration.answer_job_question(q, sample_job)
            print("-"*num_of_seperation_chars + "\n")
            print(f"{Colors.YELLOW}Response:{Colors.RESET}\n")
            print(response + "\n")

        except Exception as e:
            print(error(f"Error: {e}"))
            continue

        if i < len(test_questions):
            user_input = input(f"\n{info('Continue? (Enter/a/q): ')}").strip().lower()

            if user_input in EXIT_CODES:
                print(success("\nExiting test. Have a nice day!\n"))
                return
            elif user_input in ['a', 'all']:
                print(f"\n{warning('Batch mode: processing remaining questions...')}")
                remaining_questions = test_questions[i:]

                try:
                    batch_responses = integration.analyze_and_respond_to_job(sample_job, remaining_questions)

                    print(f"\n{success('Batch Processing Results:')}")
                    print("=" * 50)

                    for j, (quest, resp) in enumerate(batch_responses.items(), i + 1):
                        print(f"\n{question(f'Question {j}: {quest[:60]}')}")
                        print(f"{dim(f'Response length: {len(resp)} characters')}")
                        print(f"{Colors.WHITE}Response preview:{Colors.RESET} {resp[:150]}")

                        if j < len(batch_responses) + i:
                            input(f"\n{info('Press Enter to see next response...')}")

                except Exception as e:
                    print(error(f"Batch processing error: {e}"))

                break

    print(f"\n{success('Testing completed!')}")


if __name__ == "__main__":
    try:
        test_complete_integration()
    except KeyboardInterrupt:
        print(success("\nExiting test. Have a nice day!\n"))
    except Exception as e:
        print(error(f"\nUnexpected error: {e}\n"))