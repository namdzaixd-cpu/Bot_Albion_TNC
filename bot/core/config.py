import os
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("DISCORD_TOKEN", "")
GIT_URL = os.getenv("GITHUB_GIT_URL", "")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "712258265769050164"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")

# Thư mục bot/ — nơi chứa toàn bộ file dữ liệu JSON
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_SESSION_ID = random.randint(1000, 9999)
