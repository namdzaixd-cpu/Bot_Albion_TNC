import json
import os
import shutil
import subprocess
from threading import Lock, Thread

from .config import BOT_SESSION_ID, GIT_URL

# ==============================================================================
# CƠ CHẾ CHỐNG MẤT DỮ LIỆU - TỰ ĐỘNG ĐẨY NGƯỢC LÊN GITHUB
# ==============================================================================
_file_lock = Lock()  # Lock dùng cho đọc/ghi file JSON (chống race condition)
_git_lock = Lock()   # Lock dùng cho GitHub sync

# Các file được đồng bộ lên GitHub mỗi khi có thay đổi (xem save_json(sync_github=True))
GITHUB_SYNCED_FILES = [
    "bot/Storage/tnc_sp_v32.json",
    "bot/Storage/tnc_lastseen_v1.json",
    "bot/Storage/tnc_massing_v1.json",
    "bot/Storage/tnc_register_v1.json",
    "bot/Storage/tnc_guildcheck_v1.json",
    "bot/Storage/tnc_unresolved_v1.json",
    "bot/Storage/tnc_tts_config_v1.json",
    "bot/Storage/tnc_templates_v1.json",
    "bot/Storage/tnc_ai_config.json",
    "bot/Storage/tnc_coreconfig_v1.json",
    "bot/Storage/tnc_core_credited_v1.json",
    "bot/Storage/tnc_library_v1.json",
]


def sync_to_github():
    with _git_lock:
        try:
            subprocess.run(["git", "config", "user.name", "TNC_Data_Guard"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "guard@tnc-guild.com"], check=True, capture_output=True)
            existing_files = [f for f in GITHUB_SYNCED_FILES if os.path.exists(f)]
            if not existing_files:
                print("📊 [Data-Guard] Không có file dữ liệu nào để sao lưu.")
                return
            subprocess.run(["git", "add", *existing_files], check=True, capture_output=True)
            commit_res = subprocess.run(
                ["git", "commit", "-m", f"🤖 [Auto-Save] Session {BOT_SESSION_ID}"],
                capture_output=True, text=True,
            )
            if "nothing to commit" not in commit_res.stdout:
                # Luôn pull --rebase trước khi push để tránh lỗi conflict nếu có người vừa push code
                subprocess.run(["git", "pull", "--rebase", GIT_URL, "main"], check=False, capture_output=True)
                subprocess.run(["git", "push", GIT_URL, "main"], check=True, capture_output=True)
                print("📊 [Data-Guard] Đồng bộ GitHub thành công!")
            else:
                print("📊 [Data-Guard] Không có thay đổi dữ liệu cần sao lưu.")
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"❌ [Data-Guard] Lỗi Auto-Sync (Git Error): {err_msg}")
        except Exception as e:
            print(f"❌ [Data-Guard] Lỗi Auto-Sync: {e}")


def restore_from_github():
    """Kéo file dữ liệu JSON từ GitHub về máy sau khi Render deploy container mới.
    Chỉ checkout đúng các file trong GITHUB_SYNCED_FILES, không merge/rebase code.
    Đảm bảo Storage luôn có data mới nhất dù filesystem ephemeral."""
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True)
        for filepath in GITHUB_SYNCED_FILES:
            subprocess.run(
                ["git", "checkout", "origin/main", "--", filepath],
                check=False, capture_output=True
            )
        print("📥 [Data-Guard] Đã khôi phục dữ liệu từ GitHub thành công!")
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        print(f"⚠️ [Data-Guard] Không thể khôi phục từ GitHub: {err_msg} — dùng data local nếu có.")
    except Exception as e:
        print(f"⚠️ [Data-Guard] Lỗi restore: {e}")


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
