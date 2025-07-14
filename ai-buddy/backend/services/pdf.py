import os
from typing import Optional
from bson import ObjectId
from .base import BaseService, ServiceResponse
from .vector import vector_service
from ..models import PDF
from ..utils import PDFProcessor
import logging

logger = logging.getLogger(__name__)

class PDFService(BaseService):
    """PDF Service with FAISS integration - matches your working prototype"""

    def __init__(self):
        super().__init__("pdfs")
        self.pdf_processor = PDFProcessor()

    def upload_pdf(self, user_id: str, folder_id: str, uploaded_file, original_name: str) -> ServiceResponse:
        try:
            logger.info(f"Starting PDF upload for user {user_id}, file: {original_name}")
            
            # Step 1: Save file
            logger.info("Step 1: Saving uploaded file...")
            success, message, file_path = self.pdf_processor.save_uploaded_file(uploaded_file, user_id, folder_id)
            if not success:
                logger.error(f"File save failed: {message}")
                return ServiceResponse.error_response(message)
            logger.info(f"File saved successfully: {file_path}")

            # Step 2: Get file info
            file_size = self.pdf_processor.get_file_size(file_path)
            filename = os.path.basename(file_path)

            # Step 3: Create PDF record
            logger.info("Step 3: Creating PDF database record...")
            pdf = PDF()
            pdf.user_id = ObjectId(user_id)
            pdf.folder_id = ObjectId(folder_id)
            pdf.filename = filename
            pdf.original_name = original_name
            pdf.file_path = file_path
            pdf.file_size = file_size
            pdf.processed = False  # Will be set to True after processing

            result = self.collection.insert_one(pdf.to_dict())
            pdf._id = result.inserted_id
            pdf_id = str(pdf._id)
            logger.info(f"PDF record created with ID: {pdf_id}")

            # Step 4: Process PDF content with FAISS
            logger.info("Step 4: Processing PDF content with FAISS...")
            processing_result = self._process_pdf_content(pdf_id, user_id, file_path)
            
            if not processing_result.success:
                logger.error(f"PDF processing failed: {processing_result.message}")
                # Clean up on failure
                self.delete_pdf(pdf_id, user_id)
                return processing_result

            # Step 5: Mark as processed and update vector path
            logger.info("Step 5: Marking PDF as processed...")
            vector_path = vector_service._get_vector_path(user_id, pdf_id)
            
            self.collection.update_one(
                {"_id": pdf._id},
                {"$set": {
                    "processed": True,
                    "vector_collection_name": vector_path  # Store FAISS path
                }}
            )
            
            pdf.processed = True
            pdf.vector_collection_name = vector_path

            logger.info(f"PDF upload completed successfully: {original_name}")
            return ServiceResponse.success_response("PDF uploaded and processed successfully", pdf.to_display_dict())

        except Exception as e:
            logger.error(f"Critical error in PDF upload: {str(e)}", exc_info=True)
            return ServiceResponse.error_response(f"Upload failed: {str(e)}")

    def _process_pdf_content(self, pdf_id: str, user_id: str, file_path: str) -> ServiceResponse:
        """Process PDF content with FAISS - simplified like your prototype"""
        try:
            logger.info("Starting PDF text extraction...")
            
            # Check file size limit
            if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB limit
                return ServiceResponse.error_response("PDF file too large (>50MB)")
            
            # Extract text
            success, message, documents = self.pdf_processor.extract_text_from_pdf(file_path)
            if not success:
                logger.error(f"Text extraction failed: {message}")
                return ServiceResponse.error_response(message)
            
            logger.info(f"Text extraction completed, {len(documents)} chunks")
            
            # Create FAISS vectors
            logger.info("Creating FAISS vectors...")
            vector_result = vector_service.create_pdf_vectors(user_id, pdf_id, documents)
            
            if not vector_result.success:
                logger.error(f"FAISS vector creation failed: {vector_result.message}")
                return vector_result

            logger.info("PDF processing completed successfully")
            return ServiceResponse.success_response("PDF content processed successfully")
            
        except Exception as e:
            logger.error(f"Error in PDF content processing: {str(e)}", exc_info=True)
            return ServiceResponse.error_response(f"Processing failed: {str(e)}")

    def get_user_pdfs(self, user_id: str, folder_id: str = None) -> ServiceResponse:
        try:
            query = {"user_id": ObjectId(user_id)}
            if folder_id:
                query["folder_id"] = ObjectId(folder_id)

            pdfs_data = list(self.collection.find(query).sort("upload_date", -1))
            pdfs = [PDF(data).to_display_dict() for data in pdfs_data]
            return ServiceResponse.success_response(f"Found {len(pdfs)} PDFs", pdfs)

        except Exception as e:
            self.log_error("Error getting user PDFs", e)
            return ServiceResponse.error_response("Failed to get PDFs")

    def get_pdf_by_id(self, pdf_id: str, user_id: str = None) -> Optional[PDF]:
        try:
            query = {"_id": ObjectId(pdf_id)}
            if user_id:
                query["user_id"] = ObjectId(user_id)

            pdf_data = self.collection.find_one(query)
            return PDF(pdf_data) if pdf_data else None
        except Exception as e:
            self.log_error(f"Error getting PDF by ID: {pdf_id}", e)
            return None

    def delete_pdf(self, pdf_id: str, user_id: str) -> ServiceResponse:
        """Delete a specific PDF and its vectors - FIXED VERSION"""
        try:
            pdf = self.get_pdf_by_id(pdf_id, user_id)
            if not pdf:
                return ServiceResponse.error_response("PDF not found")

            # Delete physical file
            if pdf.file_path and os.path.exists(pdf.file_path):
                try:
                    self.pdf_processor.delete_pdf_file(pdf.file_path)
                    logger.info(f"Deleted physical file: {pdf.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete physical file: {e}")

            # Delete FAISS vectors
            try:
                vector_result = vector_service.delete_pdf_vectors(user_id, pdf_id)
                if not vector_result.success:
                    logger.warning(f"Failed to delete vectors: {vector_result.message}")
                else:
                    logger.info(f"Deleted vectors for PDF {pdf_id}")
            except Exception as e:
                logger.warning(f"Error deleting vectors: {e}")

            # Delete from database
            result = self.collection.delete_one({
                "_id": ObjectId(pdf_id),
                "user_id": ObjectId(user_id)
            })

            if result.deleted_count == 0:
                return ServiceResponse.error_response("PDF not found in database")

            self.log_info(f"PDF deleted successfully: {pdf.original_name}")
            return ServiceResponse.success_response(
                f"PDF '{pdf.original_name}' deleted successfully",
                {"deleted_pdf_id": pdf_id, "deleted_pdf_name": pdf.original_name}
            )

        except Exception as e:
            self.log_error("Error deleting PDF", e)
            return ServiceResponse.error_response(f"Failed to delete PDF: {str(e)}")

    def delete_folder_pdfs(self, folder_id: str, user_id: str) -> ServiceResponse:
        """Delete all PDFs in a specific folder - FIXED VERSION"""
        try:
            # Get all PDFs in the folder first
            pdfs_result = self.get_user_pdfs(user_id, folder_id)
            if not pdfs_result.success:
                return pdfs_result

            if not pdfs_result.data:
                return ServiceResponse.success_response("No PDFs to delete in folder")

            deleted_count = 0
            failed_deletes = []
            
            for pdf_data in pdfs_result.data:
                delete_result = self.delete_pdf(pdf_data['id'], user_id)
                if delete_result.success:
                    deleted_count += 1
                else:
                    failed_deletes.append(pdf_data['name'])
                    logger.warning(f"Failed to delete PDF {pdf_data['name']}: {delete_result.message}")

            if failed_deletes:
                message = f"Deleted {deleted_count} PDFs, failed to delete: {', '.join(failed_deletes)}"
                return ServiceResponse.success_response(message, {"deleted_count": deleted_count, "failed": failed_deletes})
            else:
                return ServiceResponse.success_response(
                    f"Successfully deleted {deleted_count} PDFs from folder",
                    {"deleted_count": deleted_count}
                )

        except Exception as e:
            self.log_error("Error deleting folder PDFs", e)
            return ServiceResponse.error_response(f"Failed to delete folder PDFs: {str(e)}")

    def search_pdf_content(self, pdf_id: str, user_id: str, query: str, n_results: int = 5) -> ServiceResponse:
        try:
            pdf = self.get_pdf_by_id(pdf_id, user_id)
            if not pdf:
                return ServiceResponse.error_response("PDF not found")
            if not pdf.processed:
                return ServiceResponse.error_response("PDF is still being processed")
            
            return vector_service.search_pdf_vectors(user_id, pdf_id, query, n_results)
        except Exception as e:
            self.log_error("Error searching PDF content", e)
            return ServiceResponse.error_response("Search failed")

    def get_pdf_count_for_user(self, user_id: str) -> int:
        """Get total PDF count for a user"""
        try:
            return self.collection.count_documents({"user_id": ObjectId(user_id)})
        except Exception as e:
            self.log_error("Error counting PDFs", e)
            return 0

    def get_pdf_info(self, pdf_id: str, user_id: str) -> ServiceResponse:
        """Get PDF information - ADDED METHOD"""
        try:
            pdf = self.get_pdf_by_id(pdf_id, user_id)
            if not pdf:
                return ServiceResponse.error_response("PDF not found")
            
            return ServiceResponse.success_response("PDF info retrieved", pdf.to_display_dict())
            
        except Exception as e:
            self.log_error(f"Error getting PDF info {pdf_id}", e)
            return ServiceResponse.error_response(f"Error retrieving PDF info: {str(e)}")

    def update_pdf_status(self, pdf_id: str, processed: bool) -> ServiceResponse:
        """Update PDF processing status - ADDED METHOD"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pdf_id)},
                {"$set": {"processed": processed}}
            )
            
            if result.modified_count > 0:
                return ServiceResponse.success_response("PDF status updated successfully")
            else:
                return ServiceResponse.error_response("PDF not found or status unchanged")
                
        except Exception as e:
            self.log_error("Error updating PDF status", e)
            return ServiceResponse.error_response(f"Error updating PDF status: {str(e)}")

    def search_pdfs(self, user_id: str, query: str, folder_id: str = None) -> ServiceResponse:
        """Search PDFs by name or content - ADDED METHOD"""
        try:
            search_filter = {
                "user_id": ObjectId(user_id),
                "$or": [
                    {"filename": {"$regex": query, "$options": "i"}},
                    {"original_name": {"$regex": query, "$options": "i"}}
                ]
            }
            
            if folder_id:
                search_filter["folder_id"] = ObjectId(folder_id)
            
            pdfs_data = list(self.collection.find(search_filter).sort("upload_date", -1))
            pdfs = [PDF(data).to_display_dict() for data in pdfs_data]
            
            return ServiceResponse.success_response(
                f"Found {len(pdfs)} PDFs matching '{query}'",
                pdfs
            )
            
        except Exception as e:
            self.log_error("Error searching PDFs", e)
            return ServiceResponse.error_response(f"Error searching PDFs: {str(e)}")