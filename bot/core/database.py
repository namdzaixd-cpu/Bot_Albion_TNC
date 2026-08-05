import os
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client globally
# Wrap in try-except to avoid crashing on CI environments where .env is missing
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception as e:
    print(f"Warning: Could not initialize Supabase client: {e}")
    supabase = None

def get_supabase():
    return supabase
