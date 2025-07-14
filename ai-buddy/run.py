"""
AI Buddy Application Runner

This script runs the AI Buddy Streamlit application.
"""

import sys
import os
import streamlit as st
from datetime import datetime
import logging
import subprocess
from backend.services import PDFService
from frontend.components import AuthComponent, FolderManager, QuizDisplay, ChatInterface, SavedQuizManager

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import pymongo
        # Comment out optional dependencies for now
        # import chromadb
        # import langchain 
        # import sentence_transformers
        logger.info("Core dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False

def check_services():
    """Check if required services are running"""
    services_ok = True
    
    # Check MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        logger.info("MongoDB connection: OK")
        client.close()
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        logger.error("Please ensure MongoDB is running on localhost:27017")
        services_ok = False
    
    # Check Ollama (optional check - will show warning only)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama service: OK")
        else:
            logger.warning("Ollama service may not be running")
    except Exception as e:
        logger.warning(f"Ollama service check failed: {e}")
        logger.warning("Please ensure Ollama is running: ollama serve")
    
    return services_ok

def run_streamlit():
    """Run the Streamlit application"""
    try:
        # Run Streamlit from project root, not frontend directory
        frontend_app = os.path.join(project_root, 'frontend', 'app.py')
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            frontend_app,  # Full path to app.py
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        logger.info("Starting AI Buddy application...")
        logger.info("Opening http://localhost:8501 in your browser...")
        
        # Stay in project root directory - DON'T change to frontend
        # os.chdir(frontend_dir)  # <- This was causing the problem!
        
        # Run the command from project root
        subprocess.run(cmd, cwd=project_root)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")

def main():
    """Main entry point"""
    logger.info("🦉 AI Buddy - Starting application...")
    
    # Check dependencies
    if not check_dependencies():
        logger.warning("Some dependencies missing, but trying to continue...")
        # Don't exit, just continue
    
    # Check services
    if not check_services():
        logger.error("Service checks failed. Please fix the issues above.")
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("user_data", exist_ok=True)
    os.makedirs("chroma_data", exist_ok=True)
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main()