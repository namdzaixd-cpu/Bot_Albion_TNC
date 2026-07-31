# TNC Manager — Albion Online Guild Discord Bot

Discord bot quản lý guild **TNC** trong game Albion Online. Bot chính viết bằng Python
(`discord.py`), được host online tại [bot-albion-tnc.onrender.com](https://bot-albion-tnc.onrender.com/), kèm một pnpm workspace TypeScript đang trong giai đoạn
scaffold cho dashboard web trong tương lai.

## Cấu trúc dự án

```
bot/                  Discord bot Python (thành phần chính, đang chạy production)
  main.py             Entry point: khởi tạo bot, load các cog, chạy keep_alive + bot.run
  core/               Hạ tầng dùng chung: config (env/const), storage (đọc/ghi JSON + sync GitHub),
                      permissions (is_officer), webserver (Flask keep-alive)
    templates/        Templates dùng chung: trạng thái web (index.html), mô tả tính cách AI (chat_ai_instruction.txt)
  cogs/               Mỗi hệ thống tính năng là 1 Cog: about, siphoned, massing, lastseen,
                      guildcheck, alo_tts, corebank
  *.json              Dữ liệu bot (điểm SP, massing, register, config...), tự backup .bak
artifacts/
  api-server/          Express 5 API, có route /bot/* proxy sang Flask bot (port 5000)
  mockup-sandbox/       React app scaffold (shadcn/ui) — chưa có trang thực tế
lib/
  db/                    Drizzle ORM schema (PostgreSQL) — hiện còn rỗng
  api-spec/              OpenAPI spec
  api-zod/               Zod schema sinh từ OpenAPI
  api-client-react/      React Query hooks sinh từ OpenAPI
scripts/                 Script tiện ích dùng chung trong workspace
```

## Bot Discord — tính năng

| Hệ thống | Lệnh | Mô tả |
|---|---|---|
| **About** | `/aboutme` | Giới thiệu bot + link trang web (embed ngắn gọn) |
| **Siphoned Points** | `/spupdate`, `/spcheck`, `!addsp`, `!removesp`, `!removesprole`, `!resetsp` | Parse file log `.txt` để cộng dồn điểm siphoned theo người chơi, bảng xếp hạng phân trang |
| **Massing** | `/massing`, `/masstemplatelist`, `/masstemplatedelete` | Tạo party PVP/PVE theo role/weapon, UI nút bấm (join/kick/move/fill), lưu template, tự khôi phục sau restart |
| **GuildCheck** | `/registertnc`, `/registerfor`, `/myign`, `/guildconfig`, `/guildcheck`, `/unresolved` | Đăng ký IGN Albion, tự kiểm tra qua Albion API xem còn trong guild không, tự xóa role nếu đã rời |
| **Alo (TTS)** | `/alojoin`, `/aloleave`, `/alonametoggle`, `/alo`, `/aloconfig`, `/alomute`, `/alounmute` | Đọc tin nhắn text thành giọng nói (gTTS) vào voice channel, tự rejoin khi rớt mạng |
| **Core-Bank** | `/coresetup`, `/coreadd`, `/coreremove`, `/coreautoreact`, `/corelist` | Tự động thả emoji reaction lên ảnh core nộp vào kênh, quy đổi ra giá trị silver |
| **Chat AI** | Tag bot / reply bot, `/aimodel view`, `/aimodel set`, `/aimodel add`, `/aimodel remove` | Chat AI theo tính cách tùy chỉnh (xem [Cấu hình AI Chat](#cấu-hình-ai-chat)), đọc context kênh/link/reply, đổi model qua OpenRouter hoặc Google trực tiếp |

Phân quyền dựa theo **tên role Discord**: `officer`, `guild master`, `admin`, `phó hội`, `chủ hội`.
## Cấu hình AI Chat

Cog `chat_ai` hỗ trợ 2 nhà cung cấp model, chọn qua tên model:

- Model **không** có prefix `google/` → gọi qua **OpenRouter** (`OPENROUTER_API_KEY`).
- Model **có** prefix `google/` (vd `google/gemini-3.5-flash-lite`) → gọi thẳng **Google AI Studio** bằng `GEMINI_API_KEY`, không qua OpenRouter — giúp bot còn dùng được nếu OpenRouter bị sập/hit rate limit.

- **Tính cách bot**: sửa trực tiếp file text [bot/core/templates/chat_ai_instruction.txt](bot/core/templates/chat_ai_instruction.txt) — không cần đụng code. Bot tự đọc file này lúc khởi động, nên sửa xong phải **restart bot** mới áp dụng. File có placeholder `{CURRENT_MODEL}` được tự động thay bằng model đang active. Nếu file trống hoặc bị xóa, bot fallback về cấu hình mặc định khai báo trong `chat_ai.py`.
- **Đổi model qua Discord**: `/aimodel view` (xem model hiện tại + danh sách), `/aimodel set` (đổi model đang dùng), `/aimodel add`/`/aimodel remove` (thêm/xóa model khỏi danh sách) — chỉ Officer trở lên dùng được. Lựa chọn được lưu vào `bot/tnc_ai_config.json` (tự sync GitHub) nên vẫn giữ nguyên sau khi bot restart.
- **Đổi model mặc định lúc chưa từng dùng `/aimodel`**: sửa biến `OPENROUTER_MODEL` trong `.env` (local) hoặc Environment Variables trên Render (production).

### Test AI chat ngoài Discord

2 script độc lập trong `bot/`, cùng lấy `OPENROUTER_API_KEY`/`OPENROUTER_MODEL` từ `.env` qua `core/config.py` (đổi model/key ở `.env` thì cả 2 script lẫn bot chính đều dùng chung giá trị mới):

| File | Công dụng |
|---|---|
| `bot/test_openrouter_full.py` | Gọi kèm system instruction thật từ `chat_ai_instruction.txt` — mô phỏng đúng điều kiện production |
| `bot/test_openrouter_baseline.py` | Gọi trần, không có system instruction — đo độ trễ gốc của API/model, dùng để so sánh xem prompt tính cách có làm chậm phản hồi hay không |

```bash
python bot/test_openrouter_full.py
python bot/test_openrouter_baseline.py
```

Gõ câu hỏi rồi Enter, script in ra `[X.XXs] <câu trả lời>` — số giây là thời gian phản hồi thật từ OpenRouter, không qua Discord.

## Lưu trữ dữ liệu

Toàn bộ state lưu dưới dạng file JSON phẳng trong `bot/`. Mỗi lần ghi:

1. Ghi ra file `.tmp`, backup file cũ thành `.bak`, rồi `os.replace` — chống hỏng dữ liệu khi crash giữa chừng.
2. Tự động `git commit` + `git push` dữ liệu lên GitHub (do Replit không có disk bền vững) — xem `sync_to_github()` trong `bot/main.py`.

## Chạy bot

```bash
pip install -r requirements.txt
# hoặc: uv sync (dùng pyproject.toml / uv.lock)

cp bot/.env.example bot/.env   # rồi điền giá trị thật
python bot/main.py
```

Biến môi trường cần thiết (xem [bot/.env.example](bot/.env.example)):

| Biến | Mô tả |
|---|---|
| `DISCORD_TOKEN` | Token bot Discord |
| `DISCORD_GUILD_ID` | ID server Discord |
| `GITHUB_GIT_URL` | URL GitHub kèm Personal Access Token, dùng để auto-sync dữ liệu |
| `OPENROUTER_API_KEY` | API key OpenRouter, dùng cho tính năng chat AI (cog `chat_ai`) |
| `OPENROUTER_MODEL` | Model OpenRouter dùng cho chat AI (để trống sẽ dùng model mặc định trong code) |
| `GEMINI_API_KEY` | API key Google AI Studio, chỉ cần khi chọn model có prefix `google/` qua `/aimodel` |

Bot expose Flask server tại `http://localhost:5000` (Online: [bot-albion-tnc.onrender.com](https://bot-albion-tnc.onrender.com/)):
- `GET /` — Trang giới thiệu & trạng thái bot (HTML)
- `GET /health` — health check

## Workspace TypeScript (pnpm)

```bash
pnpm install
pnpm run typecheck   # typecheck toàn bộ package
pnpm run build        # typecheck + build
```

- `pnpm --filter @workspace/api-spec run codegen` — sinh lại API hooks/Zod từ OpenAPI spec
- `pnpm --filter @workspace/db run push` — push schema DB (chỉ dùng khi dev)
- `pnpm --filter @workspace/api-server run dev` — chạy API server local

> Phần này hiện là hạ tầng chuẩn bị cho dashboard web, đa số còn ở dạng scaffold/boilerplate
> (schema DB rỗng, chưa có trang React thực tế). `api-server` đã có route `/bot/*` proxy
> sang bot Python để làm cầu nối khi dashboard được xây.

## Lưu ý bảo mật

- **Không bao giờ commit file `.env`** — chứa `DISCORD_TOKEN` và `GITHUB_GIT_URL` (URL này nhúng
  sẵn PAT của GitHub).
- `GITHUB_GIT_URL` được truyền trực tiếp vào `subprocess.run(["git", "push", GIT_URL, "main"])` —
  cẩn thận khi log lỗi vì URL có thể lộ token ra console/log.
