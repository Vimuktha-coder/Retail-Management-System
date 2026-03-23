import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_default_secret_key_change_in_production')
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Session cookie settings
    SESSION_COOKIE_SECURE = True       # Enforce HTTPS
    SESSION_COOKIE_HTTPONLY = True     # Prevent JS access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF mitigation
