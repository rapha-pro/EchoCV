import streamlit as st
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from integration.personal_chatbot import PersonalChatbot

# Configuration - Change name here
NAME = "Raphaël"

# Configure page
st.set_page_config(
    page_title=f"Ask About {NAME}",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


class PersonalAIApp:
    def __init__(self):
        self.setup_chatbot_system()
        self.setup_session_state()

    def setup_chatbot_system(self):
        """Initialize the Personal Chatbot system"""

        if 'chatbot' not in st.session_state:
            with st.spinner(f"Loading knowledge about {NAME}..."):
                try:
                    st.session_state.chatbot = PersonalChatbot()
                    st.session_state.chatbot_loaded = True
                except Exception as e:
                    st.error(f"Failed to load knowledge base: {e}")
                    st.session_state.chatbot_loaded = False

    def setup_session_state(self):
        """Initialize session state variables"""

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        if 'question_count' not in st.session_state:
            st.session_state.question_count = 0

    def render_header(self):
        """Render the app header"""

        st.title(f"🤖 Ask About {NAME}")
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"""
            **I'm an AI assistant that knows all about {NAME}'s background, skills, and experience.**

            Ask me anything about:
            • Programming skills & technologies
            • Project experience & achievements  
            • Education & certifications
            • Career goals & interests
            • Technical expertise
            """)

        with col2:
            st.metric("Questions Asked", st.session_state.question_count)

        with col3:
            if st.button("🔄 Clear Chat"):
                st.session_state.messages = []
                st.session_state.question_count = 0
                st.rerun()

    def render_suggested_questions(self):
        """Render suggested questions in sidebar"""

        st.sidebar.title("+ Suggested Questions")
        st.sidebar.markdown("Click any question to ask it:")

        suggested_questions = [
            f"Tell me about {NAME}",
            f"What experience does {NAME} have?",
            f"What's {NAME}'s educational background?",
            f"What technologies is {NAME} passionate about?",
            f"What are {NAME}'s strengths?",
            f"What programming languages does {NAME} know?",
            f"What kind of role is {NAME} looking for?",
            f"Tell me about {NAME}'s problem-solving approach",
        ]

        for i, question in enumerate(suggested_questions):
            if st.sidebar.button(question, key=f"suggested_{i}"):
                self.ask_question(question)
                st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Knowledge Base Stats")

        if st.session_state.chatbot_loaded:
            try:
                stats = st.session_state.chatbot.get_knowledge_stats()
                st.sidebar.metric("Documents Loaded", stats.get('total_documents', 0))
                st.sidebar.metric("Knowledge Chunks", stats.get('total_chunks', 0))

                # Show additional chatbot stats
                if stats.get('chatbot_status') == 'operational':
                    st.sidebar.success("Chatbot Ready")
                else:
                    st.sidebar.error("Chatbot Error")

            except Exception as e:
                st.sidebar.error(f"Stats error: {e}")

    def ask_question(self, question):
        """Process a question through the Personal Chatbot"""

        if not st.session_state.chatbot_loaded:
            st.error("Chatbot not loaded. Please refresh the page.")
            return

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now()
        })

        # Get AI response using PersonalChatbot
        with st.spinner("🤔 Thinking about your question..."):
            try:
                response = st.session_state.chatbot.answer_about_me(question)

                # Add AI response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now()
                })

                st.session_state.question_count += 1

            except Exception as e:
                st.error(f"Sorry, I encountered an error: {e}")

    def render_chat_interface(self):
        """Render the main chat interface"""

        # Chat container
        chat_container = st.container()

        with chat_container:
            # Display chat messages
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(f"**You asked:** {message['content']}")
                        st.caption(f"Asked at {message['timestamp'].strftime('%H:%M:%S')}")

                else:  # assistant
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
                        st.caption(f"Answered at {message['timestamp'].strftime('%H:%M:%S')}")

        # Question input
        st.markdown("---")
        question = st.chat_input(f"Ask me anything about {NAME}...")

        if question:
            self.ask_question(question)
            st.rerun()

    def render_knowledge_preview(self):
        """Show a preview of available knowledge"""

        with st.expander("📚 Knowledge Base Preview", expanded=False):
            st.markdown("""
            **The AI has access to information about:**

            🎓 **Education & Learning**
            - Degree and certifications
            - Courses and training

            💼 **Projects & Experience**
            - Personal projects
            - Work experience

            🎯 **Goals & Interests**
            - Career objectives
            - Technology interests
            - Learning goals

            💻 **Technical Skills**
            - Programming languages
            - Frameworks and tools
            - Development experience
            """)

    def render_footer(self):
        """Render footer information"""

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**🔗 Connect with {NAME}:**")
            st.markdown("• [LinkedIn](https://www.linkedin.com/in/raphaelonana/)")
            st.markdown("• [GitHub](https://github.com/rapha-pro)")
            st.markdown("• [Portfolio](https://nathonana.com/)")

        with col2:
            st.markdown(f"**💼 Interested in hiring {NAME}?**")
            st.markdown("Ask specific questions about his fit for your role!")

        with col3:
            st.markdown("**Powered by:**")
            st.markdown("• Personal RAG System")
            st.markdown("• ChromaDB Vector Store")
            st.markdown("• Groq LLM")

    def run(self):
        """Main app runner"""

        # Render sidebar
        self.render_suggested_questions()

        # Render main content
        self.render_header()
        self.render_knowledge_preview()
        self.render_chat_interface()
        self.render_footer()


def main():
    app = PersonalAIApp()
    app.run()


if __name__ == "__main__":
    main()