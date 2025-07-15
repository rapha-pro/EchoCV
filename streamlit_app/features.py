import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import Counter
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

NAME = "Raphaël"


def render_analytics_dashboard():
    """Render analytics about questions asked"""

    if not st.session_state.messages:
        st.info("Ask some questions first to see analytics!")
        return

    # Extract user questions
    user_questions = [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user']

    col1, col2 = st.columns(2)

    with col1:
        # Question categories
        categories = categorize_questions(user_questions)

        if categories:
            fig = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Question Categories"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Question timeline
        question_times = [msg['timestamp'].hour for msg in st.session_state.messages if msg['role'] == 'user']

        if question_times:
            time_df = pd.DataFrame({'hour': question_times})
            time_counts = time_df['hour'].value_counts().sort_index()

            fig = px.bar(
                x=time_counts.index,
                y=time_counts.values,
                title="Questions by Hour",
                labels={'x': 'Hour of Day', 'y': 'Number of Questions'}
            )
            st.plotly_chart(fig, use_container_width=True)


def categorize_questions(questions):
    """Categorize questions by topic"""

    categories = {
        "Technical Skills": 0,
        "Experience": 0,
        "Education": 0,
        "Projects": 0,
        "Career Goals": 0,
        "General": 0
    }

    keywords = {
        "Technical Skills": ["programming", "language", "technology", "framework", "tool", "skill"],
        "Experience": ["experience", "worked", "job", "role", "position", "company"],
        "Education": ["education", "degree", "university", "school", "course", "certification"],
        "Projects": ["project", "built", "created", "developed", "portfolio"],
        "Career Goals": ["goal", "future", "looking", "want", "career", "next"],
    }

    for question in questions:
        question_lower = question.lower()
        categorized = False

        for category, words in keywords.items():
            if any(word in question_lower for word in words):
                categories[category] += 1
                categorized = True
                break

        if not categorized:
            categories["General"] += 1

    return categories


def render_question_suggestions():
    """Render intelligent question suggestions based on conversation"""

    st.markdown("### 🎯 Smart Suggestions")

    # Analyze what hasn't been asked yet
    asked_topics = set()

    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            content = msg['content'].lower()
            if any(word in content for word in ["programming", "language", "code"]):
                asked_topics.add("technical")
            if any(word in content for word in ["project", "built", "developed"]):
                asked_topics.add("projects")
            if any(word in content for word in ["education", "degree", "university"]):
                asked_topics.add("education")

    # Suggest unasked topics
    suggestions = {
        "technical": [
            "What's Raphaël's strongest programming language?",
            "What development tools does Raphaël prefer?"
        ],
        "projects": [
            "What's Raphaël's most impressive project?",
            "Tell me about Raphaël's latest project",
            "What challenges has Raphaël overcome in his projects?"
        ],
        "education": [
            "What did Raphaël study in university?",
            "Does Raphaël have any certifications?",
            "What courses has Raphaël completed recently?"
        ]
    }

    unasked_topics = set(suggestions.keys()) - asked_topics

    if unasked_topics:
        st.info(f"You might want to ask about: {', '.join(unasked_topics)}")

        for topic in unasked_topics:
            with st.expander(f"Questions about {topic}"):
                for suggestion in suggestions[topic]:
                    if st.button(suggestion, key=f"smart_suggest_{suggestion}"):
                        return suggestion

    return None


def export_conversation():
    """Allow users to export the conversation"""

    if not st.session_state.messages:
        st.info("No conversation to export yet!")
        return

    # Create conversation export
    export_text = "# Conversation with Raphaël's AI Assistant\n\n"
    export_text += f"**Date:** {st.session_state.messages[0]['timestamp'].strftime('%Y-%m-%d')}\n"
    export_text += f"**Total Questions:** {st.session_state.question_count}\n\n"

    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            export_text += f"**Q:** {msg['content']}\n\n"
        else:
            export_text += f"**A:** {msg['content']}\n\n---\n\n"

    st.download_button(
        label="📄 Download Conversation",
        data=export_text,
        file_name=f"Raphaël_ai_conversation_{st.session_state.messages[0]['timestamp'].strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )