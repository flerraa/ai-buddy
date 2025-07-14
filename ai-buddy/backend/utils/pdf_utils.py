import os
import shutil
from typing import Tuple
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Improved PDF processor using the working example pattern"""

    def __init__(self):
        # Use the same pattern as working example
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n", " ", ""]  # Same as working example
        )
        logger.info(f"PDFProcessor initialized with chunk_size={settings.CHUNK_SIZE}")

    def save_uploaded_file(self, uploaded_file, user_id: str, folder_id: str) -> Tuple[bool, str, str]:
        """Save uploaded file - same as your existing implementation"""
        try:
            user_dir = os.path.join(settings.USER_DATA_PATH, user_id, "pdfs")
            os.makedirs(user_dir, exist_ok=True)

            base_name = uploaded_file.name
            file_path = os.path.join(user_dir, base_name)
            counter = 1

            while os.path.exists(file_path):
                name, ext = os.path.splitext(base_name)
                file_path = os.path.join(user_dir, f"{name}_{counter}{ext}")
                counter += 1

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            filename = os.path.basename(file_path)
            logger.info(f"PDF saved: {filename} for user {user_id}")
            return True, "PDF saved successfully", file_path

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            return False, f"Error saving PDF: {str(e)}", ""

    def extract_text_from_pdf(self, file_path: str) -> Tuple[bool, str, list]:
        """Extract text using the exact same pattern as working example"""
        try:
            logger.info(f"Starting text extraction from: {file_path}")
            
            if not file_path.lower().endswith('.pdf'):
                return False, "File is not a PDF", []
                
            if not os.path.exists(file_path):
                return False, "PDF file not found", []

            # Check file size (prevent huge files from hanging)
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB limit
            if file_size > max_size:
                return False, f"PDF too large ({file_size/1024/1024:.1f}MB > 100MB)", []

            logger.info(f"Loading PDF with PyPDFLoader: {file_path}")
            
            # Use exact same pattern as working example
            loader = PyPDFLoader(file_path)
            loaded_documents = loader.load()
            
            if not loaded_documents:
                return False, "No content found in PDF", []

            logger.info(f"Loaded {len(loaded_documents)} pages, splitting text...")
            
            # Split documents using same pattern
            documents = self.text_splitter.split_documents(loaded_documents)
            
            if not documents:
                return False, "No text could be extracted from PDF", []

            logger.info(f"✅ Extracted {len(documents)} text chunks from PDF")
            return True, f"Extracted {len(documents)} text chunks", documents

        except Exception as e:
            logger.error(f"❌ Error extracting text from PDF: {e}", exc_info=True)
            return False, f"Error extracting text: {str(e)}", []

    def delete_pdf_file(self, file_path: str) -> Tuple[bool, str]:
        """Delete PDF file - same as existing"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"PDF file deleted: {file_path}")
                return True, "PDF file deleted successfully"
            else:
                return True, "PDF file not found (already deleted)"
        except Exception as e:
            logger.error(f"Error deleting PDF file: {e}")
            return False, f"Error deleting PDF file: {str(e)}"

    def get_file_size(self, file_path: str) -> int:
        """Get file size - same as existing"""
        try:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except:
            return 0

    def cleanup_user_files(self, user_id: str) -> Tuple[bool, str]:
        """Clean up user files - same as existing"""
        try:
            user_dir = os.path.join(settings.USER_DATA_PATH, user_id)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
                logger.info(f"Cleaned up files for user: {user_id}")
                return True, "User files cleaned up successfully"
            else:
                return True, "No user files found"
        except Exception as e:
            logger.error(f"Error cleaning up user files: {e}")
            return False, f"Error cleaning up files: {str(e)}"