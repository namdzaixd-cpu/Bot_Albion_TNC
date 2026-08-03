import os
path = r'bot/cogs/guildcheck.py'
with open(path, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('name="registertnc"', 'name="register_albion"')
content = content.replace('def registertnc_cmd', 'def register_albion_cmd')
content = content.replace('/registertnc', '/register_albion')
with open(path, 'w', encoding='utf-8') as f: f.write(content)
print('Done guildcheck.py')
