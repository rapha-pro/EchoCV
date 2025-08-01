FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY Pipfile Pipfile.lock ./

# sytem:installs locked dependencies globally no virtualenv; deploy: fails if Pipfile.lock mismatches with Pipfile
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy the entire application
COPY . .


# Create necessary directories
RUN mkdir -p data/personal_data/rag_knowledge_base_cache &&  \
    mkdir -p prompts/integration && \
    mkdir -p prompts/chatbot

# Expose port that Streamlit runs on
EXPOSE 8501

# Command to run when container starts
# server.port=8501 is the default port for Streamlit
# server.address=0.0.0 allows access from outside the container
CMD ["streamlit", "run", "streamlit_app/personal_ai_assistant.py", "--server.port=8501", "--server.address=0.0.0.0"]

