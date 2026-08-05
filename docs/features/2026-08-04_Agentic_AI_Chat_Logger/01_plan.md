# Kế hoạch Triển Khai Kiến Trúc Agentic AI (Version 2)

Dưới đây là bản kế hoạch đã được cập nhật dựa trên các góp ý và câu hỏi của bạn.

## Giải đáp các câu hỏi từ User
**1. Bot dùng Tool dựa trên từ khóa hay tự nhận biết ngữ cảnh?**
- **Trả lời:** Bot **TỰ NHẬN BIẾT NGỮ CẢNH**. Trí tuệ của AI hiện đại (Function Calling) không chạy bằng if-else hay tìm từ khoá cơ bản. Nó đọc hiểu toàn bộ câu chat của bạn và tự suy luận xem câu đó có cần dùng Tool hay không. (VD: "hôm qua có drama gì" hay "kể chuyện hôm qua nghe chơi" nó đều tự hiểu là cần lôi lịch sử chat).

**2. Cách bot đang sử dụng các model như thế nào? Có phải là theo thứ tự không?**
- **Trả lời:** Đúng vậy. Hiện tại trong code cũ của bạn có biến `FAILOVER_CHAIN`, bot sẽ thử theo thứ tự (từ Ollama -> Gemini -> OpenRouter). Nếu cái 1 lỗi hoặc hết rate limit, nó nhảy sang cái 2, cái 3... 
- **Tuy nhiên, với mô hình Agentic mới:** Chúng ta sẽ chia làm 2 luồng:
  - **Luồng chat bình thường:** Vẫn dùng `FAILOVER_CHAIN` như cũ để tiết kiệm.
  - **Luồng dùng Tool (như Lục lịch sử):** Mình sẽ tách ra, BẮT BUỘC chỉ gọi thẳng vào Gemini (ví dụ: `gemini-1.5-flash` vì nó có context cực lớn 1 Triệu Token và hỗ trợ Tool Calling cực tốt). Nếu API Gemini lúc đó bị lỗi, bot sẽ tự động báo *"Hiện tại hệ thống AI đang bảo trì, không thể tóm tắt dữ liệu"* chứ tuyệt đối KHÔNG tự ý nhảy sang các model OpenRouter khác để tránh đốt Token vô nghĩa như bạn yêu cầu.

**3. Lưu trữ tất cả tin nhắn/thread trong 2 ngày thì có tốn dung lượng không?**
- **Trả lời:** **KHÔNG HỀ.** Một Server Discord đông người chat liên tục trong 2 ngày thì nhiều nhất cũng chỉ khoảng 5.000 - 10.000 tin nhắn. 10.000 tin nhắn text lưu trữ trên Supabase chỉ tốn chưa tới **5 MB** (trong khi gói Free của bạn là 500 MB). Nghĩa là bạn lưu 2 ngày thì xài cả trăm năm nữa Supabase cũng chưa đầy. Thậm chí bạn lưu 7 ngày cũng hoàn toàn bình thường.

---

## 1. Thu thập dữ liệu ngầm (Data Pipeline - Phase 1)
- Tạo lại bảng `chat_history` trên Supabase: `id`, `user_id`, `author_name`, `channel_id`, `content`, `created_at`.
- Tính năng ghi log: Ghi lại MỌI tin nhắn ở tất cả các kênh và tất cả các thread.
- Dọn dẹp tự động: Viết 1 task ngầm trong Bot Python, cứ 0h sáng sẽ tự động xóa các tin nhắn cũ hơn 2 ngày (hoặc 7 ngày tuỳ bạn chỉnh). **Không tốn 1 đồng chi phí.**

## 2. Hệ thống Công cụ (Tool Calling) cho AI (Phase 2 & 3)
Chúng ta sẽ trang bị các Tools sau cho Bot:

#### Tool 1: `read_chat_history(thoi_gian, channel_id, keyword)`
- **Bảo vệ Token:** Chỉ dùng model có Context lớn (Gemini 1.5/2.5 Flash). Nếu Gemini lỗi, bot báo bận, không xài model khác.
- AI sẽ tự động phân tích câu hỏi của user để điền tham số `thoi_gian` (VD: 12h, 24h, 48h) và gửi lệnh chui vào Supabase lấy data.

#### Tool 2: `get_massing_stats(timeframe)` (Chốt)
- AI tự lôi data số liệu báo cáo từ DB để trả lời các câu hỏi về content. Rất nhẹ, không tốn Token.

#### Tool 3: `search_albion_database(item_name)` (Chốt làm sau)
- Tính năng RAG tìm kiếm đồ Albion trên DB vector Supabase. Nhẹ và chính xác.

## User Review Required
Bạn hãy xem lại các giải đáp và cam kết bảo vệ Token ở trên. Nếu mọi thứ đã thoả mãn yêu cầu của bạn, chúng ta sẽ **triển khai lại Phase 1 (Ghi log data ngầm)** ngay lập tức để có dữ liệu cho Bot thực hành nhé! Chốt chứ?
