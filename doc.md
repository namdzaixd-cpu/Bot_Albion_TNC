Tôi đã đọc trực tiếp repo. **Bot production của bro là Python với `discord.py`, không phải JavaScript**. Phần TypeScript hiện chỉ là scaffold cho dashboard/API tương lai.

## Bot hiện đang “nhớ” như thế nào?

Trong `bot/cogs/chat_ai.py`, bot có:

```python
self.message_buffers = {}
```

Mỗi channel có một:

```python
collections.deque(maxlen=50)
```

Khi có tin nhắn, bot lưu:

```python
{
    "author": message.author.display_name,
    "roles": "...",
    "content": message.content
}
```

Sau đó, khi người dùng tag hoặc reply bot, nó lấy toàn bộ buffer của channel ghép vào prompt.

### Đây chỉ là trí nhớ RAM ngắn hạn

Hiện tại:

```text
Discord channel
   ↓
deque 50 tin nhắn trong RAM
   ↓
ghép thành một prompt lớn
   ↓
gửi Gemini/OpenRouter
```

Khi Render restart hoặc redeploy:

```text
message_buffers = {}
```

Toàn bộ lịch sử mất.

Render mặc định dùng filesystem tạm thời; các thay đổi file local cũng mất khi redeploy nếu không có persistent disk. Persistent disk lại chỉ gắn được với một service instance và làm mất khả năng zero-downtime deploy. Vì vậy database bên ngoài phù hợp hơn việc lưu lịch sử AI vào file local. ([Render][1])

## Những vấn đề cụ thể trong hệ thống memory hiện tại

### 1. Bot không lưu câu trả lời của chính nó

Đầu `on_message()` có:

```python
if message.author.bot:
    return
```

Vì vậy buffer chỉ lưu tin nhắn của người dùng, không lưu câu trả lời AI.

Ví dụ:

```text
User: Build Bloodletter nào tốt?
Bot: Dùng Bloodletter + Mistcaller...
User: Còn giày thì sao?
```

Nếu người dùng không reply trực tiếp tin nhắn của bot, model có thể không biết “giày” đang nói về build Bloodletter nào.

Nói cách khác, đây là **channel context**, chưa phải **conversation history**.

### 2. Tin nhắn hiện tại bị đưa vào prompt hai lần

Ở `chat_ai.py:316`, tin nhắn vừa nhận đã được thêm vào buffer.

Sau đó ở `chat_ai.py:417`, toàn bộ buffer được đưa vào `context_data`.

Cuối cùng ở `chat_ai.py:505`, nội dung hiện tại lại được nối thêm lần nữa:

```python
prompt = context_data + user_info + content
```

Kết quả:

```text
Nội dung kênh:
[User]: Build Bloodletter nào tốt?

Câu hỏi người dùng:
Build Bloodletter nào tốt?
```

Điều này không nghiêm trọng, nhưng làm tốn token và đôi khi khiến model coi câu hỏi là được nhấn mạnh hai lần.

### 3. Bot đưa quá nhiều thông tin vào mỗi request

Mỗi lần gọi AI, prompt có thể chứa:

* System instruction hơn 10.000 ký tự.
* Tối đa 50–300 tin nhắn của channel.
* Danh sách GM, VG và Officer.
* Thống kê tất cả role trong server.
* Nội dung reply.
* Nội dung URL lên tới 15.000 ký tự mỗi URL.
* Kết quả Albion Wiki.
* Nội dung của channel được mention.

Đây là cách **“stuff everything into context”**, không phải retrieval memory. Khi server hoạt động nhiều hơn, cách này sẽ:

* Tốn token.
* Chậm phản hồi.
* Làm model mất tập trung.
* Tăng nguy cơ prompt injection từ link hoặc nội dung channel.
* Khó xác định thông tin nào thực sự quan trọng.

### 4. `debug_prompt.txt` có thể làm lộ nội dung chat

Mỗi request đều ghi toàn bộ prompt vào:

```python
with open("debug_prompt.txt", "w", encoding="utf-8") as f:
    f.write(prompt)
```

File này nằm ở root và hiện không được `.gitignore`.

Nó có thể chứa:

* Tin nhắn channel.
* Tên người dùng và role.
* Nội dung URL.
* Dữ liệu server.
* Câu hỏi riêng của thành viên.

Nó không được hệ thống auto-sync JSON tự động commit, nhưng rất dễ bị đưa lên GitHub nếu sau này chạy:

```bash
git add .
```

Đây là điểm nên xử lý sớm.

### 5. Không nên lưu AI history bằng JSON rồi push GitHub

Cơ chế hiện tại trong `bot/core/storage.py` phù hợp với dữ liệu nhỏ, ít thay đổi như:

* Model đang chọn.
* Cấu hình TTS.
* Điểm Siphoned.
* Cấu hình guild.

Nó không phù hợp với chat history.

Nếu mỗi tin nhắn đều gọi `save_json()`:

```text
Tin nhắn Discord
   ↓
ghi file JSON
   ↓
tạo thread
   ↓
git add
   ↓
git commit
   ↓
git pull --rebase
   ↓
git push
```

Một channel hoạt động nhiều có thể tạo hàng trăm commit và hàng đợi thread Git. Dù `_git_lock` ngăn Git chạy đồng thời, các thread vẫn có thể chờ phía sau.

---

# Phương án đúng cho repo này

Tui đề xuất **kiến trúc lai**:

```text
JSON + GitHub
→ tiếp tục dùng cho dữ liệu vận hành hiện có

Supabase Postgres
→ dùng riêng cho AI history, memory và summary

RAM deque
→ giữ làm cache ngắn hạn, không phải nguồn dữ liệu chính
```

## Không cần migrate toàn bộ JSON ngay

Bro chưa cần chuyển:

```text
tnc_sp_v32.json
tnc_lastseen_v1.json
tnc_tts_config_v1.json
tnc_ai_config.json
```

sang Supabase ngay.

Những file này hiện nhỏ và ít ghi. Chuyển toàn bộ cùng lúc sẽ tăng phạm vi sửa code, tăng nguy cơ ảnh hưởng các tính năng đang chạy ổn.

Chỉ nên chuyển phần AI trước:

```text
AI conversation history
User memory
Channel summary
Memory approval
```

Sau này khi dashboard hoàn thiện hoặc cần chạy nhiều bot instance, mới cân nhắc chuyển phần còn lại.

---

# Kiến trúc memory phù hợp

```text
┌──────────────────────────────────────┐
│ Discord message                      │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ Lưu message vào Supabase             │
│ user / assistant / tool              │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ Memory retrieval                     │
│                                      │
│ • 12–20 tin nhắn gần nhất            │
│ • Summary của channel/conversation   │
│ • 3–8 memory của người đang hỏi      │
│ • Reply message                      │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ Prompt gửi Gemini/OpenRouter         │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ Lưu câu trả lời assistant            │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ Có thông tin đáng nhớ?               │
│ → tạo memory candidate               │
└──────────────────────────────────────┘
```

## Nên chia thành bốn tầng

### Tầng 1: Recent messages

Lưu cả hai phía:

```text
user
assistant
user
assistant
```

Khi gọi model, chỉ lấy khoảng 12–20 tin nhắn gần nhất của conversation.

### Tầng 2: Channel summary

Khi lịch sử dài, model phụ tạo summary:

```text
Channel đang thảo luận về build Bloodletter cho Mists.
User A muốn build rẻ khoảng 500k.
Đã thống nhất dùng Mistcaller và Cleric Robe.
Chưa quyết định giày.
```

Không cần gửi lại hàng trăm tin nhắn.

### Tầng 3: User memory

Chỉ lưu những thông tin tương đối lâu dài:

```text
User thích được gọi là bro.
User thường chơi healer.
User là người mới chơi Albion.
User muốn build dưới 1 triệu silver.
User không thích bot cà khịa.
```

Không nên lưu:

```text
User vừa chết ở Black Zone.
User đang online.
User vừa hỏi Bloodletter.
```

Các thông tin ngắn hạn nên nằm trong conversation history hoặc summary.

### Tầng 4: Guild knowledge

Tách khỏi memory cá nhân:

```text
Quy định regear.
Lịch CTA.
Quy tắc chia loot.
Danh sách officer.
Hướng dẫn đăng ký IGN.
Cách sử dụng các command của bot.
```

Đây gần với knowledge base hơn là memory.

---

# Các bảng database nên có ở giai đoạn đầu

## `ai_conversations`

```text
id
guild_id
channel_id
thread_id
conversation_type
summary
last_message_at
created_at
```

Không nhất thiết mỗi user có một conversation riêng. Với Discord guild, conversation thường gắn với channel hoặc thread.

## `ai_messages`

```text
id
conversation_id
discord_message_id
discord_user_id
role
content
reply_to_message_id
created_at
```

`role` gồm:

```text
user
assistant
tool
```

Phải lưu cả câu trả lời của bot.

## `ai_user_memories`

```text
id
guild_id
discord_user_id
memory_type
content
importance
confidence
status
source_message_id
expires_at
created_at
updated_at
```

`status`:

```text
pending
approved
rejected
expired
```

## `ai_channel_settings`

```text
guild_id
channel_id
history_enabled
memory_enabled
retention_days
max_recent_messages
created_at
updated_at
```

Bảng này quan trọng vì bro không nên mặc định lưu toàn bộ tin nhắn của mọi channel.

---

# Không nên lưu tất cả tin nhắn server

Hiện bot đưa mọi tin nhắn mà nó thấy vào RAM buffer. Nhưng khi chuyển sang database, không nên mặc định ghi toàn bộ server vĩnh viễn.

Tui đề xuất:

### Mặc định lưu

* Tin nhắn gọi bot.
* Tin nhắn reply bot.
* Câu trả lời của bot.
* Một số message liên quan nằm trong cùng conversation.

### Chỉ lưu khi Officer bật

* Toàn bộ lịch sử của một channel AI cụ thể.
* Channel summary dài hạn.
* Guild knowledge extraction.

Có thể thêm:

```text
/aimemory channel on
/aimemory channel off
/aimemory retention 30
```

Điều này vừa giảm database, vừa minh bạch hơn với thành viên.

---

# Có nên thêm vector search ngay không?

**Chưa nên.**

Postgres đã có full-text search, còn Supabase có thể thêm `pgvector` sau này nếu cần semantic search. ([Supabase][2])

Giai đoạn đầu chỉ cần:

```text
discord_user_id filter
guild_id filter
memory_type filter
importance sorting
recent timestamp
keyword hoặc tag
```

Khi mỗi user có hàng trăm memory hoặc knowledge base Albion lớn hơn, mới thêm embedding.

Với tiếng Việt và thuật ngữ Albion, semantic search sau này sẽ hữu ích cho những câu như:

```text
“build chạy trốn khi đi gathering”
```

tìm được memory hoặc knowledge:

```text
“escape set dùng Miner Workboots và Bloodletter”
```

Nhưng chưa cần trả thêm chi phí embedding ngay.

---

# Có nên làm “skill tự sinh” giống Hermes không?

## Chưa nên làm ở phiên bản đầu

Bot hiện tại chưa phải tool-calling agent. Nó đang thực hiện một vòng đơn giản:

```text
Prompt → model → text reply
```

Nó chưa có hệ thống:

```text
model chọn tool
tool chạy
model xem kết quả
model tiếp tục
```

Vì vậy, cho bot tự tạo `SKILL.md` lúc này chưa mang lại nhiều tác dụng. Model có thể đọc skill, nhưng không có hạ tầng để thực hiện quy trình nhiều bước như Hermes.

### Phiên bản đầu chỉ nên có skill tĩnh

Ví dụ:

```text
answer_albion_build
explain_guild_commands
summarize_channel
answer_guild_rules
```

Các skill này có thể là các prompt module do admin duyệt.

### Chỉ tự tạo skill sau khi có tool framework

Ví dụ bot sau này có tool:

```text
search_albion_wiki
get_member_ign
get_siphoned_points
get_massing_status
get_core_history
```

Lúc đó skill mới thực sự có giá trị:

```text
Skill: Kiểm tra thành viên chuẩn bị CTA

1. Lấy IGN đã đăng ký.
2. Kiểm tra guild membership.
3. Kiểm tra role.
4. Kiểm tra massing status.
5. Trả kết quả.
```

Hiện giờ ưu tiên đúng là:

```text
History → Memory → Summary → Retrieval → sau cùng mới Skills
```

---

# Cách kết nối Supabase với bot Python

Repo đã có:

```text
lib/db/
artifacts/api-server/
```

nhưng đó là code TypeScript/Drizzle và schema hiện đang rỗng.

Bot Python không nên phải gọi vòng qua Express API chỉ để đọc memory:

```text
Python bot → Express API → Postgres
```

Ở giai đoạn này, nên đơn giản hơn:

```text
Python bot → Supabase Postgres
TypeScript dashboard → cùng Supabase Postgres
```

Hai hệ thống dùng chung database.

Supabase cung cấp Postgres thật, Python client chính thức và nhiều kiểu kết nối. Với backend chạy liên tục, có thể dùng connection pool; tài liệu Supabase phân biệt direct connection, session pooler và transaction pooler theo môi trường ứng dụng. ([Supabase][3])

Cho repo này, tui nghiêng về:

```text
asyncpg
+
Supabase Session Pooler URL
+
một pool nhỏ
```

thay vì sử dụng SDK đồng bộ trong event loop của Discord.

---

# Những file dự kiến sẽ bị ảnh hưởng

Đây mới là thiết kế, tui chưa sửa file nào.

## File mới

```text
bot/core/database.py
```

Quản lý kết nối Postgres:

```text
init pool
close pool
execute query
fetch rows
health check
```

```text
bot/core/ai_memory.py
```

Quản lý:

```text
save_message()
get_recent_messages()
get_user_memories()
create_memory_candidate()
update_conversation_summary()
build_memory_context()
```

Một file migration, chọn một trong hai:

```text
supabase/migrations/001_ai_memory.sql
```

hoặc schema Drizzle:

```text
lib/db/src/schema/ai-memory.ts
```

Tui nghiêng về SQL migration làm nguồn chính vì bot là Python; dashboard TypeScript có thể ánh xạ các bảng đó sau.

## File sửa

```text
bot/core/config.py
```

Thêm:

```text
DATABASE_URL
AI_MEMORY_ENABLED
AI_HISTORY_RETENTION_DAYS
```

```text
bot/main.py
```

Mở database pool lúc startup và đóng khi bot shutdown.

```text
bot/cogs/chat_ai.py
```

Thay đổi lớn nhất:

* Lưu câu hỏi người dùng.
* Lấy conversation history từ database.
* Lưu câu trả lời assistant.
* Không dùng channel deque làm nguồn duy nhất.
* Không nhét tất cả role vào mọi prompt.
* Không ghi prompt chứa dữ liệu người dùng vào `debug_prompt.txt`.
* Thêm memory retrieval.
* Thêm summary khi conversation dài.

```text
requirements.txt
```

Thêm database driver và đồng thời nên dọn các dependency đang bị lặp hai lần.

---

# Một lỗi khác tôi phát hiện

Hiện `self.api_key` luôn được gán bằng:

```python
self.api_key = OPENROUTER_API_KEY
```

Sau đó trước khi xác định model Gemini hay OpenRouter, code kiểm tra:

```python
if not self.api_key:
    await message.reply("Tính năng AI đang bị tắt...")
    return
```

Điều này có nghĩa:

> Dù đã có `GEMINI_API_KEY`, bot vẫn không chạy Gemini nếu thiếu `OPENROUTER_API_KEY`.

Ngoài ra `_reload_config()` cũng chỉ tải system instruction khi OpenRouter key tồn tại.

Đây là lỗi logic độc lập với memory, nhưng nên sửa cùng đợt chỉnh `chat_ai.py`.

---

# Đánh giá cuối cùng

| Thành phần             |  Giữ hiện tại |       Chuyển Supabase |
| ---------------------- | ------------: | --------------------: |
| AI model config        |             ✅ |              Chưa cần |
| Siphoned points        |             ✅ |              Chưa cần |
| Last seen              |             ✅ |              Chưa cần |
| TTS config             |             ✅ |              Chưa cần |
| Recent RAM buffer      | Giữ làm cache | Không làm nguồn chính |
| AI messages            |             ❌ |                     ✅ |
| Conversation summaries |             ❌ |                     ✅ |
| User memories          |             ❌ |                     ✅ |
| Guild knowledge        |    Có thể sau |                     ✅ |
| Agent-created skills   |      Chưa làm |         Giai đoạn sau |

**Phương án phù hợp nhất với code hiện tại là Supabase/Postgres cho riêng AI memory, đồng thời giữ JSON cho các tính năng cũ.** Không cần MongoDB, không cần sao chép nguyên Hermes và cũng không nên chuyển toàn bộ dự án sang database trong một lần.

Tôi đã kiểm tra syntax Python và `compileall` chạy thành công. Bộ test không chạy được trong môi trường phân tích vì chưa cài package `discord.py`, không phải do test báo lỗi logic của repo.

**Bro chốt phương án “Supabase cho AI history + user memory, chưa làm auto-skill” chưa?**

[1]: https://render.com/docs/disks?utm_source=chatgpt.com "Persistent Disks – Render Docs"
[2]: https://supabase.com/docs/guides/database/full-text-search?utm_source=chatgpt.com "Full Text Search | Supabase Docs"
[3]: https://supabase.com/docs/guides/database/connecting-to-postgres?utm_source=chatgpt.com "Connect to your database | Supabase Docs"


# Nên chọn **Supabase**

Với bot Discord `Bot_Albion_TNC` của bạn, tôi khuyên dùng:

> **Supabase/PostgreSQL cho lịch sử chat, user memory, conversation summary và skill sau này.**

MongoDB vẫn làm được, nhưng không mang lại lợi thế rõ ràng cho cấu trúc dữ liệu của bot này.

## So sánh theo đúng nhu cầu bot

| Tiêu chí                    | Supabase                          | MongoDB Atlas                                   |
| --------------------------- | --------------------------------- | ----------------------------------------------- |
| Lưu Discord users           | Rất phù hợp                       | Phù hợp                                         |
| Conversation → messages     | Rất phù hợp với quan hệ SQL       | Phải quản lý reference giữa collections         |
| Memory theo user/guild      | Dễ lọc bằng SQL                   | Dễ lưu nhưng truy vấn quan hệ kém trực quan hơn |
| Tool logs, config linh hoạt | Có `JSONB`                        | Document rất linh hoạt                          |
| Dashboard xem/sửa dữ liệu   | Table Editor + SQL Editor         | Atlas Collections                               |
| Semantic search sau này     | `pgvector` cùng database          | Atlas Vector Search                             |
| Python bot trên Render      | Hỗ trợ Postgres connection/pooler | Driver Python tốt                               |
| Báo cáo, thống kê           | SQL rất thuận tiện                | Cần aggregation pipeline                        |
| Skill versioning            | Dễ dùng bảng quan hệ              | Làm được nhưng không tiện bằng SQL              |

Supabase cung cấp một PostgreSQL database đầy đủ, hỗ trợ foreign key, SQL, JSONB, connection pooling và extension `pgvector`; đây là tổ hợp rất phù hợp với ứng dụng AI có dữ liệu vừa quan hệ vừa linh hoạt. ([Supabase][1])

## Vì sao dữ liệu bot của bạn thiên về SQL?

Bot sẽ có cấu trúc như sau:

```text
Discord user
├── nhiều conversations
│   └── nhiều messages
├── nhiều memories
└── nhiều guild memberships

Conversation
├── nhiều messages
├── một summary
└── nhiều tool runs

Skill
└── nhiều skill versions
```

Đây là dữ liệu có quan hệ khá rõ ràng. PostgreSQL giúp bạn đặt:

* Foreign key.
* Unique constraint.
* Transaction.
* Cascade delete.
* Index kết hợp.
* Truy vấn thống kê bằng SQL.

Ví dụ:

```sql
select *
from ai_memories
where guild_id = $1
  and discord_user_id = $2
  and status = 'approved'
order by importance desc
limit 8;
```

Hoặc lấy lịch sử:

```sql
select role, content, created_at
from ai_messages
where conversation_id = $1
order by created_at desc
limit 20;
```

MongoDB cũng xử lý được, nhưng bạn sẽ phải tự duy trì reference giữa `users`, `conversations`, `messages`, `memories` và `skills`, hoặc nhúng quá nhiều dữ liệu vào document lớn.

## Khi nào MongoDB tốt hơn?

Nên chọn MongoDB khi:

* Bạn đã có kinh nghiệm MongoDB mạnh hơn PostgreSQL.
* Phần lớn dữ liệu là document độc lập.
* Schema thay đổi liên tục và gần như không có quan hệ.
* Bạn muốn lưu nguyên trạng các event hoặc payload lớn.
* Dự án hiện tại đã dùng MongoDB ở nhiều nơi.

Ví dụ MongoDB rất phù hợp với collection event:

```json
{
  "eventType": "discord_message",
  "payload": {
    "guildId": "...",
    "channelId": "...",
    "attachments": [],
    "embeds": []
  }
}
```

Nhưng bot của bạn không chỉ lưu event. Bạn còn cần truy vấn memory theo user, summary theo conversation, phiên bản skill, trạng thái duyệt và tool logs. Supabase cân bằng tốt hơn.

## Free tier hiện tại

Tính đến ngày 1 tháng 8 năm 2026:

* Supabase Free có **500 MB database**, 1 GB file storage và tối đa hai project hoạt động; project miễn phí có thể bị pause sau một tuần không hoạt động. ([Supabase][2])
* MongoDB Atlas M0 có khoảng **512 MB storage** và được mô tả là free forever. ([MongoDB][3])

Dung lượng miễn phí của hai bên gần tương đương. Với khoảng 100 người dùng, cả hai đều đủ để bắt đầu, nhưng bạn cần đặt retention cho message thay vì lưu mọi tin nhắn vô thời hạn.

Ví dụ:

```text
Tin nhắn thông thường: giữ 60–90 ngày
Tin nhắn gọi bot: giữ lâu hơn
Conversation summary: giữ lâu dài
User memory: giữ đến khi bị xóa hoặc hết hạn
Tool logs: giữ 30 ngày
```

## Cách kết nối phù hợp với bot Python trên Render

Tôi khuyên dùng:

```text
Discord.py bot
    ↓
asyncpg connection pool
    ↓
Supabase PostgreSQL
```

Không nhất thiết phải dùng Supabase Python SDK cho mọi query. Bot của bạn là một backend Python chạy lâu dài, nên kết nối PostgreSQL trực tiếp bằng `asyncpg` sẽ rõ ràng và dễ quản lý migration hơn.

Supabase có Shared Pooler ở session mode dành cho persistent backend chạy trên mạng IPv4; transaction mode phù hợp hơn với serverless hoặc tác vụ kết nối ngắn. ([Supabase][4])

Biến môi trường trên Render:

```env
DATABASE_URL=postgresql://postgres.project:password@region.pooler.supabase.com:5432/postgres
AI_MEMORY_ENABLED=true
AI_MESSAGE_RETENTION_DAYS=90
```

Sau đó:

```python
import asyncpg

pool = await asyncpg.create_pool(
    dsn=DATABASE_URL,
    min_size=1,
    max_size=5,
)
```

Với bot khoảng 100 người dùng, pool từ 2–5 connection là đủ để khởi đầu.

## Semantic search

Cả hai đều có vector search:

* Supabase sử dụng extension `pgvector`.
* MongoDB sử dụng Atlas Vector Search và có thể lưu embeddings cùng document. ([MongoDB][5])

Nhưng bot của bạn **chưa cần vector database ngay**.

Ban đầu hãy tìm memory theo:

```text
guild_id
discord_user_id
memory_type
importance
created_at
keyword
```

Khi số lượng memory và knowledge tăng đáng kể, thêm cột:

```sql
embedding vector(1536)
```

Supabase cho phép giữ relational data, JSONB và vector trong cùng PostgreSQL database, nên bạn không phải dựng thêm một database thứ hai. ([Supabase][6])

## Kiến trúc tôi chốt cho bot

```text
Render
└── Python Discord bot
    │
    ├── RAM deque
    │   └── cache tạm 10–20 tin nhắn
    │
    └── Supabase PostgreSQL
        ├── ai_conversations
        ├── ai_messages
        ├── ai_memories
        ├── ai_channel_settings
        ├── ai_tool_runs
        ├── ai_skills
        └── ai_skill_versions
```

Chưa cần chuyển toàn bộ JSON hiện tại vào Supabase. Bạn có thể tiếp tục dùng JSON cho Siphoned Points, TTS và config cũ, rồi dùng Supabase riêng cho AI memory.

## Quyết định cuối cùng

**Chọn Supabase.**

Lý do chính không phải Supabase mạnh hơn MongoDB trong mọi trường hợp, mà vì nó phù hợp hơn với bot của bạn:

* Cấu trúc dữ liệu có nhiều quan hệ.
* Dễ làm memory approval.
* Dễ versioning skill.
* Dễ thống kê và xóa dữ liệu theo người dùng.
* Có JSONB cho dữ liệu linh hoạt.
* Có `pgvector` khi cần AI retrieval.
* Dễ dùng chung với dashboard TypeScript sau này.
* Không phải thêm một vector database khác.

MongoDB chỉ nên được chọn nếu bạn đã quen MongoDB hơn đáng kể và muốn tối ưu tốc độ phát triển theo kỹ năng hiện có.

[1]: https://supabase.com/docs/guides/database/overview?utm_source=chatgpt.com "Database | Supabase Docs"
[2]: https://supabase.com/pricing?utm_source=chatgpt.com "Pricing & Fees | Supabase"
[3]: https://www.mongodb.com/products/platform/atlas-cloud-providers/aws/pricing?utm_source=chatgpt.com "AWS MongoDB Pricing | MongoDB"
[4]: https://supabase.com/docs/guides/database/connecting-to-postgres?utm_source=chatgpt.com "Connect to your database | Supabase Docs"
[5]: https://www.mongodb.com/docs/manual/reference/operator/aggregation/vectorsearch/?utm_source=chatgpt.com "$vectorSearch (aggregation stage) - Database Manual - MongoDB Docs"
[6]: https://supabase.com/docs/guides/database/extensions/pgvector?utm_source=chatgpt.com "pgvector: Embeddings and vector similarity | Supabase Docs"
