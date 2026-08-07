import asyncio
import functools
import os
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

# Initialize Supabase client globally.
# Backend bot dùng service_role key (bypass RLS) — bảng json_storage chỉ có
# policy cho service_role. Anon key chỉ là fallback khi thiếu service_role.
# Wrap in try-except to avoid crashing on CI environments where .env is missing.
try:
    if not SUPABASE_URL:
        print("⚠️ [Supabase] Thiếu SUPABASE_URL — chưa kết nối được.")
        supabase = None
    elif not SUPABASE_KEY:
        print("⚠️ [Supabase] Thiếu SUPABASE_SERVICE_ROLE_KEY và SUPABASE_ANON_KEY — chưa kết nối được.")
        supabase = None
    else:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        role = "service_role" if SUPABASE_SERVICE_ROLE_KEY else "anon"
        print(f"✅ [Supabase] Đã kết nối thành công (role: {role}).")
except Exception as e:
    print(f"❌ [Supabase] Không thể khởi tạo client: {e}")
    supabase = None

def get_supabase():
    return supabase


async def run_blocking(fn, *args):
    """Chạy 1 hàm BLOCKING (vd: supabase .execute()) trong thread pool
    để KHÔNG nghẽn event loop của discord.py.

    Dùng: await run_blocking(lambda: supabase.table(...).execute())
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args) if args else fn)
