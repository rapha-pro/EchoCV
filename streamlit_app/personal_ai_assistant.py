import streamlit as st
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag_system.personal_rag import PersonalRAG
from utility.text_styles import Colors

# Configure page
st.set_page_config(
    page_title="Ask About Raphaël",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


class PersonalAIApp:
    def __init__(self):
        self.setup_rag_system()
        self.setup_session_state()

    def setup_rag_system(self):
        """Initialize the Personal RAG system"""

        if 'rag_system' not in st.session_state:
            with st.spinner("Loading knowledge about Raphaël..."):
                try:
                    st.session_state.rag_system = PersonalRAG()
                    st.session_state.rag_loaded = True
                except Exception as e:
                    st.error(f"Failed to load knowledge base: {e}")
                    st.session_state.rag_loaded = False

    def setup_session_state(self):
        """Initialize session state variables"""

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        if 'question_count' not in st.session_state:
            st.session_state.question_count = 0

    def render_header(self):
        """Render the app header"""

        st.title("🤖 Ask About Raphaël")
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("""
            **I'm an AI assistant that knows all about Raphaël's background, skills, and experience.**

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
            "Tell me about Raphaël",
            "What experience does Raphaël have?",
            "What's Raphaël's educational background?",
            "What technologies is Raphaël passionate about?",
            "What are Raphaël's strengths?",
            "What programming languages does Raphaël know?",
            "What kind of role is Raphaël looking for?"
            "Tell me about Raphaël's problem-solving approach",
        ]

        for i, question in enumerate(suggested_questions):
            if st.sidebar.button(question, key=f"suggested_{i}"):
                self.ask_question(question)
                st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Knowledge Base Stats")

        if st.session_state.rag_loaded:
            try:
                stats = st.session_state.rag_system.get_knowledge_stats()
                st.sidebar.metric("Documents Loaded", stats.get('total_documents', 0))
                st.sidebar.metric("Knowledge Chunks", stats.get('total_chunks', 0))
            except:
                st.sidebar.info("Stats unavailable")

    def ask_question(self, question):
        """Process a question through the RAG system"""

        if not st.session_state.rag_loaded:
            st.error("Knowledge base not loaded. Please refresh the page.")
            return

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now()
        })

        # Get AI response
        with st.spinner("🤔 Thinking about your question..."):
            try:
                response = st.session_state.rag_system.answer_about_me(question)

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
        question = st.chat_input("Ask me anything about Raphaël...")

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
            st.markdown("**🔗 Connect with Raphaël:**")
            st.markdown("• [LinkedIn](https://www.linkedin.com/in/raphaelonana/)")
            st.markdown("• [GitHub](https://github.com/rapha-pro)")
            st.markdown("• [Portfolio](https://nathonana.com/)")

        with col2:
            st.markdown("**💼 Interested in hiring Raphaël?**")
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
    """Main function to run the app"""

    app = PersonalAIApp()
    app.run()


if __name__ == "__main__":
    main()