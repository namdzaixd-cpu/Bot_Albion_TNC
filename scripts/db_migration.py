import os
import psycopg2
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# We use DIRECT_URL for migrations
db_url = os.environ.get("DIRECT_URL")
if not db_url:
    print("Thiếu DIRECT_URL trong .env")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()

    # Create discord_channels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discord_channels (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
    """)

    # Create discord_roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discord_roles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
    """)

    print("✅ Đã tạo/kiểm tra xong bảng discord_channels và discord_roles!")

except Exception as e:
    print(f"❌ Lỗi khi chạy migration: {e}")
finally:
    if 'conn' in locals() and conn:
        cursor.close()
        conn.close()
