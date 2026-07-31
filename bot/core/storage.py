import json
import os
import shutil
import subprocess
import time
from threading import Lock, Thread

from .config import BOT_SESSION_ID, GIT_URL

# ==============================================================================
# CƠ CHẾ CHỐNG MẤT DỮ LIỆU - TỰ ĐỘNG ĐẨY NGƯỢC LÊN GITHUB
# ==============================================================================
_file_lock = Lock()  # Lock dùng cho đọc/ghi file JSON (chống race condition)
_git_lock = Lock()   # Lock dùng cho GitHub sync

# Các file được đồng bộ lên GitHub mỗi khi có thay đổi (xem save_json(sync_github=True))
GITHUB_SYNCED_FILES = [
    "bot/tnc_sp_v32.json",
    "bot/tnc_lastseen_v1.json",
    "bot/tnc_massing_v1.json",
    "bot/tnc_tts_config_v1.json",
    "bot/tnc_templates_v1.json",
]


def pull_data_from_github():
    """Pull các file data về từ GitHub khi bot khởi động (tránh mất data sau redeploy)."""
    with _git_lock:
        try:
            subprocess.run(["git", "config", "user.name", "TNC_Data_Guard"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "guard@tnc-guild.com"], check=True, capture_output=True)
            # Chỉ fetch, không merge toàn bộ — sau đó checkout từng file data
            subprocess.run(["git", "fetch", GIT_URL, "main:refs/remotes/data_pull/main"],
                           check=True, capture_output=True)
            for rel_path in GITHUB_SYNCED_FILES:
                res = subprocess.run(
                    ["git", "show", f"refs/remotes/data_pull/main:{rel_path}"],
                    capture_output=True, text=True, encoding="utf-8"
                )
                if res.returncode == 0 and res.stdout.strip():
                    abs_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        *rel_path.split("/")[1:]  # bỏ prefix "bot/"
                    )
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    # Chỉ ghi nếu file chưa tồn tại hoặc file trống
                    if not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
                        with open(abs_path, "w", encoding="utf-8") as f:
                            f.write(res.stdout)
                        print(f"✅ [Data-Guard] Đã khôi phục {rel_path} từ GitHub.")
            print("✅ [Data-Guard] Hoàn tất pull data từ GitHub.")
        except Exception as e:
            print(f"⚠️ [Data-Guard] Không pull được data từ GitHub: {e}")


def sync_to_github():
    with _git_lock:
        try:
            subprocess.run(["git", "config", "user.name", "TNC_Data_Guard"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "guard@tnc-guild.com"], check=True, capture_output=True)
            subprocess.run(["git", "add", *GITHUB_SYNCED_FILES], check=True, capture_output=True)
            commit_res = subprocess.run(
                ["git", "commit", "-m", f"🤖 [Auto-Save] Session {BOT_SESSION_ID}"],
                capture_output=True, text=True,
            )
            if "nothing to commit" not in commit_res.stdout:
                subprocess.run(["git", "push", GIT_URL, "main"], check=True, capture_output=True)
                print("📊 [Data-Guard] Đồng bộ GitHub thành công!")
            else:
                print("📊 [Data-Guard] Không có thay đổi dữ liệu cần sao lưu.")
        except Exception as e:
            print(f"❌ [Data-Guard] Lỗi Auto-Sync: {e}")


def load_json(path, default):
    """Đọc file JSON, tự fallback sang bản `.bak` nếu file chính thiếu hoặc lỗi."""
    for try_path in (path, path + ".bak"):
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {path}")
    return default() if callable(default) else default


def save_json(data, path, sync_github=True):
    """Ghi JSON an toàn (tmp -> backup -> replace), tùy chọn tự đẩy lên GitHub."""
    with _file_lock:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(path):
            shutil.copy2(path, path + ".bak")
        os.replace(tmp_path, path)
    if sync_github:
        Thread(target=sync_to_github).start()
