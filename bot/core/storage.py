import os
from .config import BOT_SESSION_ID, GIT_URL
from .database import supabase, run_blocking

# ==============================================================================
# CƠ CHẾ CHỐNG MẤT DỮ LIỆU - TỰ ĐỘNG ĐẨY LÊN SUPABASE
# ==============================================================================

def sync_to_github():
    pass

def restore_from_github():
    pass

def load_json(path, default):
    """Đọc dữ liệu từ bảng json_storage trên Supabase, dùng tên file làm khóa."""
    filename = os.path.basename(path)
    try:
        resp = supabase.table("json_storage").select("data").eq("file_name", filename).execute()
        if resp.data:
            return resp.data[0]["data"]
    except Exception as e:
        print(f"⚠️ [Data] Lỗi đọc {filename} từ Supabase: {e}")
    
    # Nếu chưa có trên Supabase, khởi tạo giá trị mặc định
    return default() if callable(default) else default

def save_json(data, path, sync_github=True):
    """Lưu dữ liệu vào bảng json_storage trên Supabase (BLOCKING — chỉ dùng ngoài event loop)."""
    filename = os.path.basename(path)
    try:
        supabase.table("json_storage").upsert(
            {"file_name": filename, "data": data},
            on_conflict="file_name"
        ).execute()
        print(f"✅ [Data] Đã lưu {filename} lên Supabase.")
    except Exception as e:
        print(f"❌ [Data] Lỗi lưu {filename} lên Supabase: {e}")

async def save_json_async(data, path, sync_github=True):
    """Lưu dữ liệu vào Supabase NHƯNG chạy trong thread pool — dùng trong command/callback."""
    filename = os.path.basename(path)
    try:
        await run_blocking(lambda: supabase.table("json_storage").upsert(
            {"file_name": filename, "data": data},
            on_conflict="file_name"
        ).execute())
        print(f"✅ [Data] Đã lưu {filename} lên Supabase (async).")
    except Exception as e:
        print(f"❌ [Data] Lỗi lưu {filename} lên Supabase: {e}")

def _trigger_sync():
    pass


