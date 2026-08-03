import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "Storage")
filepath = os.path.join(DATA_DIR, "tnc_sp_v32.json")
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        sp_data = json.load(f)
        last_update = sp_data.get("last_update", "Chưa có dữ liệu")
        supabase.table("sp_metadata").upsert({"id": 1, "last_update": last_update}).execute()
        print(f"Set sp_metadata last_update to {last_update}")
