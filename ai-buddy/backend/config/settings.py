import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ai_buddy")

    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Changed from CHROMADB_PATH to FAISS_PATH
    FAISS_PATH: str = os.getenv("FAISS_PATH", "./user_data")  # FAISS vectors stored in user_data
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "ai-buddy-secret-key")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    USER_DATA_PATH: str = os.getenv("USER_DATA_PATH", "./user_data")

    TTS_SERVICE_URL: str = os.getenv("TTS_SERVICE_URL", "http://localhost:5001")
    STT_SERVICE_URL: str = os.getenv("STT_SERVICE_URL", "http://localhost:5002")

    # NEW: Voice service URL for voicemode communication
    VOICE_SERVICE_URL: str = os.getenv("VOICE_SERVICE_URL", "http://127.0.0.1:8001")

    # Updated embedding model to match your prototype exactly
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Updated chunk sizes to match your prototype
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    def ensure_directories(self):
        os.makedirs(self.USER_DATA_PATH, exist_ok=True)
        os.makedirs(self.FAISS_PATH, exist_ok=True)

settings = Settings()
settings.ensure_directories()