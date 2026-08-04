import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

direct_url = "postgresql://postgres:Namtranpro2252.@db.woxqipelqbyqvvdqczuj.supabase.co:5432/postgres"

sql = """
CREATE TABLE IF NOT EXISTS chat_history (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS discord_channels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    guild_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS discord_roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT,
    guild_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
"""

def run():
    print(f"Connecting to {direct_url}...")
    try:
        conn = psycopg2.connect(direct_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        print("✅ Tables created successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
