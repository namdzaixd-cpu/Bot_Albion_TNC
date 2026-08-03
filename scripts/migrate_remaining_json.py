import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "Storage")

# Only these files should go to json_storage
REMAINING_FILES = [
    "tnc_massing_v1.json",
    "tnc_templates_v1.json",
    "tnc_guildcheck_config.json",
    "tnc_guildcheck_v1.json",
    "tnc_coreconfig_v1.json",
    "tnc_core_credited_v1.json",
    "tnc_library_v1.json",
    "tnc_blacklist_v1.json"
]

for filename in REMAINING_FILES:
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        print(f"Migrating {filename} to Supabase json_storage...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            supabase.table("json_storage").upsert({
                "file_name": filename,
                "data": data
            }).execute()
            print(f"Success for {filename}")
        except Exception as e:
            print(f"Failed to migrate {filename}: {e}")
    else:
        print(f"File {filename} not found locally, skipping.")
