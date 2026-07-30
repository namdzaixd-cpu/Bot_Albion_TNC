from threading import Thread

from flask import Flask

from .config import BOT_SESSION_ID

# ==============================================================================
# WEB SERVER FLASK (TREO BOT ONLINE TRÊN RENDER)
# ==============================================================================
app = Flask("")


@app.route("/")
def home():
    return f"🛡️ TNC Manager v40 [Siphoned + Massing + GuildCheck] Live! ID: {BOT_SESSION_ID}"


def _run():
    app.run(host="0.0.0.0", port=5000)


def keep_alive():
    Thread(target=_run).start()
