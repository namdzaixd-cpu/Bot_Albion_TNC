import os
import random

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

TOKEN = os.getenv("DISCORD_TOKEN", "")
GIT_URL = os.getenv("GITHUB_GIT_URL", "")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "712258265769050164"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Thư mục bot/ — nơi chứa toàn bộ file dữ liệu JSON
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_SESSION_ID = random.randint(1000, 9999)
