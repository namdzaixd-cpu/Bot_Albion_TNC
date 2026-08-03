# 🗺️ Bảng Kế Hoạch Phát Triển TNC Bot — Roadmap Toàn Diện

## Tổng Quan Dự Án

Dự án TNC Bot đang chuyển mình từ một **bot nội bộ cho guild TNC** sang một **sản phẩm mã nguồn mở phục vụ cộng đồng Albion Online**. Bảng kế hoạch này phân tích 5 đề xuất của bạn, đánh giá khó khăn, đề xuất giải pháp, và sắp xếp thành các giai đoạn phát triển rõ ràng.

---

## 📋 Phân Tích Từng Đề Xuất

### Đề Xuất 1: Mô Hình Phân Phối Bot

**Bạn muốn:** Đóng gói bot → public cho cộng đồng → họ tự cài Token, API, Host riêng.

#### Hai hướng phân phối và đánh giá:

| Tiêu chí | Self-Hosted (Tải repo về) | Invite Bot (Như top.gg) |
|---|---|---|
| **Cách hoạt động** | Người dùng clone repo, tự tạo Bot Token, tự chạy trên VPS | Bạn chạy 1 con bot duy nhất, người ta mời về server |
| **Chi phí cho bạn** | Gần như 0 | Rất cao (VPS mạnh chịu tải nhiều server) |
| **Độ phức tạp cho người dùng** | Cao (cần biết chạy Python, VPS) | Rất thấp (chỉ cần click mời) |
| **Kiểm soát dữ liệu** | Mỗi người giữ data riêng | Bạn giữ toàn bộ data |
| **Bảo trì & Update** | Người dùng tự git pull | Bạn update 1 lần, ai cũng được |
| **Phù hợp với yêu cầu "Token & API tự cài"** | ✅ Hoàn hảo | ❌ Mâu thuẫn |

> [!IMPORTANT]
> **Đề xuất:** Dựa trên định hướng của bạn ("Token và API phải là của người đó tự cài"), mô hình **Self-Hosted** là lựa chọn duy nhất hợp lý. Mô hình Invite Bot yêu cầu bạn phải chạy infrastructure riêng, chi phí cao, và đi ngược lại triết lý "mỗi người tự quản lý bot của mình".

#### Khó khăn sẽ gặp:
- **Rào cản kỹ thuật cho người dùng:** Không phải ai chơi Albion cũng biết cài Python, chạy VPS. Đa số là game thủ, không phải developer.
- **Bảo trì phiên bản:** Khi bạn update code mới, người dùng phải tự `git pull` và có thể gặp conflict với config cá nhân.

#### Hướng giải quyết:
1. **Viết script cài đặt tự động** (`setup.bat` cho Windows, `setup.sh` cho Linux) — chạy 1 lệnh là xong tất cả.
2. **Tách biệt hoàn toàn config và code** — File config của người dùng nằm trong `.env` hoặc thư mục riêng, không bao giờ bị conflict khi update.
3. **Viết hướng dẫn cài đặt cực kỳ chi tiết trên Website** (bạn đã bắt đầu làm rồi).
4. **Về lâu dài:** Có thể đóng gói bot thành Docker Image — người dùng chỉ cần chạy 1 lệnh `docker-compose up` là xong.

---

### Đề Xuất 2: Trang Web Đa Chức Năng

**Bạn muốn:** Website vừa giới thiệu, vừa hướng dẫn, vừa quảng cáo, vừa có forum/cộng đồng.

#### Kiến trúc đề xuất cho Website:

```
Trang Web TNC Bot
├── 🏠 Trang Chủ (Giới thiệu + Quảng cáo) ← Đã có
├── 📚 Hướng Dẫn Cài Đặt ← Đã có (vừa cập nhật)
├── 🚨 Global Blacklist (Xem + Tạo Ticket) ← Cần nâng cấp lớn
├── 🤝 Đội Ngũ Phát Triển ← Đã có
├── 💬 Forum / Cộng Đồng ← MỚI
│   ├── Góp ý tính năng
│   ├── Báo lỗi (Bug Report)
│   └── Thảo luận chung
└── 🔐 Dashboard Quản Trị (Cho Officer đã xác thực) ← MỚI
    ├── Quản lý Blacklist Ticket
    └── Thông tin server đã đăng ký
```

#### Khó khăn sẽ gặp:
- **Forum tự build rất tốn thời gian** — cần hệ thống bài viết, bình luận, thông báo, quản lý spam...
- **Xác thực Officer qua Discord OAuth2** — cần backend xử lý flow đăng nhập.
- **Hosting Website** — Website cần chạy 24/7, cần database cho forum và blacklist.

#### Hướng giải quyết:
1. **Forum:** Thay vì tự build forum từ đầu, có 2 lựa chọn:
   - **Nhanh gọn:** Tạo một Discord Server riêng cho cộng đồng bot (kênh `#góp-ý`, `#báo-lỗi`) và gắn link Discord mời vào website. Đây là cách đa số bot Discord đang làm.
   - **Chuyên nghiệp hơn:** Dùng GitHub Discussions hoặc tích hợp một widget forum đơn giản vào web.
2. **Xác thực:** Dùng **NextAuth.js** (bạn đã cài sẵn trong dự án) kết hợp với Discord OAuth2.
3. **Hosting:** Vercel (miễn phí cho Next.js) + Supabase hoặc PlanetScale (database miễn phí).

---

### Đề Xuất 3: Đăng Ký Thông Tin Khi Tải Bot

**Bạn muốn:** Khi ai đó tải bot về dùng, phải gửi thông tin (Discord ID người tải, Server ID) lên trang web của bạn.

#### Cơ chế đề xuất:

```
Người dùng clone repo
       ↓
Chạy lệnh setup (lần đầu)
       ↓
Bot hỏi: "Nhập Discord ID của bạn" + "Nhập Server ID"
       ↓
Bot gọi API lên Website TNC để đăng ký
       ↓
Website lưu vào Database:
  {
    "owner_discord_id": "123456789",
    "server_id": "987654321",
    "server_name": "TNC Guild",
    "registered_at": "2026-08-03",
    "bot_version": "1.0.0"
  }
```

#### Khó khăn sẽ gặp:
- **Người dùng có thể bypass** — vì code là mã nguồn mở, họ có thể xóa đoạn code gửi thông tin đi.
- **Quyền riêng tư** — một số người có thể không muốn chia sẻ Server ID.

#### Hướng giải quyết:

> [!WARNING]
> **Quan trọng:** Vì bot là mã nguồn mở (Self-hosted), bạn KHÔNG THỂ bắt buộc 100% người dùng phải đăng ký. Ai biết code đều có thể bỏ qua bước này. Thay vào đó, hãy tạo **động lực** để họ TỰ NGUYỆN đăng ký.

**Cơ chế khuyến khích đăng ký:**
1. **Global Blacklist chỉ hoạt động khi đăng ký** — Đây là killer feature. Nếu server không đăng ký với hệ thống trung tâm, bot của họ sẽ KHÔNG được đồng bộ danh sách Blacklist mới nhất từ cộng đồng. Muốn được bảo vệ khỏi scammer? Phải đăng ký.
2. **Bot hiển thị badge "Verified Server"** khi đã đăng ký — tạo cảm giác uy tín.
3. **Nhận thông báo update phiên bản mới** — chỉ server đã đăng ký mới được bot tự nhắc khi có bản cập nhật.

---

### Đề Xuất 4: Bật/Tắt Module + Hệ Thống Blacklist Web

**Bạn muốn:**
- Toggle module cho từng server.
- Officer dùng lệnh Discord → nhận link web → tạo ticket blacklist trên web (có bằng chứng, ảnh, mô tả).
- Chỉ Officer đã xác thực mới tạo được ticket.

#### 4A. Toggle Module

Vì là Self-hosted (1 bot = 1 server), cách làm đơn giản và hiệu quả nhất:

| Phương án | Mô tả | Đánh giá |
|---|---|---|
| Load/Unload Cog + Sync | Ẩn hoàn toàn lệnh khỏi Discord | ✅ Hoàn hảo cho Self-hosted |
| Check flag trong JSON | Lệnh vẫn hiện nhưng báo "đã tắt" | Dùng làm backup plan |

**Đề xuất:** Dùng Load/Unload Cog. Với mô hình Self-hosted (1 bot, 1 server), Rate Limit hoàn toàn không phải vấn đề.

#### 4B. Hệ Thống Blacklist Web — Flow Chi Tiết

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLOW TẠO BLACKLIST TICKET                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Officer gõ /blacklist report trên Discord                   │
│                    ↓                                            │
│  2. Bot tạo một Session Token (mã xác thực tạm thời)           │
│     và trả về link: https://tncbot.com/blacklist/new?token=xxx  │
│                    ↓                                            │
│  3. Officer click link → Web kiểm tra token hợp lệ không       │
│                    ↓                                            │
│  4. Web hiện form tạo Ticket:                                   │
│     ┌──────────────────────────────┐                            │
│     │ 🚨 Tạo Báo Cáo Blacklist    │                            │
│     │                              │                            │
│     │ ID Ingame: [___________]     │                            │
│     │ ID Discord: [___________]    │                            │
│     │ Nơi xảy ra: [Dropdown ▼]    │                            │
│     │   - Trong Guild              │                            │
│     │   - Ingame (Open World)      │                            │
│     │   - Discord                  │                            │
│     │ Bằng chứng: [Upload ảnh]     │                            │
│     │ Mô tả: [________________]    │                            │
│     │                              │                            │
│     │        [📤 Gửi Báo Cáo]     │                            │
│     └──────────────────────────────┘                            │
│                    ↓                                            │
│  5. Ticket được lưu vào Database trung tâm                     │
│                    ↓                                            │
│  6. Tất cả bot đã đăng ký sẽ đồng bộ blacklist mới            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Phương án xác thực Officer — So sánh:

| Phương án | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Session Token (1 lần)** | Bot tạo mã ngẫu nhiên, gắn vào URL, hết hạn sau 15 phút | Đơn giản, không cần đăng nhập web | Phải gõ lệnh Discord mỗi lần |
| **Discord OAuth2** | Officer đăng nhập web bằng tài khoản Discord, web check role | Chuyên nghiệp, dùng nhiều lần | Phức tạp hơn để code |
| **Kết hợp cả 2** | OAuth2 để đăng nhập, Token để xác nhận quyền cho hành động nhạy cảm | An toàn nhất | Tốn thời gian phát triển nhất |

> [!TIP]
> **Đề xuất tối ưu:** Dùng **Discord OAuth2** làm phương thức chính. Khi Officer đăng nhập web bằng Discord, hệ thống sẽ biết họ là ai (Discord ID), sau đó gọi Discord API để kiểm tra họ có role Officer trong server đã đăng ký hay không. NextAuth.js (đã có trong dự án) hỗ trợ Discord OAuth2 sẵn.

#### Khó khăn sẽ gặp:
- **Upload ảnh bằng chứng** — cần nơi lưu trữ ảnh (Cloudinary miễn phí, hoặc Supabase Storage).
- **Xác minh Officer role từ phía Web** — Web cần gọi Discord API để kiểm tra role của user trong một server cụ thể, cần bot token hoặc OAuth2 scope `guilds.members.read`.
- **Chống spam/lạm dụng** — Cần cơ chế report/review ticket trước khi đưa vào blacklist chính thức.

---

### Đề Xuất 5: Cơ Chế Đồng Bộ Blacklist Toàn Cầu

**Bạn muốn:** Mọi bot (từ nhiều server khác nhau) cùng chia sẻ 1 danh sách blacklist. Khi có người apply, bot check danh sách này.

#### Kiến trúc hệ thống:

```
                    ┌──────────────────────┐
                    │   TNC Central API    │
                    │   (Website Backend)  │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │   Database     │  │
                    │  │  (Blacklist)   │  │
                    │  └────────────────┘  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──┐   ┌────────▼───┐   ┌────────▼───┐
    │  Bot ở     │   │  Bot ở     │   │  Bot ở     │
    │  Server A  │   │  Server B  │   │  Server C  │
    │  (TNC)     │   │  (ABC)     │   │  (XYZ)     │
    └────────────┘   └────────────┘   └────────────┘
    
    Mỗi bot định kỳ gọi API:
    GET /api/blacklist → nhận danh sách mới nhất
```

#### Cơ chế đồng bộ — 2 phương án:

| Phương án | Cách hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Polling (Hỏi định kỳ)** | Bot gọi API mỗi 5-10 phút để lấy blacklist mới | Đơn giản, dễ code | Có độ trễ 5-10 phút |
| **Webhook (Push thông báo)** | Khi có blacklist mới, server đẩy thông báo xuống tất cả bot | Realtime, cực nhanh | Phức tạp, cần bot mở port nhận webhook |

> [!TIP]
> **Đề xuất:** Bắt đầu với **Polling** vì đơn giản và đủ dùng. Blacklist không phải dữ liệu cần real-time (trễ 5-10 phút là chấp nhận được). Sau này nếu cần, có thể nâng cấp lên Webhook.

#### Khó khăn sẽ gặp:
- **Ai kiểm duyệt ticket?** Nếu ai cũng có quyền tạo blacklist, sẽ có người lạm dụng để "trả thù cá nhân" — đưa người vô tội vào blacklist.
- **Bảo mật API** — Cần API Key để chỉ bot đã đăng ký mới gọi được API.
- **Chi phí hosting** — Database và API server trung tâm cần chạy 24/7.

#### Hướng giải quyết:
1. **Hệ thống duyệt ticket 2 lớp:**
   - Officer tạo ticket → ticket ở trạng thái `PENDING`.
   - Cần ít nhất **2-3 Officer từ các server KHÁC NHAU** xác nhận (Upvote) thì ticket mới chuyển sang `CONFIRMED` và được đưa vào blacklist chính thức.
   - Hoặc: Bạn (Admin hệ thống) duyệt thủ công ban đầu, sau đó khi cộng đồng đủ lớn thì chuyển sang cơ chế vote.
2. **API Key:** Khi bot đăng ký với hệ thống (Đề xuất 3), server trả về một API Key. Bot lưu key này và gửi kèm mỗi request.
3. **Hosting:** Vercel (free) cho Next.js + Supabase (free tier: 500MB database, 1GB storage) — đủ dùng cho giai đoạn đầu.

---

## 🏗️ Kế Hoạch Triển Khai Theo Giai Đoạn

### Phase 1: Nền Tảng Cốt Lõi (2-3 tuần)
> Mục tiêu: Hoàn thiện bot hiện tại, sẵn sàng cho người dùng tải về.

| # | Công việc | Chi tiết |
|---|---|---|
| 1.1 | Hoàn thiện tất cả tính năng bot hiện có | Fix bug, test kỹ các cog: Massing, Siphoned, GuildCheck, Blacklist, AI Chat |
| 1.2 | Tách biệt config và code | Đảm bảo tất cả cấu hình nằm trong `.env` và `config/`, không hardcode |
| 1.3 | Tạo hệ thống Toggle Module | Lệnh `/module` để bật/tắt các nhóm tính năng (Load/Unload Cog) |
| 1.4 | Viết script cài đặt tự động | `setup.bat` (Windows) / `setup.sh` (Linux) — hỏi token, tạo `.env`, cài thư viện |
| 1.5 | Viết `README.md` chi tiết | Hướng dẫn từ A-Z cho người không biết code |

---

### Phase 2: Website Nâng Cấp (2-3 tuần)
> Mục tiêu: Nâng cấp website thành hub trung tâm cho cộng đồng.

| # | Công việc | Chi tiết |
|---|---|---|
| 2.1 | Tích hợp Discord OAuth2 | Dùng NextAuth.js, cho phép đăng nhập bằng Discord |
| 2.2 | Tạo Database | Chọn Supabase hoặc tương đương, thiết kế bảng: `servers`, `blacklist_tickets`, `users` |
| 2.3 | API đăng ký server | Endpoint `/api/register` — bot gọi khi setup lần đầu |
| 2.4 | Trang Dashboard cho Officer | Sau khi đăng nhập Discord, hiện thông tin server đã đăng ký |
| 2.5 | Cập nhật giao diện Website | Polish các trang hiện có, thêm link Discord cộng đồng |

---

### Phase 3: Hệ Thống Blacklist Toàn Cầu (3-4 tuần)
> Mục tiêu: Xây dựng hệ thống blacklist chia sẻ giữa các server.

| # | Công việc | Chi tiết |
|---|---|---|
| 3.1 | Thiết kế Database Blacklist | Bảng `blacklist_tickets` với các trường: ingame_id, discord_id, location, evidence, description, status, submitted_by, server_id |
| 3.2 | Form tạo Ticket trên Web | Giao diện upload bằng chứng (ảnh), điền thông tin scammer |
| 3.3 | Xác thực Officer trên Web | Kiểm tra Discord role của người đăng nhập qua Discord API |
| 3.4 | API đồng bộ Blacklist | Endpoint `GET /api/blacklist` — bot gọi định kỳ để lấy danh sách mới nhất |
| 3.5 | Cập nhật bot: auto-check khi apply | Khi có đơn apply mới, bot gọi API check blacklist, cảnh báo Officer |
| 3.6 | Hệ thống duyệt ticket | Cơ chế upvote/confirm từ nhiều Officer trước khi blacklist chính thức |

---

### Phase 4: Đóng Gói & Phát Hành (1-2 tuần)
> Mục tiêu: Public sản phẩm cho cộng đồng.

| # | Công việc | Chi tiết |
|---|---|---|
| 4.1 | Kiểm tra toàn bộ hệ thống | Test end-to-end: cài đặt → đăng ký → tạo blacklist → đồng bộ |
| 4.2 | Tạo Discord Server cộng đồng | Kênh hỗ trợ, góp ý, báo lỗi, thông báo update |
| 4.3 | Hoàn thiện Website | Gắn link Discord, polish UI, SEO |
| 4.4 | Viết bài giới thiệu | Đăng lên các cộng đồng Albion Online (Reddit, Facebook, Discord) |
| 4.5 | (Tùy chọn) Docker Image | Đóng gói Docker để cài đặt cực nhanh cho người dùng nâng cao |

---

## 🔧 Công Nghệ Đề Xuất

| Thành phần | Công nghệ | Lý do |
|---|---|---|
| Bot Discord | Python + discord.py | Đang dùng, ổn định |
| Website | Next.js (React) | Đang dùng, phù hợp |
| Database | Supabase (PostgreSQL) | Free tier tốt, có Storage cho ảnh, có Auth |
| Hosting Web | Vercel | Free cho Next.js, auto deploy từ GitHub |
| Xác thực | NextAuth.js + Discord OAuth2 | Đã cài sẵn trong dự án |
| Lưu ảnh bằng chứng | Supabase Storage hoặc Cloudinary | Free tier đủ dùng |

---

## ⚠️ Rủi Ro & Lưu Ý Quan Trọng

> [!CAUTION]
> **Rủi ro lạm dụng Blacklist:** Đây là rủi ro lớn nhất. Nếu không có cơ chế kiểm duyệt, bất kỳ Officer nào cũng có thể đưa người vô tội vào blacklist vì tư thù. Cần thiết kế hệ thống duyệt ticket ngay từ đầu (Phase 3.6).

> [!WARNING]
> **Bảo mật API Key:** Vì bot là mã nguồn mở, API Key sẽ nằm trong file `.env` của người dùng. Cần đảm bảo mỗi API Key chỉ có quyền hạn giới hạn (chỉ đọc blacklist, chỉ tạo ticket cho server của mình).

> [!NOTE]
> **Chi phí:** Với free tier của Vercel + Supabase, bạn có thể phục vụ hàng trăm server mà không tốn đồng nào. Chỉ cần trả phí khi cộng đồng phát triển rất lớn (hàng nghìn server).

---

## Open Questions — Cần Quyết Định Trước Khi Bắt Tay Vào Làm

1. **Forum:** Bạn muốn tự build forum trên web, hay dùng Discord Server cộng đồng làm nơi thảo luận? (Đề xuất: Dùng Discord Server cho nhanh, tập trung năng lượng vào bot và blacklist).

2. **Kiểm duyệt Blacklist:** Bạn muốn dùng cơ chế nào?
   - **A.** Bạn (Admin) duyệt thủ công từng ticket.
   - **B.** Cần 2-3 Officer từ server khác nhau xác nhận.
   - **C.** Tự động duyệt ngay (rủi ro cao).

3. **Đăng ký server:** Bạn muốn bắt buộc hay khuyến khích? Nếu bắt buộc, bot sẽ không chạy nếu chưa đăng ký (nhưng người dùng có thể sửa code để bỏ qua).

4. **Ưu tiên Phase nào trước?** Bạn muốn tập trung hoàn thiện bot (Phase 1) trước hay đồng thời phát triển Website (Phase 2)?
