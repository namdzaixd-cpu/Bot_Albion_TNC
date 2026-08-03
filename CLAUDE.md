# CLAUDE.md

Xem [README.md](README.md) để biết tổng quan dự án, stack và cấu trúc code.

## Quy trình làm việc — QUAN TRỌNG NHẤT

Khi user đề xuất tính năng mới hoặc sửa đổi code: **bàn thiết kế trước** (mô tả lệnh, logic, ảnh
hưởng gì, file nào bị đụng) — KHÔNG viết/sửa code ngay.

Chỉ viết/sửa code khi user gõ RÕ RÀNG một trong các từ xác nhận: **"chốt", "ok làm đi", "làm đi",
"chốt code đi"**.

Các hành động sau KHÔNG tính là xác nhận: trả lời câu hỏi phụ, gửi ảnh/screenshot, cung cấp thêm
thông tin, hỏi ngược lại.

Nếu không chắc user đã chốt hay chưa, hỏi lại "Chốt chưa?" và chờ — tuyệt đối không tự ý code.

Ngoại lệ: các yêu cầu chỉ-đọc (đọc code, giải thích, đánh giá, tìm bug mà không sửa) không cần qua
gate này — chỉ áp dụng cho việc _viết/sửa_ code.

Quy tắc dấu hỏi: bất kỳ prompt nào kết thúc bằng dấu hỏi chấm `?` đều được coi là **câu hỏi /
thảo luận** — KHÔNG viết/sửa code, chỉ trả lời và trao đổi. Quy tắc này áp dụng ngay cả khi nội
dung câu hỏi liên quan đến code hoặc tính năng.

Sau khi code xong và pass `py_compile`: tự động `git add` + `git commit` luôn, không cần hỏi lại
"commit đi?" — user đã cấp quyền chuẩn.

Trước khi `git push`: đây là dự án dùng chung (có thể có người khác đã push thay đổi lên GitHub),
nên BẮT BUỘC `git fetch` rồi kiểm tra xem remote (`origin/<branch>`) có commit mới nào mà local
chưa có không.

- Nếu remote không có gì mới, hoặc có commit mới nhưng merge/rebase sạch không xung đột: push
  luôn, không cần hỏi lại.
- Nếu phát hiện xung đột (cùng sửa 1 đoạn code, hoặc merge/rebase báo conflict): DỪNG LẠI, KHÔNG
  tự ý resolve — báo rõ cho user biết file nào xung đột, xung đột với commit nào, và chờ user
  quyết định cách xử lý.

Sau khi push xong: kiểm tra xem máy local của user có đang chạy tiến trình bot thật không (vd
`ps aux | grep "bot/main.py"`), nếu có thì `kill` luôn tiến trình đó — tránh trường hợp bot chạy
song song cả ở local lẫn Render (xung đột Discord gateway, xung đột auto-sync Storage lên GitHub).

## Nguyên tắc code (Karpathy guidelines)

Sau khi đã "chốt", áp dụng 4 nguyên tắc này khi code:

1. **Nghĩ trước khi code** — không đoán mò, không giấu chỗ chưa rõ. Nếu có nhiều cách hiểu, nêu ra
   cho user chọn thay vì tự ý chọn 1. Nếu có cách đơn giản hơn cách user đề xuất, nói thẳng.
2. **Đơn giản trước tiên** — code tối thiểu đủ giải quyết đúng yêu cầu. Không thêm tính năng/
   abstraction/config chưa ai yêu cầu. Không xử lý lỗi cho tình huống không thể xảy ra.
3. **Sửa đúng phạm vi (surgical)** — chỉ đụng đúng chỗ cần sửa. Không tiện tay "cải thiện" code/
   comment xung quanh không liên quan, không refactor lan man. Giữ nguyên style hiện có. Chỉ dọn
   import/biến/hàm mồ côi do chính thay đổi của mình tạo ra — code chết có sẵn từ trước thì nêu ra
   cho user biết, không tự ý xóa.
4. **Làm theo tiêu chí kiểm chứng được** — biến yêu cầu mơ hồ thành tiêu chí rõ ràng, kiểm chứng
   được (vd: "sửa bug" → tìm cách tái hiện bug, sửa, rồi xác nhận hết bug thay vì chỉ sửa theo cảm
   tính).

## Về code

- Code ngắn gọn, đủ tính năng, không dài dòng thừa.
- Luôn check syntax (`python -m py_compile ...`) trước khi báo hoàn thành một thay đổi Python.
- Sau khi thêm tính năng mới hoặc fix bug trong `bot/`: cập nhật lại danh sách lệnh (bảng tính
  năng) trong README.md, và cập nhật `FEATURE_FIELDS` trong `bot/cogs/about.py` (bảng lệnh hiện
  trong `/aboutme`) nếu danh sách slash/prefix command thay đổi.
- Commit message do AI tạo (`git commit`) phải viết 100% bằng tiếng Việt (vd `sửa_lỗi(ai): ...`
  thay vì `fix(ai): ...`), khớp style hiện có trong git log.
- Khi tạo commit: KHÔNG thêm dòng `Co-Authored-By: Claude ...` vào commit message — user muốn
  GitHub chỉ hiển thị mình họ là tác giả, không hiện đồng tác giả "claude".
- TUYỆT ĐỐI KHÔNG chạy lệnh khởi động bot thật trên máy local của user (vd `python bot/main.py`,
  `python main.py`) — bot đang chạy 24/7 trên Render (production), chạy thêm 1 bản ở local sẽ
  khiến bot bị "chạy trùng" ở 2 nơi cùng lúc (xung đột kết nối Discord gateway, xung đột auto-sync
  Storage lên GitHub). Chỉ chạy các script test độc lập (vd `test_api_key/*.py`, `py_compile`,
  test suite trong `bot/tests/`) — không chạy chính bot.
- Cấu trúc bot: `bot/main.py` (entry point) + `bot/core/` (hạ tầng dùng chung: config, storage,
  permissions, webserver) + `bot/cogs/` (mỗi hệ thống tính năng — siphoned, massing, lastseen,
  guildcheck, alo_tts, corebank — là 1 cog riêng). Sửa 1 tính năng thì chỉ đụng cog tương ứng.
- Cấu hình AI Chat: Chỉ dẫn tính cách, prompt hệ thống nằm tại file [bot/core/templates/chat_ai_instruction.txt](bot/core/templates/chat_ai_instruction.txt). Chỉnh sửa file này thay vì sửa trực tiếp code Python trong cog.

## Thư mục Storage — QUY TẮC BẮT BUỘC

`bot/Storage/` là nơi lưu trữ **dữ liệu vận hành thật** của bot (dữ liệu người dùng, cấu hình guild, template, điểm số...).
Thư mục này được **tự động đồng bộ lên GitHub** mỗi khi có thay đổi (xem `GITHUB_SYNCED_FILES` trong `bot/core/storage.py`).

### ⛔ TUYỆT ĐỐI KHÔNG được phép:

- Xóa, ghi đè, hay sửa thẳng file JSON trong `bot/Storage/` — dù chỉ để test hay debug.
- Đọc/ghi file trong thư mục này bằng `open()` thuần — phải dùng `load_json()` / `save_json()` từ `bot/core/storage.py`.
- Đặt file tạm, file test, file log vào đây — các file không phải dữ liệu kho sẽ làm ô nhiễm GitHub sync.

### ✅ Quy tắc khi thêm dữ liệu mới:

1. File JSON mới **phải** đặt vào `bot/Storage/`.
2. Import `STORAGE_DIR` từ `bot/core/config.py`, khai báo đường dẫn bằng `os.path.join(STORAGE_DIR, "tên_file.json")`.
3. Đặt tên file theo pattern: `tnc_<tính_năng>_v<số_version>.json`
   - Ví dụ đúng: `tnc_massing_v1.json`, `tnc_register_v1.json`, `tnc_sp_v32.json`
   - Ví dụ sai: `data.json`, `config_temp.json`, `test123.json`
4. Thêm đường dẫn mới vào danh sách `GITHUB_SYNCED_FILES` trong `bot/core/storage.py`.
5. Đọc file chi tiết [bot/Storage/README.md](bot/Storage/README.md) trước khi thêm file mới.

## Skills & Agents có sẵn trong dự án

`.claude/skills/` — 16 skill từ [anthropics/skills](https://github.com/anthropics/skills) (chi tiết:
`.claude/skills/README.md`). Dùng khi task khớp mô tả:

- `algorithmic-art` — vẽ art sinh thuật toán bằng p5.js (seeded randomness, flow field, particle)
- `brand-guidelines` — áp màu/font thương hiệu Anthropic vào artifact
- `claude-api` — tra cứu Claude API/Anthropic SDK (model, giá, streaming, tool use, MCP, caching)
- `doc-coauthoring` — quy trình đồng viết tài liệu/spec/decision doc cùng user
- `docx` — tạo/đọc/sửa file Word (.docx/.dotx): mục lục, heading, tracked changes, ảnh, find-replace
- `frontend-design` — gợi ý thiết kế UI/thẩm mỹ không rập khuôn (typography, màu sắc)
- `internal-comms` — template báo cáo nội bộ, cập nhật lãnh đạo, báo cáo sự cố, FAQ
- `mcp-builder` — hướng dẫn xây MCP server chất lượng cao (Python FastMCP hoặc Node/TS)
- `pdf` — đọc/trích xuất/gộp/tách/xoay/watermark/điền form/OCR PDF
- `pptx` — tạo/sửa PowerPoint (.pptx/.potx), template, ghi chú diễn giả
- `skill-creator` — meta-skill để tạo/sửa/đánh giá skill khác
- `slack-gif-creator` — tạo GIF động cho Slack (đúng kích thước/tối ưu)
- `theme-factory` — áp theme màu/font có sẵn (hoặc tự tạo) cho artifact
- `web-artifacts-builder` — xây artifact HTML phức tạp nhiều component (React/Tailwind/shadcn)
- `webapp-testing` — test web app local bằng Playwright (screenshot, log, kiểm tra UI)
- `xlsx` — tạo/sửa spreadsheet (.xlsx/.xlsm/.csv/.tsv): công thức, format, chart, dọn dữ liệu bẩn

`.claude/agents/` — subagent riêng cho dự án, gọi qua Agent tool:

- `python-reviewer` — review code Python (bảo mật, PEP8, type hint, concurrency, code quality)
- `silent-failure-hunter` — săn lỗi nuốt exception / silent failure (vd: `except Exception: pass`)

# Project-Scoped Rules

## Quy tắc lưu trữ Rules/Yêu cầu mới
Khi có yêu cầu mới, rule mới hoặc chỉ dẫn từ người dùng (User Rules/Instructions), thay vì ghi vào file `.agents/AGENTS.md`, hãy ghi trực tiếp vào file [CLAUDE.md](file:/Bot_Albion_TNC/CLAUDE.md).

## Feature Documentation
Từ nay khi user mô tả tính năng mới trong quá trình phát triển, BẮT BUỘC phải tự động lưu mô tả cơ chế hoạt động và chi tiết cách hoạt động của tính năng đó vào một file riêng (vd: `docs/features.md` hoặc một markdown file tương ứng). 
Việc này đảm bảo dữ liệu không bị thất lạc và có thể dùng trực tiếp để đưa lên web dashboard hoặc viết tài liệu hướng dẫn sau này.

## Ngôn ngữ & xưng hô

Giao tiếp bằng tiếng Việt xương hô theo cách người dùng gọi
