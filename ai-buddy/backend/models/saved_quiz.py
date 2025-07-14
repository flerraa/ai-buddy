# File: backend/models/saved_quiz.py

from datetime import datetime
from typing import Dict, List, Any, Optional
from bson import ObjectId

class SavedQuiz:
    """Model for saved quiz data"""
    
    def __init__(self, user_id: str, folder_id: str, pdf_id: str, pdf_name: str, 
                 quiz_name: str, quiz_type: str, difficulty: str, 
                 questions_data: List[Dict], topic_focus: str = None):
        self.user_id = user_id
        self.folder_id = folder_id
        self.pdf_id = pdf_id
        self.pdf_name = pdf_name
        self.quiz_name = quiz_name
        self.quiz_type = quiz_type
        self.difficulty = difficulty
        self.questions_data = questions_data
        self.topic_focus = topic_focus
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "pdf_id": self.pdf_id,
            "pdf_name": self.pdf_name,
            "quiz_name": self.quiz_name,
            "quiz_type": self.quiz_type,
            "difficulty": self.difficulty,
            "questions_data": self.questions_data,
            "topic_focus": self.topic_focus,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedQuiz':
        """Create SavedQuiz instance from dictionary"""
        quiz = cls(
            user_id=data["user_id"],
            folder_id=data["folder_id"],
            pdf_id=data["pdf_id"],
            pdf_name=data["pdf_name"],
            quiz_name=data["quiz_name"],
            quiz_type=data["quiz_type"],
            difficulty=data["difficulty"],
            questions_data=data["questions_data"],
            topic_focus=data.get("topic_focus")
        )
        quiz.created_at = data.get("created_at", datetime.utcnow())
        quiz.updated_at = data.get("updated_at", datetime.utcnow())
        return quiz
    
    def get_id(self) -> str:
        """Get quiz ID (set by database)"""
        return str(getattr(self, '_id', ''))
    
    def set_id(self, quiz_id: str):
        """Set quiz ID from database"""
        self._id = ObjectId(quiz_id) if isinstance(quiz_id, str) else quiz_id
    
    def get_question_count(self) -> int:
        """Get number of questions in quiz"""
        return len(self.questions_data)
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get formatted display information"""
        return {
            "id": self.get_id(),
            "name": self.quiz_name,
            "type": self.quiz_type,
            "difficulty": self.difficulty,
            "question_count": self.get_question_count(),
            "pdf_name": self.pdf_name,
            "created_at": self.created_at.strftime("%m/%d/%Y"),
            "topic_focus": self.topic_focus or "General"
        }