"""Test kết nối Supabase mô phỏng bot init (không chạy bot)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
from core.config import SUPABASE_URL, SUPABASE_KEY, TOKEN, GUILD_ID
from core.db import get_client

print("=== ENV CHECK ===")
print(f"DISCORD_TOKEN(TOKEN): {'SET' if TOKEN else 'MISSING'}")
print(f"SUPABASE_URL: {'SET' if SUPABASE_URL else 'MISSING'}")
print(f"SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'MISSING'} (len={len(SUPABASE_KEY)})")
print(f"GUILD_ID: {GUILD_ID}")

print("\n=== CLIENT INIT ===")
client = get_client()
if client is None:
    print("❌ Client None -> bot sẽ không query được DB")
    sys.exit(1)
print("✅ Client created OK")

print("\n=== TEST QUERY guild_config ===")
try:
    res = client.table("guild_config").select("*").limit(1).execute()
    if res.data:
        print(f"✅ Query OK, rows={len(res.data)}, sample={res.data[0]}")
    else:
        print("⚠️ Query OK nhưng không có data")
except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

print("\n✅ BOT SẼ HOẠT ĐỘNG VỚI ENV NÀY (trên Render nếu set tương tự)")
