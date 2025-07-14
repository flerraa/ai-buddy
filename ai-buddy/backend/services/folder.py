from datetime import datetime
from typing import Optional
from bson import ObjectId
from .base import BaseService, ServiceResponse
from ..models import Folder

class FolderService(BaseService):
    """Service for folder management"""

    def __init__(self):
        super().__init__("folders")

    def create_folder(self, user_id: str, folder_name: str) -> ServiceResponse:
        try:
            if not folder_name or not folder_name.strip():
                return ServiceResponse.error_response("Folder name is required")

            folder_name = folder_name.strip()
            existing_folder = self.collection.find_one({
                "user_id": ObjectId(user_id),
                "name": folder_name
            })

            if existing_folder:
                return ServiceResponse.error_response("Folder name already exists")

            folder = Folder()
            folder.user_id = ObjectId(user_id)
            folder.name = folder_name
            folder.created_at = datetime.utcnow()
            folder.updated_at = datetime.utcnow()

            result = self.collection.insert_one(folder.to_dict())
            folder._id = result.inserted_id

            self.log_info(f"Folder created: {folder_name} for user {user_id}")
            return ServiceResponse.success_response("Folder created successfully", folder.to_display_dict())

        except Exception as e:
            self.log_error("Error creating folder", e)
            return ServiceResponse.error_response(f"Failed to create folder: {str(e)}")

    def get_user_folders(self, user_id: str) -> ServiceResponse:
        try:
            folders_data = list(self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", 1))
            folders = [Folder(folder).to_display_dict() for folder in folders_data]
            return ServiceResponse.success_response(f"Found {len(folders)} folders", folders)
        except Exception as e:
            self.log_error("Error getting user folders", e)
            return ServiceResponse.error_response("Failed to get folders")

    def get_folder_by_id(self, folder_id: str, user_id: str = None) -> Optional[Folder]:
        try:
            query = {"_id": ObjectId(folder_id)}
            if user_id:
                query["user_id"] = ObjectId(user_id)

            folder_data = self.collection.find_one(query)
            return Folder(folder_data) if folder_data else None
        except Exception as e:
            self.log_error(f"Error getting folder by ID: {folder_id}", e)
            return None

    def update_folder_name(self, folder_id: str, user_id: str, new_name: str) -> ServiceResponse:
        try:
            if not new_name or not new_name.strip():
                return ServiceResponse.error_response("Folder name is required")

            new_name = new_name.strip()
            existing_folder = self.collection.find_one({
                "user_id": ObjectId(user_id),
                "name": new_name,
                "_id": {"$ne": ObjectId(folder_id)}
            })

            if existing_folder:
                return ServiceResponse.error_response("Folder name already exists")

            result = self.collection.update_one(
                {"_id": ObjectId(folder_id), "user_id": ObjectId(user_id)},
                {"$set": {"name": new_name, "updated_at": datetime.utcnow()}}
            )

            if result.matched_count == 0:
                return ServiceResponse.error_response("Folder not found")

            self.log_info(f"Folder renamed to: {new_name}")
            return ServiceResponse.success_response("Folder name updated successfully")

        except Exception as e:
            self.log_error("Error updating folder name", e)
            return ServiceResponse.error_response("Failed to update folder name")

    def delete_folder(self, folder_id: str, user_id: str) -> ServiceResponse:
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(folder_id),
                "user_id": ObjectId(user_id)
            })

            if result.deleted_count == 0:
                return ServiceResponse.error_response("Folder not found")

            self.log_info(f"Folder deleted: {folder_id}")
            return ServiceResponse.success_response("Folder deleted successfully")

        except Exception as e:
            self.log_error("Error deleting folder", e)
            return ServiceResponse.error_response("Failed to delete folder")

    def get_folder_count_for_user(self, user_id: str) -> int:
        try:
            return self.collection.count_documents({"user_id": ObjectId(user_id)})
        except Exception as e:
            self.log_error("Error counting folders", e)
            return 0
