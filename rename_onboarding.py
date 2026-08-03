import os
path = r'bot/cogs/onboarding.py'
with open(path, 'r', encoding='utf-8') as f: content = f.read()

# Add os import if missing
if 'import os' not in content:
    content = 'import os\n' + content

# Add GUILD_NAME and GUILD_TAG defaults
if 'GUILD_NAME' not in content:
    content = content.replace('class OnboardingState:', 'GUILD_NAME = os.getenv("DEFAULT_GUILD_NAME", "The Northern Constellations")\nGUILD_TAG = os.getenv("DEFAULT_GUILD_TAG", "TNC")\n\nclass OnboardingState:')

# Replace strings
content = content.replace('gia nhập TNC!\\n\\n', 'gia nhập {GUILD_TAG}!\\n\\n')
content = content.replace('[TNC] {self.ign_name}', '[{GUILD_TAG}] {self.ign_name}')
content = content.replace('guild **The Northern Constellations** và nộp đơn', 'guild **{GUILD_NAME}** và nộp đơn')
content = content.replace('guild `The Northern Constellations` trong game', 'guild `{GUILD_NAME}` trong game')

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print('Done onboarding.py')
