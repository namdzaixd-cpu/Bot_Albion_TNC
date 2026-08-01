

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

# LUẬT KHỞI ĐỘNG BOT (TRÁNH PHÂN THÂN)
Tuyệt đối không được tuỳ tiện chạy lệnh `python bot/main.py` dưới nền (background tasks) liên tục.
**TRƯỚC KHI KHỞI ĐỘNG BOT ĐỂ TEST:**
1. Phải chạy lệnh liệt kê các tiến trình đang chạy (dùng tool `manage_task` action `list`).
2. Nếu phát hiện có tiến trình bot nào đang chạy dưới nền, BẮT BUỘC phải `kill` nó trước.
3. Đảm bảo chỉ có duy nhất 1 luồng bot hoạt động tại mọi thời điểm để tránh spam Discord và xung đột ghi file / tự động commit.

# LUẬT COMMIT CODE TỰ ĐỘNG BẰNG PYTHON (GIT AUTHOR)
Tuyệt đối KHÔNG dùng các lệnh như `git config user.name ...` hoặc `git config user.email ...` trong code để đổi tên người commit. 
Việc này sẽ làm hỏng cấu hình Git cục bộ (local git config) của User.
Thay vào đó, chỉ được phép ghi đè thông tin tác giả trực tiếp trên từng commit bằng cờ `--author`, ví dụ:
`git commit --author="TNC_Data_Guard <guard@tnc-guild.com>" -m "..."`

# LUẬT VIẾT COMMIT MESSAGE (100% TIẾNG VIỆT)
Tất cả các mô tả commit (commit messages) do Bot tự động tạo ra hoặc do AI thực hiện (bằng lệnh `git commit`) BẮT BUỘC phải viết 100% bằng Tiếng Việt. 
Ví dụ: `thêm_tính_năng(ai): bổ sung đếm số lượng request` thay vì `feat(ai): add request count`.
