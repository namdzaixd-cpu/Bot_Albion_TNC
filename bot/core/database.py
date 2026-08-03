import os
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client globally
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase():
    return supabase
