"""
Personal Chatbot Integration - Now using FileManager for prompts
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from rag_system.personal_rag import PersonalRAG
from utility.file_manager import FileManager
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()


class PersonalChatbot:
    """Chatbot for answering questions about personal background"""

    def __init__(self):
        print("Initializing Personal Chatbot")

        # Initialize FileManager
        self.file_manager = FileManager()

        # Initialize Personal RAG system
        self.personal_rag = PersonalRAG()

        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.2
        )

        # Load prompt
        self.prompt_template_name = "chatbot_prompt.txt"
        self.prompt_template_subdir = "chatbot"
        self.prompt_template = self.file_manager.load_prompt(self.prompt_template_name, self.prompt_template_subdir)
        self.prompt = ChatPromptTemplate.from_template(
            template=self.prompt_template
        )

        print("Personal Chatbot ready!")


    def answer_about_me(self, question):
        """Answer questions about personal background, skills, and experience"""

        print(f"Processing question: {question}")

        try:
            # Search for relevant information using PersonalRAG
            search_results = self.personal_rag.search_documents(question, top_k=8)

            if not search_results:
                return self._get_fallback_response(question)

            # Create context from search results
            context = "\n\n".join([
                f"Source: {result.get('source', 'Unknown')}\nContent: {result['content']}"
                for result in search_results
            ])

            # Use the FileManager-loaded prompt template
            prompt = self.prompt_template.format(
                question=question,
                context=context
            )

            prompt_request = self.prompt.format_messages(
                question=question,
                context=context
            )

            response = self.llm.invoke(prompt_request)
            answer = response.content if hasattr(response, 'content') else str(response)

            print(f"Generated answer")
            return answer.strip()

        except Exception as e:
            print(f"❌ Error processing question: {e}")
            return f"I'm sorry, I encountered an error while processing your question. Please try asking something else!"


    def _get_fallback_response(self, question):
        """Provide helpful fallback when no relevant documents found"""

        question_lower = question.lower()

        if any(word in question_lower for word in ["programming", "language", "code", "technology"]):
            return "I'd be happy to tell you about my technical skills! Try asking about specific programming languages, frameworks, or technologies you're interested in."

        elif any(word in question_lower for word in ["project", "work", "experience"]):
            return "I have various projects and work experience to share! Ask me about specific types of projects, technologies I've worked with, or particular areas of experience."

        elif any(word in question_lower for word in ["education", "school", "degree"]):
            return "I can tell you about my educational background! Ask me about my degree, courses, or academic achievements."

        else:
            return "I don't have specific information about that in my knowledge base. Try asking about my technical skills, projects, work experience, or education!"


    def get_knowledge_stats(self):
        """Get statistics about the knowledge base using PersonalRAG's method"""

        try:
            # Use the existing get_knowledge_stats from PersonalRAG
            stats = self.personal_rag.get_knowledge_stats()

            # Add chatbot-specific info
            stats.update({
                "chatbot_status": "operational",
                "prompt_template_loaded": bool(self.prompt_template),
                "file_manager_ready": True
            })

            return stats

        except Exception as e:
            print(f"❌ Error getting knowledge stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "knowledge_loaded": False,
                "chatbot_status": f"error: {e}",
                "prompt_template_loaded": bool(self.prompt_template),
                "file_manager_ready": False
            }

    def reload_prompt_template(self):
        """Reload the prompt template using FileManager"""

        print("Reloading prompt template...")
        self.prompt_template = self.file_manager.load_prompt(self.prompt_template_name, self.prompt_template_subdir)
        return "Prompt template reloaded successfully!"



def test_personal_chatbot():
    """Test the personal chatbot"""

    print("Testing Personal Chatbot")

    chatbot = PersonalChatbot()

    # Test knowledge stats first
    print("\nKnowledge Base Stats:")
    stats = chatbot.get_knowledge_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 50)

    test_questions = [
        "What programming languages do you know?",
        "Tell me about your projects",
        "What's your educational background?",
        "What are your technical strengths?",
        "What kind of work are you looking for?"
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        answer = chatbot.answer_about_me(question)
        print(f"Answer: {answer}")
        print("-" * 50)


if __name__ == "__main__":
    test_personal_chatbot()