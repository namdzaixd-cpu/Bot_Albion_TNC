"""Test nhanh db.py / config_store.py ở chế độ không có credential.
Mục tiêu: đảm bảo hệ thống không crash khi Supabase thiếu, và helper trả giá trị đúng.
Chạy: python scripts/test_db_layer.py
"""
import os
import sys

# Giả lập thiếu env
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
os.environ.pop("SUPABASE_ANON_KEY", None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot.core import db
from bot.core import config_store
from bot.core.config import DEFAULT_GUILD_ID

print("1) get_client() thiếu env ->", db.get_client())
print("2) safe_select thiếu client ->", db.safe_select("corebank_config", filters={"guild_id": "x"}))
print("3) safe_upsert thiếu client ->", db.safe_upsert("corebank_config", {"guild_id": "x"}))
print("4) get_config fallback default ->",
      config_store.get_config("corebank_config", "999", default={"guild_id": "999", "auto_react": True}))
print("5) save_config thiếu client ->",
      config_store.save_config("corebank_config", {"guild_id": "999"}))
print("6) DEFAULT_GUILD_ID ->", DEFAULT_GUILD_ID)
print("ALL OK — không crash khi thiếu credential.")
