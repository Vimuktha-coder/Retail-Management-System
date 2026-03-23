import os
from supabase import create_client, Client
from config import Config

supabase: Client = None
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_KEY = Config.SUPABASE_KEY

# Basic validation to prevent crashing on 'Invalid URL' error if user didn't set it in .env yet
if SUPABASE_URL and SUPABASE_URL.startswith("http"):
    if SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase client initialized.")
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
else:
    print("Warning: Missing or invalid Supabase URL in .env. Supabase client will be None, running app in UI-only mode.")
