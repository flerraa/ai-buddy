# File: backend/services/ai_cache.py - NEW FILE
import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ..config import settings
import logging

logger = logging.getLogger(__name__)

@st.cache_resource
def get_cached_embeddings():
    """Cache embeddings globally like the prototype"""
    try:
        logger.info(f"🔄 Loading cached HuggingFace embeddings: {settings.EMBEDDING_MODEL}")
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        logger.info(f"✅ Cached HuggingFace embeddings loaded: {settings.EMBEDDING_MODEL}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to load cached embedding model: {e}")
        raise

@st.cache_resource  
def get_cached_ollama():
    """Cache Ollama model globally like the prototype"""
    try:
        logger.info(f"🔄 Loading cached Ollama model: {settings.OLLAMA_MODEL}")
        model = Ollama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        logger.info(f"✅ Cached Ollama model loaded: {settings.OLLAMA_MODEL}")
        return model
    except Exception as e:
        logger.error(f"Failed to load cached Ollama model: {e}")
        raise