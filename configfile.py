import os
from dotenv import load_dotenv

load_dotenv()

# Access the keys using os.environ.get()
gemini_key = os.environ.get("GEMINI_API_KEY")
spotify_id = os.environ.get("sid")
spotify_secret = os.environ.get("sid_sec")
supabase_url = os.environ.get("supabase_url")
supabase_key = os.environ.get("supabase_key")
supabase_service = os.environ.get("supabase_service")
