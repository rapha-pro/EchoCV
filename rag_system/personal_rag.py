import os
import sys
from pathlib import Path
import chromadb
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Import FileManager
sys.path.append(str(Path(__file__).parent.parent))
from utility.file_manager import FileManager

load_dotenv()


class PersonalRAG:
    def __init__(self, force_reload=False):
        """Initialize personal knowledge base with FileManager"""

        self.file_manager = FileManager()

        # Set up ChromaDB with explicit persistence
        cache_dir = self.file_manager.data_dir / "rag_knowledge_base_cache"
        self.file_manager.ensure_directory(cache_dir)

        # Set up ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(cache_dir))

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

        # Only autoload if completely empty or forced to do so
        if self.collection.count() != 0 and not force_reload:
            print(f"\nLoaded existing knowledge base: {self.collection.count()} chunks\n")
        else:
            if force_reload:
                print("Force reload requested - clearing existing data..")
                self._clear_collection()
            else:
                print("\nEmpty knowledge base detected, auto-loading documents...")

            self.load_personal_documents()

        print(f"Personal RAG system initialized. "\
              f"ChromaDB persistence directory: {cache_dir}\n")

    def _clear_collection(self):
        """Clear all data from the collection"""
        try:
            # Get all IDs and delete them
            all_data = self.collection.get()
            if all_data['ids']:
                self.collection.delete(ids=all_data['ids'])
                print("Cleared existing collection data")
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")


    def get_knowledge_stats(self):
        """Get comprehensive stats about personal knowledge base"""

        count = self.collection.count()

        if count == 0:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "sources": [],
                "doc_types": [],
                "knowledge_loaded": False
            }

        # Get sample of documents to show sources
        sample = self.collection.get(include=["metadatas"])

        sources = set()
        doc_types = set()

        for metadata in sample['metadatas']:
            sources.add(metadata.get('source', 'unknown'))
            doc_types.add(metadata.get('doc_type', 'unknown'))

        return {
            "total_documents": len(sources),
            "total_chunks": count,
            "sources": list(sources),
            "doc_types": list(doc_types),
            "knowledge_loaded": True
        }

    def _add_document_content(self, content, source_name, doc_type, description=""):
        """Add document content using FileManager"""

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

            print("Added " + "\"" + Path(source_name).name + "\"" + " to knowledge base")

        except Exception as e:
            print(f"❌ Error processing content: {e}")


    def search_documents(self, query, top_k=5):
        """Search personal knowledge base and return formatted results"""

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # Format results for easier use
            formatted_results = []

            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'source': results['metadatas'][0][i].get('source', 'Unknown'),
                        'doc_type': results['metadatas'][0][i].get('doc_type', 'general'),
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })

            return formatted_results

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def load_personal_documents(self):
        """Load all documents using FileManager"""

        print(f"Looking for documents...")

        # Use FileManager to find documents
        doc_files = self.file_manager.find_documents()

        if not doc_files:
            print("No documents found in data/personal_data/")
            print("Add your documents there:")
            print("   - resume.pdf or resume.txt")
            print("   - projects.md (portfolio descriptions)")
            print("   - personal_statement.txt")
            print("   - skills.txt")
            print("   Supported formats: .txt, .md, .pdf, .docx")
            return False

        print(f"📚 Found {len(doc_files)} documents: {doc_files}")

        # Load each document using FileManager
        for doc_file in doc_files:
            try:
                # Validate file
                valid, message = self.file_manager.validate_file_for_extraction(doc_file)

                if not valid:
                    print(f"   ⚠️ {doc_file.name}: {message}")
                    continue

                # Extract text using FileManager
                content = self.file_manager.extract_text(doc_file)

                if not content.strip():
                    print(f"   {doc_file.name}: Empty or couldn't extract text")
                    continue

                # Get document info and type using FileManager
                file_info = self.file_manager.get_file_info(doc_file)
                doc_type = file_info['document_type']
                description = f"Personal {doc_type} information"

                print(f"Loading: {doc_file.name} (type: {doc_type}, {len(content)} chars)")

                # Add to knowledge base
                self._add_document_content(content, str(doc_file), doc_type, description)

            except Exception as e:
                print(f"❌ Error loadingO {doc_file.name}: {e}")

        return True


def test_personal_rag():
    """Test PersonalRAG with FileManager"""

    print("Testing PersonalRAG with FileManager")

    rag = PersonalRAG(force_reload=True)

    # Test stats
    stats = rag.get_knowledge_stats()
    print(f"\nKnowledge Stats: {stats}")

    # Test search
    if stats['knowledge_loaded']:
        test_queries = [
            "programming languages",
            "education background",
            "project experience"
        ]

        for query in test_queries:
            print(f"\n🔍 Searching: {query}")
            results = rag.search_documents(query, top_k=3)

            for i, result in enumerate(results):
                print(f"   {i + 1}. {result['source']} (score: {result['distance']:.3f})")
                print(f"      {result['content'][:100]}...")


if __name__ == "__main__":
    test_personal_rag()