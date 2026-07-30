# CLAUDE.md

Xem [README.md](README.md) để biết tổng quan dự án, stack và cấu trúc code.

> Lưu ý: `instruction.md` ở root là custom instructions cho **Claude.ai chat/Projects** (workflow
> upload file, paste code vào Replit Shell) — không áp dụng cho Claude Code. File này (`CLAUDE.md`)
> mới là instructions cho Claude Code.

## Quy trình làm việc — QUAN TRỌNG NHẤT

Khi user đề xuất tính năng mới hoặc sửa đổi code: **bàn thiết kế trước** (mô tả lệnh, logic, ảnh
hưởng gì, file nào bị đụng) — KHÔNG viết/sửa code ngay.

Chỉ viết/sửa code khi user gõ RÕ RÀNG một trong các từ xác nhận: **"chốt", "ok làm đi", "làm đi",
"chốt code đi"**.

Các hành động sau KHÔNG tính là xác nhận: trả lời câu hỏi phụ, gửi ảnh/screenshot, cung cấp thêm
thông tin, hỏi ngược lại.

Nếu không chắc user đã chốt hay chưa, hỏi lại "Chốt chưa?" và chờ — tuyệt đối không tự ý code.

Ngoại lệ: các yêu cầu chỉ-đọc (đọc code, giải thích, đánh giá, tìm bug mà không sửa) không cần qua
gate này — chỉ áp dụng cho việc *viết/sửa* code.

## Về code

- Code ngắn gọn, đủ tính năng, không dài dòng thừa.
- Luôn check syntax (`python -m py_compile ...`) trước khi báo hoàn thành một thay đổi Python.
- Sau khi thêm tính năng mới hoặc fix bug trong `bot/`: cập nhật lại danh sách lệnh (bảng tính
  năng) trong README.md nếu danh sách slash/prefix command thay đổi.
- Cấu trúc bot: `bot/main.py` (entry point) + `bot/core/` (hạ tầng dùng chung: config, storage,
  permissions, webserver) + `bot/cogs/` (mỗi hệ thống tính năng — siphoned, massing, lastseen,
  guildcheck, alo_tts, corebank — là 1 cog riêng). Sửa 1 tính năng thì chỉ đụng cog tương ứng.

## Ngôn ngữ & xưng hô

Giao tiếp bằng tiếng Việt, xưng tui/bro.
