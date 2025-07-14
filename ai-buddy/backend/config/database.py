from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from .settings import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: MongoClient = None
        self.database: Database = None
        self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(settings.MONGODB_URL)
            self.database = self.client[settings.DATABASE_NAME]
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        return self.database[collection_name]

    def close_connection(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def setup_indexes(self):
        try:
            users_collection = self.get_collection("users")
            users_collection.create_index("username", unique=True)
            users_collection.create_index("email")

            folders_collection = self.get_collection("folders")
            folders_collection.create_index("user_id")
            folders_collection.create_index([("user_id", 1), ("name", 1)])

            pdfs_collection = self.get_collection("pdfs")
            pdfs_collection.create_index("user_id")
            pdfs_collection.create_index("folder_id")
            pdfs_collection.create_index([("user_id", 1), ("folder_id", 1)])

            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

db_manager = DatabaseManager()
db_manager.setup_indexes()
