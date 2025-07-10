import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import PyPDF2
from pathlib import Path


load_dotenv()


class PersonalRAG:
    def __init__(self):
        """Initialize personal knowledge base"""

        # Set up ChromaDB with explicit persistence
        project_root = Path(__file__).parent.parent
        cache_dir = project_root / "data" / "rag_knowledge_base_cache"
        cache_dir.mkdir(exist_ok=True)

        # Set up ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(persist_dir)
        )

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="personal_knowledge",
            metadata={"description": "My personal background and experience"}
        )

        # Set up embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Set up LLM
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0.3
        )

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "]
        )

        # Only auto-load if completely empty
        if self.collection.count() == 0:
            print("\nEmpty knowledge base detected, auto-loading documents...")
            self.load_personal_documents()
        else:
            print(f"\nLoaded existing knowledge base: {self.collection.count()} chunks\n")

        print(ITALIC + BLINK + f"Personal RAG system initialized. "\
                               f"ChromaDB persistence directory: {persist_dir}\n" + RESET)


    def get_knowledge_stats(self):
        """Show stats about personal knowledge base"""

        count = self.collection.count()

        if count == 0:
            return "Knowledge base is empty"

        # Get sample of documents to show sources
        sample = self.collection.get(include=["metadatas"])

        sources = set()
        doc_types = set()

        for metadata in sample['metadatas']:
            sources.add(metadata.get('source', 'unknown'))
            doc_types.add(metadata.get('doc_type', 'unknown'))

        stats = f"""\nKnowledge Base Stats:\n+ Total chunks:{count}\n+ Sources:\n{', '.join(sources)}\n+ Document types: {', '.join(doc_types)}"""

        return stats

    def search_knowledge(self, query, n_results=5):
        """Search personal knowledge base"""

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            return results

        except Exception as e:
            print(f"❌ Search error: {e}")
            return None


    def answer_about_me(self, question):
        """Generate personalized answer using RAG"""

        print(f"🔍 Searching knowledge for: {question}")

        # Search relevant information
        search_results = self.search_knowledge(question)

        if not search_results or not search_results['documents'][0]:
            return "I don't have enough information to answer that question."

        # Combine relevant chunks
        relevant_info = "\n\n".join(search_results['documents'][0])

        # Generate response
        prompt = f"""
        Based on the following information about me, answer this question: {question}

        My background information:
        {relevant_info}

        Please provide a personalized, student-professional response that directly answers the question using specific 
        details from my background. Keep it concise but compelling. 
        DON'Ts
        - DO NOT USE ai-detectable words like: innovation, spearheaded, cutting-edge, prospect, particularly drawn... ai-words similar to these in your answer
        "- DO NOT USE EM-DASHES-NEVER
        """

        response = self.llm.invoke([HumanMessage(content=prompt)])

        return response.content


    def load_personal_documents(self):
        """Automatically load all documents from personal_data folder"""

        # Create personal_data directory if it doesn't exist
        personal_data_dir = Path(__file__).parent.parent / "data" / "personal_data"
        personal_data_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Looking for documents in: {personal_data_dir}")

        # Find all supported file types
        supported_extensions = ['*.txt', '*.md', '*.pdf', '*.docx']
        doc_files = []

        for extension in supported_extensions:
            doc_files.extend(list(personal_data_dir.rglob(extension)))

        if not doc_files:
            print("No documents found in data/personal_data/")
            print("Add your documents there:")
            print("   - resume.pdf or resume.txt")
            print("   - projects.md (portfolio descriptions)")
            print("   - personal_statement.txt")
            print("   - skills.txt")
            print("   Supported formats: .txt, .md, .pdf, .docx")

            return False

        print(f"📚 Found {len(doc_files)} documents:")

        # Load each document
        for doc_file in doc_files:
            try:
                # Extract text based on file type
                content = self._extract_text(doc_file)

                if not content.strip():
                    print(f"   ⚠️ {doc_file.name}: Empty or couldn't extract text")
                    continue

                # Infer document type from filename
                doc_type = self._infer_doc_type(doc_file.name)
                description = f"Personal {doc_type} information"

                print(f"Loading: {doc_file.name} (type: {doc_type}, {len(content)} chars)")

                # Use the extracted content instead of reading file directly
                self._add_document_content(content, str(doc_file), doc_type, description)

            except Exception as e:
                print(f"❌ Error loading {doc_file.name}: {e}")

        return True

    def _extract_text(self, file_path):
        """Extract text from different file formats"""

        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        try:
            if extension == '.pdf':
                return self._extract_pdf_text(file_path)
            elif extension == '.docx':
                return self._extract_docx_text(file_path)
            elif extension in ['.txt', '.md']:
                return self._extract_plain_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {extension}")

        except Exception as e:
            print(f"❌ Error extracting text from {file_path.name}: {e}")
            return ""


    def _extract_pdf_text(self, file_path):
        """Extract text from PDF files"""

        text = ""

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

        return text


    def _extract_docx_text(self, file_path):
        """Extract text from Word documents"""

        try:
            import docx
            doc = docx.Document(file_path)

            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

            return text

        except ImportError:
            print("❌ python-docx not installed. Install with: pipenv install python-docx")
            return ""


    def _extract_plain_text(self, file_path):
        """Extract text from plain text files"""

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


    def _add_document_content(self, content, source_name, doc_type, description=""):
        """Add document content directly (instead of reading from file)"""

        try:
            print(f"Processing content from: {Path(source_name).name}")

            # Split into chunks
            chunks = self.text_splitter.split_text(content)
            print(f"   Split into {len(chunks)} chunks")

            # Create embeddings and store
            for i, chunk in enumerate(chunks):
                chunk_id = f"{Path(source_name).stem}_chunk_{i}"

                # Generate embedding
                embedding = self.embeddings.embed_query(chunk)

                # Add to ChromaDB
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": Path(source_name).name,
                        "doc_type": doc_type,
                        "description": description,
                        "chunk_index": i
                    }]
                )

            print(f"Added {Path(source_name).name} to knowledge base")

        except Exception as e:
            print(f"❌ Error processing content: {e}")


    def _infer_doc_type(self, filename):
        """Guess document type from filename"""

        filename_lower = filename.lower()

        if any(word in filename_lower for word in ['resume', 'cv']):
            return 'resume'
        elif any(word in filename_lower for word in ['project', 'portfolio', 'work']):
            return 'projects'
        elif any(word in filename_lower for word in ['skill', 'technical', 'tech']):
            return 'skills'
        elif any(word in filename_lower for word in ['personal', 'statement', 'cover', 'letter']):
            return 'personal_statement'
        elif any(word in filename_lower for word in ['about', 'bio', 'background', 'introduction', 'intro']):
            return 'about_me'
        elif any(word in filename_lower for word in ['education', 'school', 'university']):
            return 'education'
        elif any(word in filename_lower for word in ['transcript']):
            return 'transcript'
        else:
            return 'general'



def test_rag_system(rag):
    """Comprehensive test of the Personal RAG system"""

    print(MAGENTA + "Comprehensive Test" + RESET)
    print("=" * 40)

    # Test questions
    test_questions = [
        "Tell me about yourself",
        "What programming languages do you know?",
        "What projects have you worked on?",
        "What's your educational background?",
        "Why are you interested in data science?",
        "Why do you want to work at Google?"
    ]

    print(f"\nTesting with {len(test_questions)} questions:")
    print("=" * 50)

    for i, question in enumerate(test_questions, 1):
        print(BLUE + ITALIC + f"\nQuestion {i}: {question}" + RESET)
        print("-" * 30)

        # Generate answer (search happens inside answer_about_me)
        answer = rag.answer_about_me(question)
        print(f"Answer: {answer}")

        # Option to pause or exit
        if i < len(test_questions):
            user_input = input(
                f"\nPress Enter to continue, or 's' to skip to interactive mode, or (type any of {", ".join(EXIT_CODES)} to exit) ").strip().lower()
            if user_input in EXIT_CODES:
                print(RED + "\nTest stopped.\n" + RESET)
                return
            elif user_input == 's':
                interactive_rag_test(rag)
                return

    print(GREEN + f"\nTest completed! Final stats: {rag.get_knowledge_stats()}" + RESET)


def interactive_rag_test(rag):
    """Interactive test where you can ask your own questions"""

    print(MAGENTA + "\nInteractive RAG Test - Ask Your Own Questions" + RESET)
    print("-" * 50)

    if rag is None:
        rag = PersonalRAG()
        loaded = rag.load_personal_documents()
        if not loaded:
            print("No documents loaded. Add files to data/personal_data/ first.")
            return

    print(YELLOW + f"\nAsk questions about your background (type any of {", ".join(EXIT_CODES)} to exit):" + RESET)

    while True:
        print("\nYour question: " + YELLOW)
        question = input().strip()
        print(RESET)

        if question.lower() in EXIT_CODES:
            print(GREEN + "\nGoodbye!\n" + RESET)
            break

        if not question:
            continue

        print(f"\nSearching...")
        answer = rag.answer_about_me(question)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    # ANSI escape color codes (foreground)
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Text styles
    RESET = '\033[0m'  # Reset / Normal
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    ITALIC = '\033[3m'

    EXIT_CODES= ["q", "e", "!", "exit", "quit"]


    # instantiate personal rag
    rag = PersonalRAG()

    # Show initial stats
    print(BLINK + ITALIC + f"\nInitial status\n{rag.get_knowledge_stats()}" + RESET)

    # Only load documents if knowledge base is empty (shouldn't normally have to enter this if-loop)
    # documents are loaded in __init__
    if rag.collection.count() == 0:
        print(f"\nEmpty knowledge base detected. Auto-loading documents...")
        loaded = rag.load_personal_documents()

        if not loaded:
            print("\nTo get started:")
            print("1. Create files in: data/personal_data/")
            print("2. Add documents like: about_me.txt, resume.pdf, etc.")
            print("3. Run this script again")

            print(GREEN + "Goodbye!" + RESET)
            sys.exit(0)


    print("\n" + "="*20 + "\n" + BLUE + "\nChoose test mode:" + YELLOW)
    print("1. Comprehensive test (predefined questions)")
    print("2. Interactive test (ask your own questions)" + RESET)


    choice = input(f"\nPress either {", ".join(EXIT_CODES)} to exit\n\nEnter 1 or 2: ").strip()

    if choice == "1":
        print(1)
        test_rag_system(rag)
    elif choice == "2":
        print(2)
        interactive_rag_test(rag)

    elif choice.lower() in EXIT_CODES:
        print(GREEN + "\nExiting Main. Have a nice day!\n" + RESET)
        sys.exit(0)
    else:
        print("Invalid choice, running comprehensive test...")
        test_rag_system(rag)
