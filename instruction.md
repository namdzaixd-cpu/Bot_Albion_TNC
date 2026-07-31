Đây là project Bot_Albion_TNC — bot Discord quản lý guild TNC trong game Albion Online.

Stack kỹ thuật
Ngôn ngữ: Python (discord.py 2.x)
Code trên: Local IDE (khuyên dùng với AI Agent) hoặc Replit (thư mục bot/)
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
Khi tui đề xuất tính năng mới hoặc sửa đổi: AI Agent / Claude PHẢI bàn thiết kế trước (mô tả lệnh, logic, ảnh hưởng gì) — KHÔNG được tự ý viết/sửa code ngay.
AI Agent / Claude chỉ được viết/sửa code trên file khi tui gõ RÕ RÀNG 1 trong các từ xác nhận: "chốt", "ok làm đi", "làm đi", "chốt code đi".
Các hành động sau KHÔNG tính là xác nhận: trả lời câu hỏi phụ, gửi ảnh/screenshot, cung cấp thêm thông tin, hỏi ngược lại.
Nếu không chắc tui đã chốt hay chưa, trợ lý AI phải hỏi lại "Bro chốt chưa?" và chờ, tuyệt đối không tự ý code.
Sau khi tui chốt, AI mới được tạo/sửa code.

Về code
- Nếu dùng qua AI Agent trên IDE: Tự động đọc trực tiếp cấu trúc file hiện tại trên máy để làm gốc.
- Nếu dùng qua Claude web: Luôn dùng (các) file mới nhất tui upload trong Files làm gốc.
Code ngắn gọn, đủ tính năng, không dài dòng thừa.
Luôn check syntax kỹ càng (có thể dùng lệnh `python3 -m py_compile`) trước khi áp dụng.
Sau khi có tính năng mới hoặc fix bug: tự động cập nhật lại danh sách lệnh (glossary) gửi kèm.

Về cách đưa/sửa code
- Đối với AI Agent (trên IDE): Tự động sửa thẳng vào các file trong workspace. Sau khi sửa xong, tự động chạy lệnh git để commit và push lên nhánh main.
- Đối với Claude web (hoặc Replit): Xuất đầy đủ code của các file bị ảnh hưởng để tui tự paste. Nhắc tui chạy các lệnh git push và upload lại file mới để đồng bộ.
- Chuẩn lệnh Git sau MỌI thay đổi code (thay đúng đường dẫn file đã sửa):
  git add bot/cogs/<file>.py
  git commit -m "mô tả thay đổi"
  git push origin main

Ngôn ngữ & xưng hô
Giao tiếp hoàn toàn bằng tiếng Việt, xưng tui/bro.