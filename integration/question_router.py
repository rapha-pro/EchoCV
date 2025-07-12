import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from pathlib import Path


load_dotenv()


class QuestionRouter:
    """Lightweight router for classifying job application questions"""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.1
        )

        # Load classification prompt
        self.classification_prompt = self._load_classification_prompt()

        # Create classification chain
        self.classification_chain = self._create_classification_chain()

        print("Question Router initialized")

    def _load_classification_prompt(self):
        """Load classification prompt from file"""

        try:
            prompt_file = Path(__file__).parent.parent / "prompts" / "job_question_classification.txt"

            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()

            return template

        except Exception as e:
            print(f"❌ Error loading classification prompt: {e}")
            return self._get_fallback_prompt()


    def _get_fallback_prompt(self):
        """Fallback prompt if file loading fails"""
        return """
        Classify this job application question:

        Question: {question}

        Categories: why_work_here, experience_match, cover_letter, flexible

        {format_instructions}
        """


    def _create_classification_chain(self):
        """Create chain to classify job application questions"""

        # Define classification schema
        classification_schema = [
            ResponseSchema(
                name="question_type",
                description="Type of question: 'why_work_here', 'experience_match', 'cover_letter', or 'flexible'"
            ),
            ResponseSchema(
                name="confidence",
                description="Confidence level: 'high', 'medium', or 'low'"
            ),
            ResponseSchema(
                name="reasoning",
                description="Brief explanation for the classification"
            )
        ]

        output_parser = StructuredOutputParser.from_response_schemas(classification_schema)

        prompt_template = PromptTemplate(
            input_variables=["question"],
            template=self.classification_prompt,
            partial_variables={"format_instructions": output_parser.get_format_instructions()}
        )

        return LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            output_parser=output_parser
        )


    def classify_question(self, question):
        """Classify question using LLM chain"""

        try:
            result = self.classification_chain.invoke({"question": question})
            return result['text']
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            return self._fallback_classification(question)


    def _fallback_classification(self, question):
        """Simple keyword-based fallback if LLM classification fails"""

        question_lower = question.lower()

        if any(phrase in question_lower for phrase in ["why do you want", "why work", "why join", "why apply"]):
            return {
                "question_type": "why_work_here",
                "confidence": "medium",
                "reasoning": "Keyword-based fallback classification"
            }
        elif any(phrase in question_lower for phrase in ["experience relate", "qualification", "how does your"]):
            return {
                "question_type": "experience_match",
                "confidence": "medium",
                "reasoning": "Keyword-based fallback classification"
            }
        elif "cover letter" in question_lower:
            return {
                "question_type": "cover_letter",
                "confidence": "high",
                "reasoning": "Keyword-based fallback classification"
            }
        else:
            return {
                "question_type": "flexible",
                "confidence": "low",
                "reasoning": "Keyword-based fallback classification"
            }