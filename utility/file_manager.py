"""
File Manager - Centralized file operations for the entire project
Handles text extraction, prompt loading, and file utilities
"""

import os
from pathlib import Path
import PyPDF2
from typing import Optional, Dict, List, Union


class FileManager:
    """Centralized file management for all project file operations"""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize FileManager with project root"""

        if project_root is None:
            # Auto-detect project root (go up until we find a known project file)
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                if (current_path / ".env").exists() or (current_path / "data").exists():
                    project_root = current_path
                    break
                current_path = current_path.parent
            else:
                project_root = Path(__file__).parent.parent

        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.prompts_dir = self.project_root / "prompts"

        print(f"FileManager initialized - Project root: {self.project_root}")


    def load_prompt(self, prompt_name: str, prompts_subdir: str = "") -> str:
        """
        Load prompt template from file

        Args:
            prompt_name: Name of prompt file (with or without .txt extension)
            prompts_subdir: Optional subdirectory within prompts/

        Returns:
            Prompt text content
        """

        # Ensure .txt extension
        if not prompt_name.endswith('.txt'):
            prompt_name += '.txt'

        # Build full path
        if prompts_subdir:
            prompt_path = self.prompts_dir / prompts_subdir / prompt_name
        else:
            prompt_path = self.prompts_dir / prompt_name

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            print(f"Loaded prompt: {prompt_path}")
            return content

        except FileNotFoundError:
            print(f"⚠️  Prompt file not found: {prompt_path}")
            return self._get_fallback_prompt(prompt_name)

        except Exception as e:
            print(f"❌ Error loading prompt {prompt_name}: {e}")
            return f"Error loading prompt: {prompt_name}"


    def _get_fallback_prompt(self, prompt_name: str) -> str:
        """Provide fallback prompts for common cases"""

        fallbacks = {
        "personal_chatbot_prompt.txt": """
            You are an AI assistant representing a person's professional background.
            Answer questions about their experience, skills, education, and projects.
            
            Question: {question}
            Context: {context}
            
            Answer as this person in first person:
                        """.strip(),

                        "job_application_prompt.txt": """
            You are helping someone apply for a job. Generate a professional response.
            
            Question: {question}
            Job Context: {job_data}
            Personal Context: {personal_context}
            
            Response:
        """.strip(),

        "cover_letter_prompt.txt": """
            Write a professional cover letter for this job application.
            
            Job Details: {job_data}
            Personal Background: {personal_context}
            
            Cover Letter:
        """.strip()
                }

        return fallbacks.get(prompt_name, "Please provide an appropriate response based on the context.")


    def save_prompt(self, prompt_name: str, content: str, prompts_subdir: str = "") -> bool:
        """Save prompt template to file"""

        # Ensure .txt extension
        if not prompt_name.endswith('.txt'):
            prompt_name += '.txt'

        # Build full path and create directories
        if prompts_subdir:
            prompt_dir = self.prompts_dir / prompts_subdir
        else:
            prompt_dir = self.prompts_dir

        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = prompt_dir / prompt_name

        try:
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Saved prompt: {prompt_path}")
            return True

        except Exception as e:
            print(f"❌ Error saving prompt {prompt_name}: {e}")
            return False


    def extract_text(self, file_path: Union[str, Path]) -> str:
        """Extract text from various file formats"""

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        extractors = {
            '.pdf': self._extract_pdf_text,
            '.docx': self._extract_docx_text,
            '.txt': self._extract_plain_text,
            '.md': self._extract_plain_text,
            '.py': self._extract_plain_text,
            '.json': self._extract_plain_text,
            '.csv': self._extract_plain_text,
        }

        if extension not in extractors:
            raise ValueError(f"Unsupported file type: {extension}")

        try:
            text = extractors[extension](file_path)
            print(f"Extracted text from {file_path.name} ({len(text)} characters)")
            return text

        except Exception as e:
            print(f"❌ Error extracting text from {file_path.name}: {e}")
            raise

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF files"""

        text = ""

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

        return text.strip()

    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from Word documents"""

        try:
            import docx
            doc = docx.Document(file_path)

            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

            return text.strip()

        except ImportError:
            raise ImportError("python-docx not installed. Install with: pipenv install python-docx")


    def _extract_plain_text(self, file_path: Path) -> str:
        """Extract text from plain text files"""

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()


    def find_documents(self,
                       directory: Union[str, Path] = None,
                       extensions: List[str] = None,
                       recursive: bool = True) -> List[Path]:
        """Find documents in directory"""

        if directory is None:
            directory = self.data_dir / "personal_data"
        else:
            directory = Path(directory)

        if extensions is None:
            extensions = ['.txt', '.md', '.pdf', '.docx', '.py', '.json']

        documents = []

        if not directory.exists():
            print(f"⚠️  Directory not found: {directory}")
            return documents

        search_pattern = "**/*" if recursive else "*"

        for extension in extensions:
            pattern = f"{search_pattern}{extension}"
            found_files = list(directory.glob(pattern))
            documents.extend(found_files)

        print(f"Found {len(documents)} documents in {directory}")
        return sorted(documents)


    def infer_document_type(self, filename: str) -> str:
        """Infer document type from filename"""

        filename_lower = filename.lower()

        type_keywords = {
            'resume': ['resume', 'cv'],
            'projects': ['project', 'portfolio', 'work'],
            'skills': ['skill', 'technical', 'tech'],
            'personal_statement': ['personal', 'statement', 'cover', 'letter'],
            'about_me': ['about', 'bio', 'background', 'introduction', 'intro'],
            'education': ['education', 'school', 'university'],
            'transcript': ['transcript'],
            'code': ['.py', '.js', '.java', '.cpp'],
            'config': ['config', 'settings', '.env', '.json'],
        }

        for doc_type, keywords in type_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return doc_type

        return 'general'


    def ensure_directory(self, directory: Union[str, Path]) -> Path:
        """Ensure directory exists, create if needed"""

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory


    def get_file_info(self, file_path: Union[str, Path]) -> Dict:
        """Get comprehensive file information"""

        file_path = Path(file_path)

        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()

        return {
            "exists": True,
            "name": file_path.name,
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "extension": file_path.suffix.lower(),
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "absolute_path": str(file_path.absolute()),
            "document_type": self.infer_document_type(file_path.name)
        }


    def validate_file_for_extraction(self, file_path: Union[str, Path]) -> tuple[bool, str]:
        """Validate if file can be processed for text extraction"""

        file_path = Path(file_path)

        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if not file_path.is_file():
            return False, f"Not a file: {file_path}"

        extension = file_path.suffix.lower()
        supported_extensions = ['.txt', '.md', '.pdf', '.docx', '.py', '.json', '.csv']

        if extension not in supported_extensions:
            return False, f"Unsupported file type: {extension}"

        # Check file size (warn if very large)
        # size_mb = file_path.stat().st_size / (1024 * 1024)
        # if size_mb > 50:
        #     return False, f"File too large: {size_mb:.1f}MB (max 50MB)"
        #
        return True, "File is valid for text extraction"



def test_file_manager():
    """Test FileManager functionality"""

    print("Testing FileManager")
    print("=" * 50)

    fm = FileManager()

    # Test prompt loading
    print("\nTesting Prompt Loading:")

    # Test with existing prompt
    prompt = fm.load_prompt("personal_chatbot_prompt")
    print(f"Loaded prompt length: {len(prompt)} characters")

    # Test with non-existing prompt (should use fallback)
    fallback = fm.load_prompt("non_existing_prompt")
    print(f"Fallback prompt: {fallback[:50]}...")

    # Test document discovery
    print("\nTesting Document Discovery:")
    docs = fm.find_documents()
    for doc in docs[:5]:  # Show first 5
        info = fm.get_file_info(doc)
        print(f"   {info['name']} ({info['size_kb']}KB, type: {info['document_type']})")

    # Test text extraction
    print("\nTesting Text Extraction:")
    if docs:
        for doc in docs[:2]:  # Test first 2 documents
            valid, message = fm.validate_file_for_extraction(doc)
            if valid:
                try:
                    text = fm.extract_text(doc)
                    print(f"   {doc.name}: {len(text)} characters extracted")
                except Exception as e:
                    print(f"   {doc.name}: Error - {e}")
            else:
                print(f"   {doc.name}: {message}")


if __name__ == "__main__":
    test_file_manager()