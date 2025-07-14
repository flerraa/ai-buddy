from datetime import datetime
from typing import Dict, Any
from bson import ObjectId

class PDF:
    """PDF model for database operations"""
    
    def __init__(self, data: Dict[str, Any] = None):
        if data:
            self._id = data.get('_id')
            self.user_id = data.get('user_id')
            self.folder_id = data.get('folder_id')
            self.filename = data.get('filename')
            self.original_name = data.get('original_name')
            self.file_path = data.get('file_path')
            self.vector_collection_name = data.get('vector_collection_name')
            self.file_size = data.get('file_size', 0)
            self.upload_date = data.get('upload_date')
            self.processed = data.get('processed', False)
        else:
            self._id = None
            self.user_id = None
            self.folder_id = None
            self.filename = None
            self.original_name = None
            self.file_path = None
            self.vector_collection_name = None
            self.file_size = 0
            self.upload_date = None
            self.processed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': ObjectId(self.user_id) if isinstance(self.user_id, str) else self.user_id,
            'folder_id': ObjectId(self.folder_id) if isinstance(self.folder_id, str) else self.folder_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'vector_collection_name': self.vector_collection_name,
            'file_size': self._safe_file_size(),
            'upload_date': self.upload_date or datetime.utcnow(),
            'processed': self.processed
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self._id) if self._id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'folder_id': str(self.folder_id) if self.folder_id else None,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'vector_collection_name': self.vector_collection_name,
            'file_size': self._safe_file_size(),  # Use safe file size method
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed': self.processed
        }

    def _safe_file_size(self) -> int:
        """Safely return file size as integer, handling None values"""
        try:
            if self.file_size is None or self.file_size == "":
                return 0
            
            # Convert to number if it's a string
            if isinstance(self.file_size, str):
                try:
                    return int(float(self.file_size))
                except (ValueError, TypeError):
                    return 0
            
            # Ensure it's a valid number
            if isinstance(self.file_size, (int, float)) and self.file_size >= 0:
                return int(self.file_size)
            else:
                return 0
                
        except Exception:
            return 0

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    def mark_as_processed(self):
        self.processed = True

    def get_size_formatted(self) -> str:
        safe_size = self._safe_file_size()
        if safe_size < 1024:
            return f"{safe_size} B"
        elif safe_size < 1024 * 1024:
            return f"{safe_size / 1024:.1f} KB"
        else:
            return f"{safe_size / (1024 * 1024):.1f} MB"