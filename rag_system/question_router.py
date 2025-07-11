import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.schema import HumanMessage
from pathlib import Path

load_dotenv()

class SmartQuestionRouter:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.1  # Low temperature for consistent classification
        )

        # Load prompt template from file
        self.classification_prompt_template = self._load_prompt_template("classification_prompt.txt")

        # Set up classification chain
        self.classification_chain = self._create_classification_chain()

        print("Smart Question Router initialized")


    def _load_prompt_template(self, filename):
        """Load the classification prompt template from file"""

        try:
            prompt_file = Path(__file__).parent / "prompts" / filename

            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()

            print(f"Loaded classification prompt: {prompt_file.name}")
            return template

        except Exception as e:
            print(f"❌ Error loading classification prompt: {e}")
            return self._get_fallback_prompt()


    def _get_fallback_prompt(self):
        """Fallback prompt if file loading fails"""
        return """
        Classify this question as either asking about a person's background/experience (personal) or asking for general knowledge (general).

        Question: {question}

        {format_instructions}
        """

    def _create_classification_chain(self):
        """Create chain to classify questions"""

        # Define classification schema
        classification_schema = [
            ResponseSchema(
                name="question_type",
                description="Type of question: 'personal' or 'general'"
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
            template=self.classification_prompt_template,
            partial_variables={"format_instructions": output_parser.get_format_instructions()}
        )

        return LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            output_parser=output_parser
        )


    def classify_question(self, question):
        """Classify the question type"""

        try:
            result = self.classification_chain.invoke({"question": question})
            return result['text']
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            return self._fallback_classification(question)


    def _fallback_classification(self, question):
        """Simple keyword-based fallback classification"""

        personal_keywords = ["you", "your", "my", "i", "me", "tell me about yourself"]
        question_lower = question.lower()

        is_personal = any(keyword in question_lower for keyword in personal_keywords)

        return {
            "question_type": "personal" if is_personal else "general",
            "confidence": "low",
            "reasoning": "Fallback classification using keywords"
        }