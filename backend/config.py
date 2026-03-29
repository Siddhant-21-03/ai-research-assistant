"""
Configuration for the AI Research Assistant.
Loads environment variables and defines paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Paths
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# RAG Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "models/gemini-embedding-001"
LLM_MODEL = "gemini-2.5-flash"
COLLECTION_NAME = "research_docs"
