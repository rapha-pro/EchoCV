import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Import modules
from personal_ai_assistant import PersonalAIApp
from features import render_analytics_dashboard, render_question_suggestions, export_conversation


def main():
    """Enhanced main function with multiple pages"""

    st.sidebar.title("Personal AI Assistant")

    # Page selection
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["💬 Chat with AI", "📊 Analytics", "⚙️ Advanced Features"]
    )

    if page == "💬 Chat with AI":
        # Main chat interface
        app = PersonalAIApp()
        app.run()

    elif page == "📊 Analytics":
        st.title("📊 Question Analytics")
        render_analytics_dashboard()

        st.markdown("---")
        export_conversation()

    elif page == "⚙️ Advanced Features":
        st.title("⚙️ Advanced Features")

        # Smart suggestions
        suggestion = render_question_suggestions()
        if suggestion:
            st.success(f"Try asking: {suggestion}")

        st.markdown("---")

        # Additional features
        st.markdown("### Additional Tools")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Reset Knowledge Base"):
                if 'rag_system' in st.session_state:
                    del st.session_state.rag_system
                st.success("Knowledge base will reload on next question")

        with col2:
            if st.button("📈 View Detailed Stats"):
                if 'rag_system' in st.session_state:
                    try:
                        stats = st.session_state.rag_system.get_knowledge_stats()
                        st.json(stats)
                    except:
                        st.error("Could not load detailed stats")


if __name__ == "__main__":
    main()