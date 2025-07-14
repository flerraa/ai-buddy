from abc import ABC
from pymongo.collection import Collection
from ..config import db_manager
import logging

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base service class for common database operations"""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection: Collection = db_manager.get_collection(collection_name)

    def get_collection(self) -> Collection:
        return self.collection

    def log_error(self, message: str, exception: Exception = None):
        error_msg = f"[{self.__class__.__name__}] {message}"
        if exception:
            error_msg += f": {str(exception)}"
        logger.error(error_msg)

    def log_info(self, message: str):
        logger.info(f"[{self.__class__.__name__}] {message}")

    def log_warning(self, message: str):
        logger.warning(f"[{self.__class__.__name__}] {message}")


class ServiceResponse:
    """Standardized service response"""

    def __init__(self, success: bool, message: str, data: any = None):
        self.success = success
        self.message = message
        self.data = data

    def to_dict(self):
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data
        }

    @classmethod
    def success_response(cls, message: str, data: any = None):
        return cls(True, message, data)

    @classmethod
    def error_response(cls, message: str, data: any = None):
        return cls(False, message, data)
