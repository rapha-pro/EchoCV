import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from rag_system.personal_rag import PersonalRAG
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()


class PersonalChatbot:
    """Chatbot for answering questions about personal background"""

    def __init__(self):
        print("Initializing Personal Chatbot")

        # Initialize Personal RAG system
        self.personal_rag = PersonalRAG()
        print("Personal RAG system loaded")

        # Initialize LLM
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("LLM initialized")

        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        print("Prompt template loaded")

        print("Personal Chatbot ready!")

    def _load_prompt_template(self):
        """Load the prompt template from file"""

        prompt_file = Path(__file__).parent / "prompts" / "personal_chatbot_prompt.txt"

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read().strip()

            print(f"✅ Loaded prompt template from: {prompt_file}")
            return template

        except FileNotFoundError:
            print(f"⚠️  Prompt file not found: {prompt_file}")
            print("Using fallback prompt template")

            # Fallback prompt if file doesn't exist
            return """
            You are an AI assistant representing a person's professional background.
            Answer questions about their experience, skills, education, and projects.

            Speak in first person and be conversational.

            Question: {question}
            Context: {context}

            Answer:
            """

        except Exception as e:
            print(f"❌ Error loading prompt template: {e}")
            return "Answer this question based on the context: {question}\n\nContext: {context}"

    def answer_about_me(self, question):
        """Answer questions about personal background, skills, and experience"""

        print(f"🤔 Processing question: {question}")

        try:
            # Search for relevant information using PersonalRAG
            search_results = self.personal_rag.search_documents(question, top_k=5)

            if not search_results:
                return self._get_fallback_response(question)

            # Create context from search results
            context = "\n\n".join([
                f"Source: {result.get('source', 'Unknown')}\nContent: {result['content']}"
                for result in search_results
            ])

            # Use the loaded prompt template
            prompt = self.prompt_template.format(
                question=question,
                context=context
            )

            # Get response from LLM
            response = self.llm.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            answer = response.choices[0].message.content

            print(f"✅ Generated answer")
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
                "prompt_template_loaded": bool(self.prompt_template)
            })

            return stats

        except Exception as e:
            print(f"❌ Error getting knowledge stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "knowledge_loaded": False,
                "chatbot_status": f"error: {e}",
                "prompt_template_loaded": bool(self.prompt_template)
            }

    def reload_prompt_template(self):
        """Reload the prompt template (useful for development)"""

        print("🔄 Reloading prompt template...")
        self.prompt_template = self._load_prompt_template()
        return "Prompt template reloaded successfully!"


def test_personal_chatbot():
    """Test the personal chatbot"""

    print("🧪 Testing Personal Chatbot")

    chatbot = PersonalChatbot()

    # Test knowledge stats first
    print("\n📊 Knowledge Base Stats:")
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
        print(f"\n❓ Question: {question}")
        answer = chatbot.answer_about_me(question)
        print(f"🤖 Answer: {answer}")
        print("-" * 50)


if __name__ == "__main__":
    test_personal_chatbot()