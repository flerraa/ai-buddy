# 🤖 AI Buddy - AI Tutor Bot To Encourage Self Learning

> Transform your PDF study materials into interactive learning experiences with AI-powered quiz generation and real-time tutoring assistance.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-brightgreen.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Overview

AI Buddy is a comprehensive educational platform that leverages artificial intelligence to create interactive learning experiences. Upload your PDF study materials and instantly generate intelligent quizzes with real-time AI tutoring support through both text and voice interaction.

### ✨ Key Features

- **🧠 Intelligent Quiz Generation**: Automatically create MCQ and open-ended questions from PDF content using Large Language Models
- **🎯 AI-Powered Tutoring**: Real-time contextual explanations, hints, and learning guidance
- **🎤 Voice Interaction**: Speech-to-text input and text-to-speech responses for natural conversation
- **📁 Smart Document Management**: Organize study materials with hierarchical folder system
- **🔍 Semantic Search**: Advanced RAG (Retrieval-Augmented Generation) for context-aware responses
- **📊 Learning Analytics**: Track quiz performance and learning progress
- **🌐 Cross-Platform**: Web-based interface accessible on desktop, tablet, and mobile

## 🛠️ Technology Stack

### Backend
- **Python FastAPI**: High-performance API development with async support
- **MongoDB**: Document-based database for user data and file metadata
- **FAISS**: Vector database for semantic search and document embeddings
- **Ollama**: Local Large Language Model deployment and inference

### AI & Machine Learning
- **HuggingFace Transformers**: Document embedding generation and NLP processing
- **LangChain**: LLM application framework for RAG implementation
- **Sentence Transformers**: Semantic text understanding and similarity search

### Voice Processing
- **Faster Whisper**: High-accuracy speech-to-text transcription
- **Coqui TTS**: Natural text-to-speech synthesis
- **Dedicated Voice Service**: Separate FastAPI microservice for audio processing

### Frontend
- **Streamlit**: Interactive web application with real-time components
- **Responsive Design**: Mobile-friendly interface with modern UI components

## 🏗️ Architecture

    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Frontend      │    │   Backend       │    │  Voice Service  │
    │   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
    │   Port: 8501    │    │   MongoDB       │    │   Port: 8001    │
    └─────────────────┘    │   FAISS         │    └─────────────────┘
                           │   Ollama LLM    │
                           └─────────────────┘

## 📋 Prerequisites

- **Python 3.11+**
- **MongoDB ** 
- **NVIDIA GPU** (recommended for optimal AI performance)
- **Minimum 8GB RAM** (16GB+ recommended or more)
- **5GB+ free disk space**

## 🚀 Quick Start

### 1. Clone Repository

    git clone https://github.com/yourusername/ai-buddy.git
    cd ai-buddy

### 2. Environment Setup

    # Create virtual environment
    python -m venv venv

    # Activate virtual environment
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

### 3. MongoDB Setup

    # Install MongoDB Community Edition
    # Windows: Download from https://www.mongodb.com/try/download/community
    # macOS: brew install mongodb-community
    # Ubuntu: sudo apt install mongodb

    # Start MongoDB service
    mongod

### 4. Ollama Installation

    # Download and install Ollama from https://ollama.ai
    # Pull required model
    ollama pull deepseek-r1:8b

### 5. Voice Service Setup

    cd voicemode
    python -m venv venv
    venv\Scripts\activate  # Windows
    # source venv/bin/activate  # macOS/Linux
    pip install -r requirements.txt

    # Start voice service
    python voice_service.py

### 6. Launch Application

    # In main directory
    python run run.py

Navigate to http://localhost:8501 to access AI Buddy!

## 📖 Usage Guide

### Getting Started
1. **Register/Login**: Create your account or sign in
2. **Create Folders**: Organize your study materials
3. **Upload PDFs**: Add your study documents (up to 50MB)
4. **Generate Quizzes**: Choose quiz type and difficulty
5. **Study Interactively**: Attempt quizzes with AI tutoring support
6. **Voice Mode**: Use speech for natural conversation with AI tutor

### Features Walkthrough

#### 📄 Document Upload
- Supports PDF files up to 50MB
- Automatic content extraction and processing
- Vector embedding generation for semantic search

#### 🧠 Quiz Generation
- **Multiple Choice Questions**: AI-generated with 4 options
- **Open-Ended Questions**: Encourage critical thinking
- **Difficulty Levels**: Easy, Medium, Hard
- **Custom Topics**: Focus on specific subjects

#### 🎯 AI Tutoring
- **Context-Aware Explanations**: Based on your study material
- **Adaptive Hints**: Guidance without revealing answers
- **Real-Time Support**: Instant help during quiz attempts

#### 🎤 Voice Interaction
- **Speech Input**: Ask questions naturally
- **Audio Responses**: Hear explanations aloud
- **Conversation Mode**: Extended dialogue with AI tutor

## 🔧 Configuration

### Environment Variables
Create .env file in root directory:

    MONGODB_URL=mongodb://localhost:27017/
    OLLAMA_BASE_URL=http://localhost:11434
    VOICE_SERVICE_URL=http://localhost:8001
    DEBUG=True

### Model Configuration

    # Supported Ollama models
    SUPPORTED_MODELS = [
        "deepseek-r1:8b",
        "llama3.2:3b",
        "mistral:7b"
    ]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Future Enhancements

- [ ] **Multi-language Support**: Support for documents in different languages
- [ ] **Collaborative Learning**: Shared study sessions and group quizzes
- [ ] **Mobile App**: Native iOS/Android applications
- [ ] **Advanced Analytics**: Detailed learning progress insights
- [ ] **Integration**: LMS integration and API endpoints

## 📞 Contact & Support

- **Author**: Muhammad Syazwan Akmal bin Sahimi
- **Email**: syazwanakmal80@gmail.com
- **University**: Universiti Tenaga Nasional (UNITEN)

## 🏆 Acknowledgments

- **Supervisor**: TS. Dr. Mohd Hazli bin Mohamed Zabil
- **Institution**: College of Computing and Informatics, UNITEN
- **Project Type**: Final Year Project (FYP)
- **Academic Year**: 2025

---

⭐ **Star this repository if AI Buddy helped enhance your learning experience!**

---

*Built with ❤️ for the future of education*
