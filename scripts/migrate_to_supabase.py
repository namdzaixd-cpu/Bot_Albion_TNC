import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY is missing in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "Storage")

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

print("Starting migration from JSON to Supabase...")

# 1. Migrate AI Config (tnc_ai_config.json -> ai_config)
ai_config = load_json("tnc_ai_config.json")
if ai_config:
    print("Migrating ai_config...")
    guild_id = "default"  # Using 'default' since it was global before
    try:
        supabase.table("ai_config").upsert({
            "guild_id": guild_id,
            "model": ai_config.get("model", "inclusionai/ling-3.0-flash:free"),
            "available_models": ai_config.get("available_models", []),
            "channel_buffers": ai_config.get("channel_buffers", {}),
            "intercept_channels": ai_config.get("intercept_channels", []),
            "autowiki_channels": ai_config.get("autowiki_channels", [])
        }).execute()
        print("ai_config migrated successfully.")
    except Exception as e:
        print(f"Error migrating ai_config: {e}")

# 2. Migrate Last Seen (tnc_lastseen_v1.json -> user_activity)
lastseen = load_json("tnc_lastseen_v1.json")
if lastseen:
    print(f"Migrating {len(lastseen)} user_activity records...")
    records = []
    for user_id, timestamp in lastseen.items():
        records.append({"user_id": user_id, "last_seen": timestamp})
    
    # Supabase allows bulk upsert
    if records:
        try:
            # Upsert in chunks of 1000 to be safe
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i+chunk_size]
                supabase.table("user_activity").upsert(chunk).execute()
            print("user_activity migrated successfully.")
        except Exception as e:
            print(f"Error migrating user_activity: {e}")

# 3. Migrate Silver Pieces (tnc_sp_v32.json -> user_economy)
sp_data = load_json("tnc_sp_v32.json")
if sp_data:
    history = sp_data.get("history", {})
    print(f"Migrating {len(history)} user_economy records...")
    records = []
    for user_id, sp in history.items():
        records.append({"user_id": user_id, "silver_pieces": int(sp)})
        
    if records:
        try:
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i+chunk_size]
                supabase.table("user_economy").upsert(chunk).execute()
            print("user_economy migrated successfully.")
        except Exception as e:
            print(f"Error migrating user_economy: {e}")

# 4. Migrate TTS Config (tnc_tts_config_v1.json -> tts_config)
tts_data = load_json("tnc_tts_config_v1.json")
if tts_data:
    print(f"Migrating {len(tts_data)} tts_config records...")
    records = []
    for user_id, voice in tts_data.items():
        records.append({"user_id": user_id, "voice": voice})
        
    if records:
        try:
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i+chunk_size]
                supabase.table("tts_config").upsert(chunk).execute()
            print("tts_config migrated successfully.")
        except Exception as e:
            print(f"Error migrating tts_config: {e}")

print("Migration completed!")
