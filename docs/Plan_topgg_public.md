# 🚀 Kế Hoạch Public Bot Lên Top.gg — Mô Hình Invite Bot (1 Bot - Nhiều Server)

> **Lưu ý:** Đây là plan **bổ sung**, không thay thế [implementation_plan.md gốc](../implementation_plan.md) (hướng Self-Hosted).
> Plan gốc vẫn còn giá trị nếu muốn quay lại hướng Self-Hosted sau này.

---

## Tổng Quan

**Mục tiêu:** Đưa bot lên top.gg (hoặc nền tảng tương tự) để người dùng **bấm 1 nút "Invite"** là có bot trong server ngay, không cần cài đặt gì.

**Mô hình:** 1 instance bot chạy trên server → phục vụ tất cả Discord server đã invite.

**Tên bot public:** TeeEnTee (viết tắt TNT)

**Kiến trúc triển khai:** 1 Codebase, 2 Config (cùng source code, chạy khác nhau tùy biến môi trường `BOT_PROFILE`)

```
code sửa 1 lần → git push
        ↓
┌─────────────┬──────────────┐
│ Render #1   │ Render #2    │
│ Bot TNC     │ Bot TNT      │
│ (.env TNC)  │ (.env public)│
│ Có AI       │ Không AI     │
│ 1 server    │ Nhiều server │
└─────────────┴──────────────┘
```

**Khác biệt với Plan gốc:**

| | Plan gốc (Self-Hosted) | Plan này (Invite Bot) |
|---|---|---|
| Ai chạy bot? | Mỗi người tự chạy bot riêng | Chạy 1 bot duy nhất |
| Cài đặt | Clone repo, setup Python, VPS | Bấm "Invite" trên top.gg |
| Chi phí | $0 | Tăng theo số server |
| Fix bug | Mỗi người tự pull code mới | Deploy 1 lần, tất cả được fix |
| Data | Mỗi người giữ data riêng | Giữ toàn bộ data |

---

## Quyết Định Đã Chốt

| Câu hỏi | Quyết định |
|----------|------------|
| Hosting | Giữ Render + UptimeRobot (đang chạy ổn 3 tháng), xem xét Oracle Cloud Free sau |
| Scope public | Tất cả tính năng (trừ AI) |
| Giới hạn server | Có, tối đa 20-30 server lúc đầu |
| Tên bot | TeeEnTee (TNT) |
| Kiến trúc | 1 Codebase, 2 Config (dùng `BOT_PROFILE`) |

---

## 📊 Phân Tích Tính Năng: AI vs Non-AI

### 🔴 Tính năng SẼ BỎ (ở bản public)

Dùng AI — tốn API credits, không scale được khi public. Tất cả nằm trong 1 file duy nhất: `bot/cogs/chat_ai.py`.

| # | Tính năng | Lệnh / Trigger | Lý do bỏ |
|---|-----------|-----------------|-----------|
| 1 | Chat AI thông minh | Tag bot / reply / từ khóa | Tốn Gemini/OpenRouter credits |
| 2 | Failover AI chain | Tự động | 8 model dự phòng, tất cả tốn API |
| 3 | Vision / Đọc ảnh | `/aichat vision` | Dùng Gemini multimodal, tốn token |
| 4 | Nói leo ngẫu nhiên | `/aichat intercept` | Phụ thuộc AI để generate response |
| 5 | Auto Wiki (AI-enhanced) | `/ailibrary autowiki` | Dùng AI tổng hợp kết quả wiki |
| 6 | Thư viện kiến thức RAG | `/ailibrary set_channel`, `scan`, `clear` | OCR ảnh + AI search |
| 7 | Đọc link / Web scraping | Tự động khi chat có URL | Cào web để gửi cho AI xử lý |
| 8 | Buffer tin nhắn | `/aichat buffer` | Lưu đệm tin nhắn cho AI context |
| 9 | Check credit API | `/aimodel balance` | Không còn AI thì không cần |

> Chỉ cần **không load cog `chat_ai`** (dựa vào `BOT_PROFILE`) là bỏ toàn bộ AI — không ảnh hưởng gì đến các tính năng khác.

### 🟢 Tính năng GIỮ NGUYÊN (Không dùng AI)

| # | Cog | Tính năng | Dùng gì |
|---|-----|-----------|---------|
| 1 | `massing.py` | Hệ thống massing/CTA | Discord API + Albion API |
| 2 | `siphoned.py` | Theo dõi Siphoned Mana | Discord API + Albion API |
| 3 | `guildcheck.py` | Kiểm tra thông tin guild/player | Albion API |
| 4 | `lastseen.py` | Xem lần cuối player online | Albion API |
| 5 | `alo_tts.py` | Text-to-Speech voice channel | Discord Voice API |
| 6 | `corebank.py` | Hệ thống ngân hàng guild | Discord API + JSON storage |
| 7 | `onboarding.py` | Recruit — duyệt đơn thành viên mới | Albion API + Discord API |
| 8 | `blacklist.py` | Quản lý blacklist | Albion API + JSON storage |
| 9 | `about.py` | Thông tin bot | Discord API |

> Tính năng **recruit** (onboarding) bao gồm cả logic nhắc ảnh stat — hoàn toàn là if/else thuần, **không dùng AI**.

### 🔵 Tính năng Wiki

Lệnh `/wiki` tra cứu Albion Wiki qua DuckDuckGo — **không dùng AI**, chỉ cào kết quả search. Cần tách ra khỏi `chat_ai.py` thành cog độc lập.

---

## 🛠️ Nền Tảng Hiện Tại & Tương Thích Với Top.gg

| Nền tảng | Tương thích | Ghi chú |
|----------|-------------|---------|
| **GitHub** | ✅ | Không ảnh hưởng. Thêm link repo vào trang listing |
| **Render + UptimeRobot** | ✅ | Combo đang chạy ổn 3 tháng, bot online 24/7 |
| **Chat AI** | ❌ Bỏ ở bản public | Giữ cho bản TNC nội bộ |

---

## ⚠️ 3 Bất Lợi Chính & Giải Pháp

### Bất Lợi 1: Chi Phí Hosting 💰

**Vấn đề:** Nhiều server hơn → tốn RAM/CPU hơn → cần nâng plan hosting.

**Giải pháp theo giai đoạn:**

| Giai đoạn | Server | Hosting | Chi phí |
|-----------|--------|---------|---------|
| Khởi đầu | 0-50 | Render Free + UptimeRobot (giữ nguyên) | **$0/tháng** |
| Tăng trưởng | 50-200 | Render Starter hoặc Oracle Cloud Free | **$0-7/tháng** |
| Scale lớn | 200-500+ | VPS riêng (Contabo $5/tháng, 4GB RAM) | **$5-10/tháng** |

**Nguồn thu bù chi phí:** Premium tier, Top.gg vote reward, Ko-fi/Patreon, Sponsor từ guild lớn.

---

### Bất Lợi 2: Data Isolation 🔒

**Vấn đề:** Hiện tại data lưu chung trong `bot/Storage/`. Server A có thể thấy data server B.

**Giải pháp:**

#### Giai đoạn 1: Tách folder theo guild

```
bot/Storage/
├── global/                      ← data dùng chung
│   └── global_blacklist_v1.json
├── guilds/
│   ├── 123456789/               ← guild A
│   │   ├── massing_v1.json
│   │   ├── onboarding.json
│   │   └── corebank_v1.json
│   └── 987654321/               ← guild B
│       └── ...
```

#### Giai đoạn 2: Chuyển sang database cloud (khi 100+ guild)

Supabase (PostgreSQL, free 500MB) hoặc MongoDB Atlas (free 512MB).

**GitHub sync:** Data global → vẫn sync. Data per-guild → KHÔNG sync, lưu local/DB.

---

### Bất Lợi 3: Support Burden 🆘

**Vấn đề:** Nhiều user → nhiều bug report, xin feature, complain.

**Giải pháp:**
- **Tự động hóa:** Auto setup wizard, `/help` chi tiết, error messages rõ ràng, web dashboard
- **Cộng đồng:** Discord support server, GitHub Issues, docs đầy đủ
- **Giới hạn scope:** Public bản có giới hạn 20-30 server, self-serve design

---

## 🔧 Các Thay Đổi Kỹ Thuật Cần Thiết

| # | Việc | Mức độ | Chi tiết |
|---|------|--------|----------|
| 1 | **BOT_PROFILE config** | 🟢 Dễ | Thêm biến `BOT_PROFILE` vào config.py, đọc từ `.env` |
| 2 | **Điều kiện load cog `chat_ai`** | 🟢 Dễ | Chỉ load khi `BOT_PROFILE != "public"` |
| 3 | **Tách `/wiki` ra khỏi chat_ai** | 🟢 Dễ | Tạo cog `wiki.py` riêng |
| 4 | **Data per-guild** | 🔴 Lớn | Sửa tất cả cog để đọc/ghi data theo `guild_id` |
| 5 | **Bỏ hardcode TNC** | 🟡 TB | Onboarding, welcome message → config per-guild |
| 6 | **Permission linh hoạt** | 🟡 TB | `is_officer()` → mỗi server tự chọn role |
| 7 | **Auto setup wizard** | 🟡 TB | Bot join server mới → embed hướng dẫn + button |
| 8 | **Lệnh `/help`** | 🟢 Dễ | Help chi tiết cho từng module |
| 9 | **Bỏ GitHub sync per-guild** | 🟡 TB | Chỉ sync data global |
| 10 | **Rate limit protection** | 🟡 TB | Cooldown/ratelimit cho các lệnh |

---

## 📋 Lộ Trình Triển Khai

### Phase 1: Chuẩn Bị Nền Tảng (2-3 tuần)
> Mục tiêu: Sửa bot từ single-guild → multi-guild

| # | Công việc | Chi tiết |
|---|-----------|----------|
| 1.1 | BOT_PROFILE system | Thêm biến `BOT_PROFILE`, load cog tùy profile |
| 1.2 | Data isolation per-guild | Tách `bot/Storage/` theo `guilds/<guild_id>/` |
| 1.3 | Bỏ hardcode TNC | Config per-guild cho onboarding, welcome message |
| 1.4 | Permission system linh hoạt | Mỗi server tự chọn role nào là "Officer" |
| 1.5 | Tách `/wiki` ra cog riêng | Cog `wiki.py` độc lập, không phụ thuộc AI |
| 1.6 | Sửa GitHub sync | Chỉ sync data global, không sync per-guild data |

### Phase 2: Trải Nghiệm Người Dùng (1-2 tuần)
> Mục tiêu: Đảm bảo user tự dùng được mà không cần support

| # | Công việc | Chi tiết |
|---|-----------|----------|
| 2.1 | Auto setup wizard | Bot join server → gửi hướng dẫn setup + button |
| 2.2 | Lệnh `/help` chi tiết | FAQ + hướng dẫn từng module |
| 2.3 | Error messages rõ ràng | Sửa error message thành cụ thể + có hướng fix |
| 2.4 | Rate limit / cooldown | Bảo vệ bot khỏi spam/abuse |

### Phase 3: Beta Test (1-2 tuần)
> Mục tiêu: Mời 5-10 server Albion VN dùng thử

| # | Công việc | Chi tiết |
|---|-----------|----------|
| 3.1 | Tạo Discord Application mới | Bot TNT, token riêng, avatar riêng |
| 3.2 | Deploy Render instance #2 | Chạy cùng repo, env `BOT_PROFILE=public` |
| 3.3 | Mời server test | 5-10 guild Albion VN quen biết |
| 3.4 | Thu thập feedback & fix bug | Sửa dựa trên feedback |

### Phase 4: Public Release (1 tuần)
> Mục tiêu: Lên top.gg chính thức

| # | Công việc | Chi tiết |
|---|-----------|----------|
| 4.1 | Tạo Discord support server | Kênh hỗ trợ, góp ý, báo lỗi |
| 4.2 | Viết description cho top.gg | Mô tả bot, screenshot, hướng dẫn |
| 4.3 | Submit lên top.gg | Chờ review & approve |
| 4.4 | Viết docs/wiki | Tài liệu hướng dẫn đầy đủ |

### Phase 5: Scale & Monetize (tùy tình hình)
> Mục tiêu: Phát triển bền vững

| # | Công việc | Chi tiết |
|---|-----------|----------|
| 5.1 | Migrate sang DB cloud | Supabase/MongoDB khi đạt 100+ guild |
| 5.2 | Premium tier | Tính năng nâng cao cho guild donate |
| 5.3 | Blacklist sync đa server | Hệ thống blacklist chia sẻ (kết hợp Plan gốc Phase 3) |
| 5.4 | Vote reward system | Tích hợp top.gg API cho vote reward |

---

## 🔗 Liên Kết Với Plan Gốc

Plan này **không mâu thuẫn** với [Plan gốc](../implementation_plan.md). Có thể kết hợp:

| Từ Plan gốc | Dùng được cho Plan này |
|-------------|----------------------|
| Phase 2: Website nâng cấp | ✅ Web dashboard dùng chung |
| Phase 3: Blacklist toàn cầu | ✅ Áp dụng tại Phase 5.3 |
| Phase 4.2: Discord community server | ✅ Áp dụng tại Phase 4.1 |
| Đề xuất 4B: Blacklist web flow | ✅ Dùng nguyên thiết kế |

---

## Open Questions — Còn Lại

1. **Kiến trúc code:** Đã chốt dùng "1 Codebase, 2 Config" (`BOT_PROFILE`). Cần bàn chi tiết cách implement khi bắt đầu Phase 1.

2. **Avatar & branding:** Bot TNT cần avatar riêng, description riêng trên Discord Developer Portal.
