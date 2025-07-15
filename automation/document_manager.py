import json
import logging
from datetime import datetime
from pathlib import Path

class DocumentManager:
    """Manages document storage with correct project root paths"""

    def __init__(self):
        # Get the project root (JobFlow directory)
        self.project_root = self._find_project_root()
        print(f"Project root: {self.project_root}")

        self.setup_directories()
        self.setup_logging()

        print("✅ Document Manager initialized")

    def _find_project_root(self):
        """Find the JobFlow project root directory"""

        # Start from current file location
        current_path = Path(__file__).resolve()

        # Look for the JobFlow root by finding specific markers
        for parent in current_path.parents:
            # Check if this looks like the JobFlow root
            if (parent / "data").exists() or parent.name == "JobFlow" or (parent / "integration").exists():
                return parent

        # Fallback: assume we're in a subdirectory of JobFlow
        # Go up until we find the right structure
        search_path = current_path.parent
        while search_path.parent != search_path:  # Not at filesystem root
            if (search_path / "data" / "personal_data").exists():
                return search_path
            search_path = search_path.parent

        # Last fallback: use current working directory
        return Path.cwd()

    def setup_directories(self):
        """Create organized directory structure in correct locations"""

        # NEVER create or modify data/personal_data - it should already exist
        personal_data_path = self.project_root / "data" / "personal_data"

        if not personal_data_path.exists():
            print(f"⚠️ Warning: Personal data directory not found at {personal_data_path}")
            print("Please ensure your Tech_resume.pdf is in JobFlow/data/personal_data/")
        else:
            print(f"✅ Found personal data directory: {personal_data_path}")

        # Create ONLY the logs directories (never touch data/)
        logs_directories = [
            "logs/screenshots",
            "logs/documents/cover_letters",
            "logs/documents/applications",
            "logs/responses_generated",
            "logs/application_attempts",
            "logs/error_logs"
        ]

        for directory in logs_directories:
            full_path = self.project_root / directory
            full_path.mkdir(parents=True, exist_ok=True)

        print("✅ Logs directory structure created")
        self._create_gitignore()

    def _create_gitignore(self):
        """Create .gitignore in project root to exclude logs/"""

        gitignore_content = """
        # Logs and generated content
        logs/
        *.log
        
        # personal data
        data/
        
        # Browser automation
        screenshots/
        *.png
        *.jpg
        """

        gitignore_path = self.project_root / ".gitignore"

        # Read existing .gitignore if it exists
        existing_content = ""
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()

        # Add our content if not already present
        if "logs/" not in existing_content:
            with open(gitignore_path, 'a') as f:
                f.write(gitignore_content)
            print("✅ Updated .gitignore to exclude logs/")

    def setup_logging(self):
        """Setup logging in the logs directory"""

        # Create logger
        self.logger = logging.getLogger('JobApplicationAgent')
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # File handler for application logs (in project root logs/)
            log_file = self.project_root / "logs" / "application_attempts" / "job_applications.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers to logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

        print("✅ Logging system configured")

    # ===== PERSONAL DATA ACCESS (READ-ONLY) =====

    def get_personal_document_path(self, doc_type):
        """Get path to personal documents in JobFlow/data/personal_data/"""

        personal_data_dir = self.project_root / "data" / "personal_data"

        # Map document types to actual filenames
        personal_docs = {
            "resume": "Tech_resume.pdf",
            "portfolio": "portfolio.pdf",
            "references": "references.txt",
            "transcript": "transcript.pdf"
        }

        filename = personal_docs.get(doc_type.lower())
        if not filename:
            self.logger.warning(f"Unknown document type: {doc_type}")
            return None

        doc_path = personal_data_dir / filename

        if doc_path.exists():
            self.logger.info(f"Found personal document: {doc_path}")
            return str(doc_path)
        else:
            self.logger.warning(f"Personal document not found: {doc_path}")
            return None

    def list_personal_documents(self):
        """List all available personal documents"""

        personal_data_dir = self.project_root / "data" / "personal_data"
        documents = []

        if personal_data_dir.exists():
            for file_path in personal_data_dir.glob("*"):
                if file_path.is_file():
                    documents.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })

        return documents

    # ===== GENERATED CONTENT STORAGE =====

    def save_cover_letter(self, company, position, content):
        """Save AI-generated cover letter to logs/documents/cover_letters/"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = self._safe_filename(company)
        safe_position = self._safe_filename(position)

        filename = f"{safe_company}_{safe_position}_{timestamp}.txt"
        filepath = self.project_root / "logs" / "documents" / "cover_letters" / filename

        # Save content with metadata
        full_content = f"""Generated Cover Letter
======================
Company: {company}
Position: {position}
Generated: {datetime.now().isoformat()}

{content}
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        self.logger.info(f"Cover letter saved: {filepath}")
        return str(filepath)

    def save_application_response(self, company, position, question, response):
        """Save individual AI response to logs/responses_generated/"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = self._safe_filename(company)

        # Create company-specific directory
        company_dir = self.project_root / "logs" / "responses_generated" / safe_company
        company_dir.mkdir(exist_ok=True)

        # Response data
        response_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "company": company,
                "position": position,
                "question_type": self._classify_question_type(question)
            },
            "question": question,
            "response": response,
            "character_count": len(response),
            "word_count": len(response.split())
        }

        filename = f"response_{timestamp}.json"
        filepath = company_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Response saved: {filepath}")
        return str(filepath)

    def save_complete_application(self, company, position, application_data):
        """Save complete application to logs/documents/applications/"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = self._safe_filename(company)
        safe_position = self._safe_filename(position)

        filename = f"{safe_company}_{safe_position}_complete_{timestamp}.json"
        filepath = self.project_root / "logs" / "documents" / "applications" / filename

        # Enhanced application data
        complete_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "company": company,
                "position": position,
                "application_url": application_data.get("url", ""),
                "status": "submitted" if application_data.get("submitted") else "draft",
                "total_responses": len(application_data.get("responses", [])),
                "documents_generated": len(application_data.get("documents_generated", []))
            },
            "application_data": application_data,
            "summary": {
                "questions_answered": [r.get("question", "")[:50] + "..." for r in application_data.get("responses", [])],
                "files_uploaded": application_data.get("documents_generated", []),
                "completion_time": application_data.get("completion_time", "unknown")
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Complete application saved: {filepath}")
        return str(filepath)

    def save_screenshot(self, company, position, screenshot_type="general"):
        """Generate screenshot path for browser automation"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = self._safe_filename(company)
        safe_position = self._safe_filename(position)

        # Create company directory in logs/screenshots/
        company_dir = self.project_root / "logs" / "screenshots" / safe_company
        company_dir.mkdir(exist_ok=True)

        filename = f"{safe_position}_{screenshot_type}_{timestamp}.png"
        filepath = company_dir / filename

        self.logger.info(f"Screenshot path prepared: {filepath}")
        return str(filepath)

    # ===== APPLICATION TRACKING =====

    def log_application_attempt(self, company, position, url, success, error_msg=None, duration=None):
        """Log application attempt with comprehensive tracking"""

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "company": company,
            "position": position,
            "url": url,
            "success": success,
            "error": error_msg,
            "duration_seconds": duration,
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        # Monthly log file in logs/application_attempts/
        log_file = self.project_root / "logs" / "application_attempts" / f"attempts_{datetime.now().strftime('%Y%m')}.json"

        # Load existing logs
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(log_data)

        # Save updated logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

        # Log to main logger
        if success:
            self.logger.info(f"Application successful: {company} - {position}")
        else:
            self.logger.error(f"Application failed: {company} - {position} - {error_msg}")

    def get_application_stats(self):
        """Get statistics on application attempts"""

        stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "companies_applied": set(),
            "most_recent_attempt": None,
            "success_rate": 0.0
        }

        attempts_dir = self.project_root / "logs" / "application_attempts"

        for log_file in attempts_dir.glob("attempts_*.json"):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)

                for log_entry in logs:
                    stats["total_attempts"] += 1
                    stats["companies_applied"].add(log_entry.get("company", "Unknown"))

                    if log_entry.get("success", False):
                        stats["successful_attempts"] += 1
                    else:
                        stats["failed_attempts"] += 1

                    # Track most recent
                    if not stats["most_recent_attempt"] or log_entry["timestamp"] > stats["most_recent_attempt"]:
                        stats["most_recent_attempt"] = log_entry["timestamp"]

            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Calculate success rate
        if stats["total_attempts"] > 0:
            stats["success_rate"] = (stats["successful_attempts"] / stats["total_attempts"]) * 100

        stats["companies_applied"] = list(stats["companies_applied"])

        return stats

    # ===== UTILITY METHODS =====

    def _safe_filename(self, text):
        """Create safe filename from text"""

        if not text:
            return "unknown"

        # Remove/replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_text = "".join(c if c in safe_chars else "_" for c in text)

        # Limit length and remove extra underscores
        safe_text = safe_text[:50].strip("_")

        return safe_text if safe_text else "unknown"

    def _classify_question_type(self, question):
        """Classify question type for better organization"""

        question_lower = question.lower()

        if any(word in question_lower for word in ["why", "motivation", "interest"]):
            return "motivation"
        elif any(word in question_lower for word in ["experience", "background", "skill"]):
            return "experience"
        elif any(word in question_lower for word in ["strength", "weakness", "challenge"]):
            return "personal_assessment"
        elif any(word in question_lower for word in ["goal", "future", "career"]):
            return "career_goals"
        elif any(word in question_lower for word in ["cover", "letter"]):
            return "cover_letter"
        else:
            return "general"

def test_document_manager():
    """Test the document management system with correct paths"""

    print("Testing Document Manager with Correct Paths")
    print("=" * 50)

    # Initialize manager
    doc_manager = DocumentManager()

    # Test personal document access
    print("\nTesting personal document access:")
    resume_path = doc_manager.get_personal_document_path("resume")
    print(f"Resume path: {resume_path}")

    personal_docs = doc_manager.list_personal_documents()
    print(f"Found {len(personal_docs)} personal documents:")
    for doc in personal_docs:
        print(f"  - {doc['name']} ({doc['size']} bytes)")

    # Test that we're using the correct project structure
    print(f"\nProject root: {doc_manager.project_root}")
    print(f"Personal data directory: {doc_manager.project_root / 'data' / 'personal_data'}")
    print(f"Logs directory: {doc_manager.project_root / 'logs'}")

    # Test generated content storage
    print("\nTesting generated content storage:")

    cover_letter_path = doc_manager.save_cover_letter(
        "Test Company",
        "Test Position",
        "This is a test cover letter"
    )
    print(f"Cover letter saved: {cover_letter_path}")

    print("\nDocument Manager test completed!")

if __name__ == "__main__":
    test_document_manager()