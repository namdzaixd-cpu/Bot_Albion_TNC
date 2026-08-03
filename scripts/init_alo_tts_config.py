import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "Storage")
filepath = os.path.join(DATA_DIR, "tnc_tts_config_v1.json")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        record = {
            "id": 1,
            "read_name": data.get("read_name", {}),
            "rejoin": data.get("rejoin", {}),
            "afk": data.get("afk", {})
        }
        supabase.table("alo_tts_config").upsert(record).execute()
        print("Migrated alo_tts_config successfully.")
