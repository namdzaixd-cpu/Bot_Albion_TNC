import os
from threading import Thread

from flask import Flask, jsonify
from flask_cors import CORS

from .config import BOT_SESSION_ID, STORAGE_DIR
from .storage import load_json

# ==============================================================================
# WEB SERVER FLASK (TREO BOT ONLINE TRÊN RENDER)
# ==============================================================================
app = Flask("")
CORS(app)  # Enable CORS cho tất cả các route để Web có thể lấy API

@app.route("/api/blacklist")
def api_blacklist():
    file_path = os.path.join(STORAGE_DIR, "global_blacklist_v1.json")
    data = load_json(file_path, dict)
    return jsonify(data.get("blacklist", []))


@app.route("/")
def home():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "templates", "index.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content.replace("{{ session_id }}", str(BOT_SESSION_ID))
    except Exception as e:
        print(f"❌ Lỗi load web template: {e}")
    
    return f"🛡️ TNC Manager v40 [Siphoned + Massing + GuildCheck] Live! ID: {BOT_SESSION_ID}"


def _run():
    app.run(host="0.0.0.0", port=5000)


def keep_alive():
    Thread(target=_run).start()
