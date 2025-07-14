from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
import bcrypt

class User:
    """User model for database operations"""
    
    def __init__(self, data: Dict[str, Any] = None):
        if data:
            self._id = data.get('_id')
            self.username = data.get('username')
            self.email = data.get('email', '')
            self.password_hash = data.get('password_hash')
            self.role = data.get('role', 'user')
            self.status = data.get('status', 'active')
            self.created_at = data.get('created_at')
            self.last_login = data.get('last_login')
        else:
            self._id = None
            self.username = None
            self.email = ''
            self.password_hash = None
            self.role = 'user'
            self.status = 'active'
            self.created_at = None
            self.last_login = None

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at or datetime.utcnow(),
            'last_login': self.last_login
        }

    def to_safe_dict(self) -> Dict[str, Any]:
        return {
            '_id': str(self._id) if self._id else None,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at,
            'last_login': self.last_login
        }

    @property
    def id(self) -> str:
        return str(self._id) if self._id else None

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_active(self) -> bool:
        return self.status == 'active'
