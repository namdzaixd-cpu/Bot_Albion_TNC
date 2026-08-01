

# LUẬT CẬP NHẬT TÍNH NĂNG
Mỗi khi lập trình thêm tính năng hoặc lệnh mới cho Bot, BẮT BUỘC phải cập nhật danh sách FEATURE_FIELDS trong file bot/cogs/about.py để bảng giới thiệu luôn được đồng bộ.

# LUẬT BẢO VỄ DỮ LIỆU (STORAGE) — QUAN TRỌNG NHẤT

`bot/Storage/` chứa dữ liệu thật của người dùng. Mất là mất vĩnh viễn, không khôi phục được.

**TUYỆT ĐỐI NGHIÊM CẤM:**
- Xóa, ghi đè, sửa trực tiếp bất kỳ file nào trong `bot/Storage/` — kể cả khi debug, test hay refactor.
- Dùng `open()` để đọc/ghi file trong thư mục này — chỉ dùng `load_json()` / `save_json()` từ `bot/core/storage.py`.
- Đặt file tạm, test, log vào `bot/Storage/`.

**KHI CẦN THÊM FILE DỮ LIỆU MỚI:**
1. Đặt file vào `bot/Storage/` với tên dạng: `tnc_<tính_năng>_v<version>.json`
2. Import `STORAGE_DIR` từ `bot/core/config.py`
3. Thêm đường dẫn vào `GITHUB_SYNCED_FILES` trong `bot/core/storage.py`
4. Đọc `bot/Storage/README.md` để biết danh sách file hiện có trước khi tạo mới
