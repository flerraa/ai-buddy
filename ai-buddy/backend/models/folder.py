from datetime import datetime
from typing import Dict, Any
from bson import ObjectId

class Folder:
    """Folder model for database operations"""
    
    def __init__(self, data: Dict[str, Any] = None):
        if data:
            self._id = data.get('_id')
            self.user_id = data.get('user_id')
            self.name = data.get('name')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            self._id = None
            self.user_id = None
            self.name = None
            self.created_at = None
            self.updated_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': ObjectId(self.user_id) if isinstance(self.user_id, str) else self.user_id,
            'name': self.name,
            'created_at': self.created_at or datetime.utcnow(),
            'updated_at': self.updated_at or datetime.utcnow()
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self._id) if self._id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    def update_timestamp(self):
        self.updated_at = datetime.utcnow()
