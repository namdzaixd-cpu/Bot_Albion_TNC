import os
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("DISCORD_TOKEN", "")
GIT_URL = os.getenv("GITHUB_GIT_URL", "")
# Guild mặc định (fallback khi thiếu env). Đổi tại .env DISCORD_GUILD_ID.
DEFAULT_GUILD_ID = "712258265769050164"
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", DEFAULT_GUILD_ID))
GUILD_NAME = os.getenv("GUILD_NAME", "The Northern Constellations")
GUILD_TAG = os.getenv("GUILD_TAG", "TNC")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
# Backend (bot) ưu tiên SERVICE ROLE KEY để bypass RLS và ghi config an toàn.
# Fallback các tên biến khác (anon / NEXT_PUBLIC_*) để bot chạy được dù Render set tên nào.
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    or ""
)

# Thư mục bot/ — dùng cho file config/template và file tạm
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Thư mục bot/Storage/ — nơi chứa toàn bộ file dữ liệu JSON
STORAGE_DIR = os.path.join(DATA_DIR, "Storage")

BOT_SESSION_ID = random.randint(1000, 9999)
