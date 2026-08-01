# 📦 bot/Storage — Kho Dữ Liệu Bot TNC

Thư mục này chứa **toàn bộ dữ liệu vận hành thật** của Bot Albion TNC.
Mọi thay đổi trong thư mục này đều được **tự động đồng bộ lên GitHub** qua cơ chế `GITHUB_SYNCED_FILES` trong `bot/core/storage.py`.

---

## ⛔ NGHIÊM CẤM (dành cho AI Agent & Developer)

> **Dữ liệu ở đây là thật. Mất là mất vĩnh viễn, không thể khôi phục.**

- **KHÔNG** xóa, ghi đè hay sửa thẳng file JSON ở đây — kể cả khi đang debug hoặc test.
- **KHÔNG** dùng `open()` thuần để đọc/ghi — phải dùng `load_json()` / `save_json()` từ `bot/core/storage.py` (có cơ chế backup `.bak` + atomic write).
- **KHÔNG** đặt file tạm, file test, file log vào đây — chúng sẽ bị đẩy lên GitHub và làm ô nhiễm data repo.

---

## ✅ Quy tắc khi thêm file dữ liệu mới

1. **Đặt file vào thư mục này** với tên theo pattern:
   ```
   tnc_<tính_năng>_v<số_version>.json
   ```
   Ví dụ đúng: `tnc_massing_v1.json`, `tnc_register_v1.json`
   Ví dụ sai: `data.json`, `config_temp.json`, `test_xyz.json`

2. **Import `STORAGE_DIR`** từ `bot/core/config.py` trong cog tương ứng:
   ```python
   from core.config import STORAGE_DIR
   MY_FILE = os.path.join(STORAGE_DIR, "tnc_myfeature_v1.json")
   ```

3. **Thêm đường dẫn** vào `GITHUB_SYNCED_FILES` trong `bot/core/storage.py`:
   ```python
   "bot/Storage/tnc_myfeature_v1.json",
   ```

4. **Bump version** (`_v1` → `_v2`) khi cấu trúc JSON thay đổi không tương thích ngược, để tránh bot crash khi đọc data cũ.

---

## 📋 Danh sách file hiện có

| File | Mô tả | Cog sở hữu | Sync GitHub |
|------|--------|------------|-------------|
| `tnc_massing_v1.json` | Dữ liệu các party Massing đang active | `cogs/massing.py` | ✅ |
| `tnc_templates_v1.json` | Template Massing do Officer lưu (ZvZ, PVP...) | `cogs/massing.py` | ✅ |
| `tnc_sp_v32.json` | Lịch sử điểm Siphoned của thành viên | `cogs/siphoned.py` | ✅ |
| `tnc_lastseen_v1.json` | Thời điểm online cuối cùng của thành viên | `cogs/lastseen.py` | ✅ |
| `tnc_register_v1.json` | Đăng ký IGN ↔ Discord ID | `cogs/guildcheck.py` | ✅ |
| `tnc_guildcheck_v1.json` | Cấu hình GuildCheck (role, channel, guild Albion) | `cogs/guildcheck.py` | ✅ |
| `tnc_unresolved_v1.json` | Thành viên chưa xác minh IGN | `cogs/guildcheck.py` | ✅ |
| `tnc_coreconfig_v1.json` | Cấu hình Core-Bank (channel, token UB) | `cogs/corebank.py` | ✅ |
| `tnc_core_credited_v1.json` | Lịch sử cấp Core cho thành viên | `cogs/corebank.py` | ✅ |
| `tnc_tts_config_v1.json` | Cấu hình ALO TTS (channel, ngôn ngữ) | `cogs/alo_tts.py` | ✅ |
| `tnc_ai_config.json` | Cấu hình AI Chat (model, channel, whitelist) | `cogs/chat_ai.py` | ✅ |

> File `.bak` (vd: `tnc_lastseen_v1.json.bak`) là bản backup tự động — **đừng xóa**, bot dùng để khôi phục nếu file chính bị lỗi.

---

## 🔧 Cơ chế bảo vệ dữ liệu

Bot dùng cơ chế **atomic write** để đảm bảo không mất dữ liệu khi bot crash giữa chừng:
1. Ghi data ra file `.tmp`
2. Copy file hiện tại thành `.bak`
3. Rename `.tmp` → file chính (atomic `os.replace`)

Toàn bộ logic này nằm trong `bot/core/storage.py`.
