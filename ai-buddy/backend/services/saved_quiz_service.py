# File: backend/services/saved_quiz_service.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from backend.models.saved_quiz import SavedQuiz
from .base import BaseService, ServiceResponse

class SavedQuizService(BaseService):
    """Service for managing saved quizzes"""
    
    def __init__(self):
        super().__init__("saved_quizzes")
    
    def save_quiz(self, user_id: str, folder_id: str, pdf_id: str, pdf_name: str,
                  quiz_name: str, quiz_type: str, difficulty: str, 
                  questions_data: List[Dict], topic_focus: str = None) -> ServiceResponse:
        """Save a new quiz"""
        try:
            # Check if quiz name already exists in this folder
            existing = self.collection.find_one({
                "user_id": user_id,
                "folder_id": folder_id,
                "quiz_name": quiz_name
            })
            
            if existing:
                return ServiceResponse.error_response(
                    "Quiz name already exists in this folder. Please choose a different name."
                )
            
            # Create new saved quiz
            saved_quiz = SavedQuiz(
                user_id=user_id,
                folder_id=folder_id,
                pdf_id=pdf_id,
                pdf_name=pdf_name,
                quiz_name=quiz_name,
                quiz_type=quiz_type,
                difficulty=difficulty,
                questions_data=questions_data,
                topic_focus=topic_focus
            )
            
            # Insert into database
            result = self.collection.insert_one(saved_quiz.to_dict())
            saved_quiz.set_id(result.inserted_id)
            
            self.log_info(f"Quiz saved: {quiz_name} by user {user_id}")
            return ServiceResponse.success_response(
                "Quiz saved successfully!",
                saved_quiz.get_display_info()
            )
            
        except Exception as e:
            self.log_error("Error saving quiz", e)
            return ServiceResponse.error_response(f"Error saving quiz: {str(e)}")
    
    def get_folder_quizzes(self, user_id: str, folder_id: str) -> ServiceResponse:
        """Get all saved quizzes for a folder"""
        try:
            quizzes_data = list(self.collection.find({
                "user_id": user_id,
                "folder_id": folder_id
            }).sort("created_at", -1))
            
            quizzes = []
            for quiz_data in quizzes_data:
                quiz_data['id'] = str(quiz_data['_id'])
                saved_quiz = SavedQuiz.from_dict(quiz_data)
                saved_quiz.set_id(quiz_data['_id'])
                quizzes.append(saved_quiz.get_display_info())
            
            return ServiceResponse.success_response(
                "Quizzes retrieved successfully",
                quizzes
            )
            
        except Exception as e:
            self.log_error("Error retrieving quizzes", e)
            return ServiceResponse.error_response(f"Error retrieving quizzes: {str(e)}")
    
    def get_quiz_by_id(self, quiz_id: str, user_id: str) -> ServiceResponse:
        """Get a specific saved quiz by ID"""
        try:
            quiz_data = self.collection.find_one({
                "_id": ObjectId(quiz_id),
                "user_id": user_id
            })
            
            if not quiz_data:
                return ServiceResponse.error_response("Quiz not found")
            
            quiz_data['id'] = str(quiz_data['_id'])
            saved_quiz = SavedQuiz.from_dict(quiz_data)
            saved_quiz.set_id(quiz_data['_id'])
            
            return ServiceResponse.success_response(
                "Quiz retrieved successfully",
                {
                    "quiz_info": saved_quiz.get_display_info(),
                    "questions": saved_quiz.questions_data,
                    "pdf_id": saved_quiz.pdf_id,
                    "pdf_name": saved_quiz.pdf_name
                }
            )
            
        except Exception as e:
            self.log_error("Error retrieving quiz", e)
            return ServiceResponse.error_response(f"Error retrieving quiz: {str(e)}")
    
    def update_quiz_name(self, quiz_id: str, user_id: str, new_name: str) -> ServiceResponse:
        """Update quiz name"""
        try:
            # Check if new name already exists in the same folder
            quiz_data = self.collection.find_one({
                "_id": ObjectId(quiz_id),
                "user_id": user_id
            })
            
            if not quiz_data:
                return ServiceResponse.error_response("Quiz not found")
            
            # Check for name conflicts in the same folder
            existing = self.collection.find_one({
                "user_id": user_id,
                "folder_id": quiz_data["folder_id"],
                "quiz_name": new_name,
                "_id": {"$ne": ObjectId(quiz_id)}
            })
            
            if existing:
                return ServiceResponse.error_response(
                    "Quiz name already exists in this folder"
                )
            
            # Update the quiz name
            result = self.collection.update_one(
                {"_id": ObjectId(quiz_id), "user_id": user_id},
                {
                    "$set": {
                        "quiz_name": new_name,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.log_info(f"Quiz renamed: {quiz_id} to {new_name}")
                return ServiceResponse.success_response("Quiz name updated successfully")
            else:
                return ServiceResponse.error_response("No changes made")
                
        except Exception as e:
            self.log_error("Error updating quiz name", e)
            return ServiceResponse.error_response(f"Error updating quiz name: {str(e)}")
    
    def delete_quiz(self, quiz_id: str, user_id: str) -> ServiceResponse:
        """Delete a saved quiz"""
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(quiz_id),
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                self.log_info(f"Quiz deleted: {quiz_id}")
                return ServiceResponse.success_response("Quiz deleted successfully")
            else:
                return ServiceResponse.error_response("Quiz not found")
                
        except Exception as e:
            self.log_error("Error deleting quiz", e)
            return ServiceResponse.error_response(f"Error deleting quiz: {str(e)}")
    
    def delete_quizzes_by_pdf(self, pdf_id: str, user_id: str) -> ServiceResponse:
        """Delete all quizzes associated with a PDF"""
        try:
            result = self.collection.delete_many({
                "pdf_id": pdf_id,
                "user_id": user_id
            })
            
            self.log_info(f"Deleted {result.deleted_count} quizzes for PDF {pdf_id}")
            return ServiceResponse.success_response(
                f"Deleted {result.deleted_count} associated quizzes",
                {"deleted_count": result.deleted_count}
            )
            
        except Exception as e:
            self.log_error("Error deleting quizzes by PDF", e)
            return ServiceResponse.error_response(f"Error deleting quizzes: {str(e)}")
    
    def delete_quizzes_by_folder(self, folder_id: str, user_id: str) -> ServiceResponse:
        """Delete all quizzes in a folder"""
        try:
            result = self.collection.delete_many({
                "folder_id": folder_id,
                "user_id": user_id
            })
            
            self.log_info(f"Deleted {result.deleted_count} quizzes for folder {folder_id}")
            return ServiceResponse.success_response(
                f"Deleted {result.deleted_count} quizzes from folder",
                {"deleted_count": result.deleted_count}
            )
            
        except Exception as e:
            self.log_error("Error deleting folder quizzes", e)
            return ServiceResponse.error_response(f"Error deleting folder quizzes: {str(e)}")
    
    def get_quiz_count_by_pdf(self, pdf_id: str, user_id: str) -> int:
        """Get count of quizzes for a specific PDF"""
        try:
            return self.collection.count_documents({
                "pdf_id": pdf_id,
                "user_id": user_id
            })
        except Exception as e:
            self.log_error(f"Error counting quizzes for PDF {pdf_id}", e)
            return 0
    
    def generate_default_quiz_name(self, pdf_name: str, folder_id: str, user_id: str) -> str:
        """Generate default quiz name with incremental numbering"""
        try:
            # Get existing quiz count for this folder
            existing_count = self.collection.count_documents({
                "folder_id": folder_id,
                "user_id": user_id
            })
            
            quiz_number = existing_count + 1
            current_date = datetime.now().strftime("%m/%d/%Y")
            
            # Remove .pdf extension from pdf_name if present
            clean_pdf_name = pdf_name.replace('.pdf', '').replace('.PDF', '')
            
            default_name = f"Quiz {quiz_number} - {clean_pdf_name} - {current_date}"
            
            # Check if this name already exists and increment if needed
            while self.collection.find_one({
                "folder_id": folder_id,
                "user_id": user_id,
                "quiz_name": default_name
            }):
                quiz_number += 1
                default_name = f"Quiz {quiz_number} - {clean_pdf_name} - {current_date}"
            
            return default_name
            
        except Exception as e:
            self.log_error("Error generating default quiz name", e)
            # Fallback to simple naming
            return f"Quiz - {pdf_name} - {datetime.now().strftime('%m/%d/%Y')}"