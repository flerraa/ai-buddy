import logging
import os
import shutil
from typing import List, Any
from langchain_community.vectorstores import FAISS
from ..config import settings
from .base import ServiceResponse
from .ai_cache import get_cached_embeddings  # NEW IMPORT

logger = logging.getLogger(__name__)

class VectorService:
    """FAISS Vector Service with Cached Embeddings (like prototype)"""

    def __init__(self):
        # No longer store embeddings instance - use cached version
        logger.info("VectorService initialized (embeddings cached globally)")

    def _get_embeddings(self):
        """Get cached embeddings - replaces _init_embeddings"""
        return get_cached_embeddings()

    def _get_vector_path(self, user_id: str, pdf_id: str) -> str:
        """Get vector storage path for user's PDF """
        user_vector_dir = os.path.join(settings.FAISS_PATH, user_id, "vectors")
        os.makedirs(user_vector_dir, exist_ok=True)
        vector_path = os.path.join(user_vector_dir, f"{pdf_id}_vectors")
        return vector_path

    def create_pdf_vectors(self, user_id: str, pdf_id: str, documents: List[Any]) -> ServiceResponse:
        """Create FAISS vectors """
        try:
            logger.info(f"Creating FAISS vectors for {len(documents)} documents...")
            
            if not documents:
                return ServiceResponse.error_response("No documents to process")
            
            # Use cached embeddings
            embeddings = self._get_embeddings()
            
            # Create FAISS database 
            logger.info("Creating FAISS database from documents...")
            db = FAISS.from_documents(documents, embeddings)
            
            # Get save path
            vector_path = self._get_vector_path(user_id, pdf_id)
            
            # Save to local directory 
            logger.info(f"Saving vectors to: {vector_path}")
            db.save_local(vector_path)
            
            logger.info(f"✅ FAISS vectors created and saved to: {vector_path}")
            
            return ServiceResponse.success_response(
                "Vectors created successfully",
                {
                    "vector_path": vector_path,
                    "chunk_count": len(documents)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating FAISS vectors: {str(e)}", exc_info=True)
            return ServiceResponse.error_response(f"Failed to create vectors: {str(e)}")

    def search_pdf_vectors(self, user_id: str, pdf_id: str, query: str, n_results: int = 5) -> ServiceResponse:
        """Search FAISS vectors"""
        try:
            logger.info(f"Searching FAISS vectors for query: {query[:100]}...")
            
            vector_path = self._get_vector_path(user_id, pdf_id)
            
            if not os.path.exists(vector_path):
                return ServiceResponse.error_response("Vector database not found. Please re-upload the PDF.")
            
            # Use cached embeddings
            embeddings = self._get_embeddings()
            
            # Load FAISS database
            db = FAISS.load_local(
                vector_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            # Search with similarity 
            docs = db.similarity_search(query, k=n_results)
            
            # Format results
            formatted = []
            for doc in docs:
                formatted.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 1.0
                })

            logger.info(f"Found {len(formatted)} results")
            return ServiceResponse.success_response(f"Found {len(formatted)} documents", formatted)
            
        except Exception as e:
            logger.error(f"❌ Error searching FAISS vectors: {str(e)}", exc_info=True)
            return ServiceResponse.error_response(f"Search failed: {str(e)}")

    def delete_pdf_vectors(self, user_id: str, pdf_id: str) -> ServiceResponse:
        """Delete FAISS vectors"""
        try:
            vector_path = self._get_vector_path(user_id, pdf_id)
            
            if os.path.exists(vector_path):
                shutil.rmtree(vector_path, ignore_errors=True)
                logger.info(f"🗑️ Deleted FAISS vectors: {vector_path}")
            else:
                logger.info(f"FAISS vectors not found: {vector_path}")
                
            return ServiceResponse.success_response("PDF vectors deleted successfully")
            
        except Exception as e:
            logger.error(f"❌ Error deleting FAISS vectors: {str(e)}")
            return ServiceResponse.error_response(f"Failed to delete vectors: {str(e)}")

    def get_vector_database(self, user_id: str, pdf_id: str):
        """Get FAISS database for direct use"""
        try:
            vector_path = self._get_vector_path(user_id, pdf_id)
            
            if not os.path.exists(vector_path):
                return None
            
            # Use cached embeddings
            embeddings = self._get_embeddings()
            
            db = FAISS.load_local(
                vector_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            return db
            
        except Exception as e:
            logger.error(f"Error loading FAISS database: {str(e)}")
            return None

# Export singleton instance - now with cached embeddings!
vector_service = VectorService()