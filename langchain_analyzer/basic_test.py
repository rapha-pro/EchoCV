import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()


def test_groq_connection():
    """Test if our Groq API key works"""

    # Create LLM instance with Groq
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.1-8b-instant",
        temperature=0.1
    )

    response = llm.invoke("Say hello and tell me what model you are!")

    print("🤖 AI Response:")
    print(response.content)
    print("\n✅ Groq connection successful!")


if __name__ == "__main__":
    test_groq_connection()