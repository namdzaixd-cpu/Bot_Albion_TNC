# TNC Manager — Albion Online Guild Discord Bot

Discord bot quản lý guild **TNC** trong game Albion Online. Bot chính viết bằng Python
(`discord.py`), host trên Replit, kèm một pnpm workspace TypeScript đang trong giai đoạn
scaffold cho dashboard web trong tương lai.

## Cấu trúc dự án

```
bot/                  Discord bot Python (thành phần chính, đang chạy production)
  main.py             Entry point: khởi tạo bot, load các cog, chạy keep_alive + bot.run
  core/               Hạ tầng dùng chung: config (env/const), storage (đọc/ghi JSON + sync GitHub),
                      permissions (is_officer), webserver (Flask keep-alive)
  cogs/               Mỗi hệ thống tính năng là 1 Cog: siphoned, massing, lastseen,
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
| **Siphoned Points** | `/spupdate`, `/spcheck`, `!addsp`, `!removesp`, `!removesprole`, `!resetsp` | Parse file log `.txt` để cộng dồn điểm siphoned theo người chơi, bảng xếp hạng phân trang |
| **Massing** | `/massing`, `/masstemplatelist`, `/masstemplatedelete` | Tạo party PVP/PVE theo role/weapon, UI nút bấm (join/kick/move/fill), lưu template, tự khôi phục sau restart |
| **GuildCheck** | `/registertnc`, `/registerfor`, `/myign`, `/guildconfig`, `/guildcheck`, `/unresolved` | Đăng ký IGN Albion, tự kiểm tra qua Albion API xem còn trong guild không, tự xóa role nếu đã rời |
| **Alo (TTS)** | `/alojoin`, `/aloleave`, `/alonametoggle`, `/alo`, `/aloconfig`, `/alomute`, `/alounmute` | Đọc tin nhắn text thành giọng nói (gTTS) vào voice channel, tự rejoin khi rớt mạng |
| **Core-Bank** | `/coresetup`, `/coreadd`, `/coreremove`, `/coreautoreact`, `/corelist` | Tự động thả emoji reaction lên ảnh core nộp vào kênh, quy đổi ra giá trị silver |

Phân quyền dựa theo **tên role Discord**: `officer`, `guild master`, `admin`, `phó hội`, `chủ hội`.

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

Bot expose Flask server tại `http://localhost:5000`:
- `GET /` — trạng thái bot (JSON)
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
