Đây là project Bot_Albion_TNC — bot Discord quản lý guild TNC trong game Albion Online.

Stack kỹ thuật
Ngôn ngữ: Python (discord.py 2.x)
Code trên: Replit (thư mục bot/)
Deploy: Render (web service, chạy python bot/main.py)
Lưu data: File JSON tự động sync lên GitHub sau mỗi thay đổi
GitHub repo: namdzaixd-cpu/Bot_Albion_TNC

Cấu trúc code (đã refactor từ 1 file main.py duy nhất sang cấu trúc Cog):
bot/main.py       — entry point: tạo bot, load các cog, chạy keep_alive + bot.run
bot/core/         — hạ tầng dùng chung: config.py (env/const), storage.py (đọc/ghi JSON + sync GitHub),
                    permissions.py (is_officer), webserver.py (Flask keep-alive)
bot/cogs/         — mỗi hệ thống tính năng 1 file cog: siphoned.py, massing.py, lastseen.py,
                    guildcheck.py, alo_tts.py, corebank.py
Khi sửa 1 tính năng, chỉ cần đụng vào cog tương ứng (và core/ nếu đổi hạ tầng dùng chung),
không phải sửa nguyên khối main.py như trước nữa.

Quy trình làm việc — QUAN TRỌNG NHẤT
Khi tui đề xuất tính năng mới hoặc sửa đổi: Claude PHẢI bàn thiết kế trước (mô tả lệnh, logic, ảnh hưởng gì) — KHÔNG được viết/sửa code ngay.
Claude chỉ được viết/sửa code khi tui gõ RÕ RÀNG 1 trong các từ xác nhận: "chốt", "ok làm đi", "làm đi", "chốt code đi".
Các hành động sau KHÔNG tính là xác nhận: trả lời câu hỏi phụ, gửi ảnh/screenshot, cung cấp thêm thông tin, hỏi ngược lại.
Nếu không chắc tui đã chốt hay chưa, Claude phải hỏi lại "Bro chốt chưa?" và chờ, tuyệt đối không tự ý code.
Sau khi tui chốt, Claude mới được tạo/sửa code.

Về code
Luôn dùng (các) file mới nhất tui upload trong Files làm gốc — file nào liên quan tới thay đổi thì dùng bản đó
(vd: sửa Massing thì dùng bot/cogs/massing.py mới nhất, không dùng bản cũ trong bộ nhớ).
Code ngắn gọn, đủ tính năng, không dài dòng thừa.
Luôn check syntax (python3 -m py_compile) trước khi đưa ra.
Sau khi có tính năng mới hoặc fix bug: tự động cập nhật lại danh sách lệnh (glossary) gửi kèm.

Về cách đưa code
Sửa nhỏ (1 đoạn, không đổi cấu trúc): đưa dạng shell script python3 - << 'EOF' ... EOF để tui paste thẳng vào Replit Shell.
Thay đổi lớn (thêm tính năng, refactor, xóa/thêm cả section): xuất đầy đủ (các) file cog/core bị ảnh hưởng qua file presenter, không dùng heredoc (paste dài dễ bị cắt trong Replit Shell).
Sau MỌI thay đổi code, luôn kèm 3 dòng lệnh (thay đúng đường dẫn file đã sửa):
git add bot/cogs/<file>.py
git commit -m "mô tả thay đổi"
git push origin main
Sau thay đổi lớn: nhắc tui upload lại (các) file đã đổi vào Files để lần sau Claude dùng đúng bản mới nhất.

Ngôn ngữ & xưng hô
Giao tiếp hoàn toàn bằng tiếng Việt, xưng tui/bro.