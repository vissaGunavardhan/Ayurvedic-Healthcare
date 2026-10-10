import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file explicitly
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-ayurcare-2026')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    DATABASE_PATH = BASE_DIR / 'healthcare.db'
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Gemini models
    GEMINI_MODEL = 'gemini-3.8-flash'
    GEMINI_EMBEDDING_MODEL = 'gemini-embedding-001'

    # Fallback coordinates (if user IP or browser permission defaults before GPS locks)
    DEFAULT_LAT = 17.3850  # Hyderabad default coordinate example
    DEFAULT_LNG = 78.4867
