with open('bot/cogs/guildcheck.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('\\"\\"\\"Chạy toàn bộ logic check. Trả về (removed_list, error_msg).\\"\\"\\"', '\"\"\"Chạy toàn bộ logic check. Trả về (removed_list, error_msg).\"\"\"')
with open('bot/cogs/guildcheck.py', 'w', encoding='utf-8') as f: f.write(content)
print("Done fix")
