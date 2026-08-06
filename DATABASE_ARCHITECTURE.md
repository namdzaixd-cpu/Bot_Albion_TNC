# 🗄️ Kiến trúc Database — Bot TNC (Supabase)

> Tài liệu này giải thích **tầng dữ liệu** của Bot TNC theo ngôn ngữ đơn giản,
> dành cho người không chuyên backend. Sau đợt chuẩn hóa (commit `04df239`),
> hệ thống đã được làm lại để **an toàn, ổn định và mượt mà**.

---

## 1. Supabase là gì? (đơn giản)

Supabase = một **kho dữ liệu online** (giống Google Sheet nhưng mạnh hơn).
Bot và Web Dashboard đều đọc/ghi vào chung một kho này, nên:
- Bot lưu cấu hình → Web Dashboard hiện ra ngay.
- Web Dashboard đổi cài đặt → Bot nhận biết lập tức.

Supabase có 2 "chìa khóa" (key):
| Key | Dùng cho | Quyền |
|-----|----------|-------|
| **Service Role** | Backend (Bot + Server Web) | Toàn quyền, vượt qua mọi khóa |
| **Anon** | Trình duyệt (Browser) | Bị giới hạn, chỉ xem được gì được cho phép |

> ⚠️ **Quy tắc vàng:** Service Role là "chìa khóa master" — **tuyệt đối không** để lọt ra trình duyệt.

---

## 2. Kiến trúc tổng quan

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│  Discord Bot │────────▶│   Supabase       │◀────────│  Web Dashboard│
│  (Python)    │  ghi/đọc │   (Postgres)     │  đọc/ghi │  (Next.js)    │
└─────────────┘         └──────────────────┘         └──────────────┘
   dùng Service Role        ▲ bảng + RLS                  dùng Service Role
                             │ (chỉ server)
                        ❌ Anon bị KHÓA (deny all)
```

**Không có ai** truy cập DB trực tiếp từ trình duyệt — mọi thứ đi qua Server Web (API routes).

---

## 3. Hai tầng code

### 🐍 Tầng Bot (Python) — `bot/core/`
| File | Nhiệm vụ |
|------|----------|
| `db.py` | **Lớp kết nối chuẩn**. Có retry (thử lại 3 lần nếu mạng lỗi), ghi log rõ ràng, không bao giờ treo. |
| `database.py` | Lớp cũ, giờ chỉ là "cầu nối" để code cũ không bị hỏng. |
| `config_store.py` | **Cache thông minh**. Lưu config vào bộ nhớ, không cần query DB mỗi lần → nhanh gấp nhiều lần. |
| `storage.py` | Lưu file JSON lên DB an toàn (có kiểm tra lỗi). |
| `config.py` | Quản lý key & ID server. Bot dùng **Service Role**. |

### 🌐 Tầng Web (TypeScript) — `web_dashboard/src/lib/`
| File | Nhiệm vụ |
|------|----------|
| `supabaseServer.ts` | Client **Server-only** (Service Role). Chỉ dùng trong API routes. Lazy-init (không crash lúc build). |
| `supabase.ts` | Client **Browser** (Anon). Dành cho component nếu cần. |

> ✅ Đã kiểm tra: Service Role **không bị import** vào bất kỳ component client nào → key an toàn.

---

## 4. Các bảng dữ liệu

(Tạo bởi `scripts/migration.sql`, bổ sung bởi `scripts/migration_security.sql`)

| Bảng | Chứa gì |
|------|---------|
| `guild_config` | Cài đặt chung của guild (kênh apply, role officer...) |
| `corebank_config` | Cấu hình hệ thống Core-Bank (kênh, token UnbelievaBoat) |
| `blacklist` | Danh sách người bị cấm |
| `siphoned_energy` | Năng lượng Siphoned |
| `logs` | Nhật ký hoạt động (hiện ở dashboard "Hoạt động gần đây") |
| `json_storage` | Kho JSON linh hoạt (key = tên file) |
| `ai_config`, `user_activity`, `user_economy`, `alo_tts_config`, `sp_metadata` | Các module chuyên biệt |

**Bảo mật thêm:**
- Mọi bảng bật **RLS** (Row Level Security) → Anon bị từ chối hoàn toàn.
- **Index** trên `guild_id` → tìm kiếm nhanh.
- **Trigger** giới hạn `json_storage` ≤ 1MB → tránh phình to làm chậm hệ thống.

---

## 5. Cách hoạt động thực tế (ví dụ)

**Bro đổi "Bật module Onboarding" trên Web Dashboard:**
1. Web gửi PATCH → API route (`config/route.ts`) dùng `supabaseServer` cập nhật `guild_config`.
2. API gọi webhook báo Bot: "config đổi rồi!".
3. Bot nhận tín hiệu → `config_store.reload_all()` xoá cache → lần sau đọc lấy giá trị mới.
4. Bot bật/tắt module theo config mới.

→ **Mượt mà, không cần restart bot.**

---

## 6. Xử lý lỗi (Resilience)

Nếu Supabase mạng chập chờn:
- `db.py` **tự thử lại 3 lần** (nghỉ giãn cách tăng dần).
- Nếu vẫn lỗi → trả về giá trị mặc định, bot **không crash**.
- Mọi lỗi đều được **ghi log** để tra cứu sau.

---

## 7. Dành cho dev (kỹ thuật)

### Chạy test tầng DB (Python)
```bash
python scripts/test_db_layer.py
```
→ Kiểm tra hệ thống không crash khi thiếu credential.

### Build Web
```bash
cd web_dashboard && npm run build
```

### Áp dụng migration bảo mật
Chạy file `scripts/migration_security.sql` trên Supabase SQL Editor
(sau khi đã chạy `scripts/migration.sql`).

---

## 8. Tóm tắt cho bro Kudo

- ✅ Bot dùng **key đúng** (service role) → ghi config ổn định.
- ✅ Web **không lộ key** ra trình duyệt.
- ✅ Cache → dashboard **nhanh hơn**, bot **đỡ query DB**.
- ✅ Tự retry → **ít lỗi** khi mạng yếu.
- ✅ RLS + index + giới hạn size → **an toàn & hiệu năng tốt**.

> Mọi truy cập DB giờ đi qua 1 đường chuẩn (`db.py` / `config_store.py` / `supabaseServer.ts`),
> dễ bảo trì, dễ mở rộng. 🎯
