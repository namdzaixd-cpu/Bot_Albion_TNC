import re
path = 'bot/cogs/about.py'
with open(path, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('"**Lệnh Guild (Sĩ Quan)**\\n"\n        "`/massing` (quản lý Massing)\\n"\n        "`/guildconfig` (cấu hình GuildCheck — Officer)\\n"\n        "`/guildcheck` (check tay rời guild — Officer)\\n"\n        "`/unresolved` (xem danh sách chưa xác định — Officer)",', '"🛡️ GuildCheck",\n        "`/guildconfig` (cấu hình GuildCheck — Officer)\\n"\n        "`/guildcheck` (check tay rời guild — Officer)\\n"\n        "`/unresolved` (xem danh sách chưa xác định — Officer)",')
with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Done fix about")
