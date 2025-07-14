from datetime import datetime
from typing import Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from .base import BaseService, ServiceResponse
from ..models import User

class AuthService(BaseService):
    """Authentication service for user management"""

    def __init__(self):
        super().__init__("users")

    def register_user(self, username: str, password: str, email: str = "") -> ServiceResponse:
        try:
            if not username or not password:
                return ServiceResponse.error_response("Username and password are required")
            if len(password) < 6:
                return ServiceResponse.error_response("Password must be at least 6 characters")

            if self.collection.find_one({"username": username}):
                return ServiceResponse.error_response("Username already exists")

            user = User()
            user.username = username.strip()
            user.email = email.strip()
            user.password_hash = User.hash_password(password)
            user.created_at = datetime.utcnow()

            result = self.collection.insert_one(user.to_dict())
            user._id = result.inserted_id

            self.log_info(f"User registered: {username}")
            return ServiceResponse.success_response("User registered successfully", user.to_safe_dict())

        except DuplicateKeyError:
            return ServiceResponse.error_response("Username already exists")
        except Exception as e:
            self.log_error("Error registering user", e)
            return ServiceResponse.error_response(f"Registration failed: {str(e)}")

    def login_user(self, username: str, password: str) -> ServiceResponse:
        try:
            if not username or not password:
                return ServiceResponse.error_response("Username and password are required")

            user_data = self.collection.find_one({"username": username.strip()})
            if not user_data:
                return ServiceResponse.error_response("Invalid username or password")

            user = User(user_data)

            if not user.is_active():
                return ServiceResponse.error_response("Account is suspended")

            if not User.verify_password(password, user.password_hash):
                return ServiceResponse.error_response("Invalid username or password")

            user.last_login = datetime.utcnow()
            self.collection.update_one({"_id": user._id}, {"$set": {"last_login": user.last_login}})

            self.log_info(f"User logged in: {username}")
            return ServiceResponse.success_response("Login successful", user.to_safe_dict())

        except Exception as e:
            self.log_error("Error during login", e)
            return ServiceResponse.error_response("Login failed")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_data = self.collection.find_one({"_id": ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception as e:
            self.log_error(f"Error getting user by ID: {user_id}", e)
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            user_data = self.collection.find_one({"username": username})
            return User(user_data) if user_data else None
        except Exception as e:
            self.log_error(f"Error getting user by username: {username}", e)
            return None

    def update_user_password(self, user_id: str, old_password: str, new_password: str) -> ServiceResponse:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return ServiceResponse.error_response("User not found")

            if not User.verify_password(old_password, user.password_hash):
                return ServiceResponse.error_response("Current password is incorrect")

            if len(new_password) < 6:
                return ServiceResponse.error_response("New password must be at least 6 characters")

            new_hash = User.hash_password(new_password)
            self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": new_hash}})

            self.log_info(f"Password updated: {user.username}")
            return ServiceResponse.success_response("Password updated successfully")

        except Exception as e:
            self.log_error("Error updating password", e)
            return ServiceResponse.error_response("Failed to update password")

    def suspend_user(self, user_id: str) -> ServiceResponse:
        try:
            result = self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "suspended"}})
            if result.matched_count == 0:
                return ServiceResponse.error_response("User not found")
            self.log_info(f"User suspended: {user_id}")
            return ServiceResponse.success_response("User suspended successfully")
        except Exception as e:
            self.log_error("Error suspending user", e)
            return ServiceResponse.error_response("Failed to suspend user")

    def activate_user(self, user_id: str) -> ServiceResponse:
        try:
            result = self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active"}})
            if result.matched_count == 0:
                return ServiceResponse.error_response("User not found")
            self.log_info(f"User activated: {user_id}")
            return ServiceResponse.success_response("User activated successfully")
        except Exception as e:
            self.log_error("Error activating user", e)
            return ServiceResponse.error_response("Failed to activate user")
