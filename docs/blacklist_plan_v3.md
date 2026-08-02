# Thiết kế: Hệ thống Global Blacklist (Danh sách đen liên minh) V3

## 1. Trả lời vụ Web Dashboard "0 Đồng"

**Hỏi:** Làm web quy mô xịn xò như vậy thì có tốn phí duy trì server hàng tháng không? Có thể chạy dự án 100% 0 đồng không?
**Đáp:** **Hoàn toàn 100% 0 ĐỒNG được!** Thế giới công nghệ bây giờ hỗ trợ lập trình viên cực kỳ mạnh tay bằng các gói Free Tier (Miễn phí trọn đời). Cấu trúc "0 đồng" cho siêu dự án của bro sẽ như sau:
1. **Bot Discord (Đang chạy):** Chạy trên **Render.com** (Gói Free).
2. **Website chính (Nơi tải bot, tra blacklist, custom tính năng):** Sẽ viết bằng React/Next.js và đẩy lên **Vercel.com**. Thằng Vercel này miễn phí trọn đời cho dự án phi thương mại, tốc độ load siêu bàn thờ, tặng luôn cái tên miền `bot-albion-tnc.vercel.app` siêu đẹp.
3. **Database (Kho chứa dữ liệu toàn cầu):** Dùng **Supabase** hoặc **Neon.tech**. Đây là 2 hệ thống cơ sở dữ liệu PostgreSQL đỉnh nhất hiện nay, cho phép lưu trữ hàng triệu dòng Blacklist miễn phí mà không tốn 1 xu.

👉 **Tóm lại:** Bro chỉ cần tốn đúng "chất xám" để lên ý tưởng, còn tiền server, tiền host, tiền domain... tất cả đều có thể xài hàng Free xịn xò 100%.

---

## 2. Các lệnh Discord (Tích hợp ngay bây giờ)

Trong lúc chờ dự án Web thành hình (đó là chặng đường dài), ta vẫn xây móng vững chắc bằng các lệnh Discord:
- `/blacklist add [discord_user] [ingame_name] [lý do]`
- `/blacklist remove [discord_user hoặc ingame_name]`
- `/blacklist check [ingame_name hoặc discord_id]`
- `/blacklist view`: In ra danh sách dạng phân trang (sang trang để xem không bị trôi chat).

## 3. Cơ chế duyệt đơn (Cập nhật: Xác nhận 2 Lớp)

Theo đúng ý bro, tui đã sửa lại kịch bản khi có Kẻ Cấp Báo (Blacklisted) nộp đơn:
1. Bot vẫn in ra cái Bảng Đỏ cảnh báo to oạch 🚨.
2. Bot **VẪN GIỮ LẠI nút "Duyệt Đơn"** (bên cạnh nút Từ chối).
3. Tuy nhiên, nếu Officer cố tình (hoặc bấm nhầm) vào nút "Duyệt Đơn" đó, bot **KHÔNG duyệt ngay** mà sẽ tung ra một Cảnh báo bật lên (hoặc popup/nút xác nhận phụ):
   *"⚠️ ID này hiện đang nằm trong blacklist của hệ thống, bạn có thật sự muốn duyệt đơn này?"*
4. Chỉ khi Officer ấn **"Vẫn Duyệt"** ở bước xác nhận thứ 2 này, thì đối tượng rủi ro đó mới được vào guild. Cơ chế này giúp đảm bảo sự linh hoạt tuyệt đối cho Officer mà không sợ "lỡ tay".

---
> [!IMPORTANT]
> **Xác nhận (User Review Required)**
> Tui đã đưa cơ chế bảo mật 2 lớp vào nút Duyệt Đơn và vạch sẵn bản đồ "0 Đồng" cho cái Website rồi. 
> Lần này nếu bro đã mãn nguyện, hãy gõ **"Chốt thiết kế, code đi"**, tui sẽ biến bản kế hoạch này thành sự thật!
