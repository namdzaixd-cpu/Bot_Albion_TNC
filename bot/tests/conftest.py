import os
import sys

# Đảm bảo bot/ nằm trong sys.path để import được core.* / cogs.* / main
# dù pytest được chạy từ đâu.
BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

os.environ.setdefault("DISCORD_TOKEN", "dummy-token-for-ci")
os.environ.setdefault("GITHUB_GIT_URL", "")
