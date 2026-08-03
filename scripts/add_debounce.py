import os, re
path = r'bot/cogs/onboarding.py'
with open(path, 'r', encoding='utf-8') as f: content = f.read()

def add_processing(view_name, content):
    init_str = f"class {view_name}(discord.ui.View):\n    def __init__"
    if init_str in content:
        # find the end of the init
        idx = content.find(':', content.find(init_str)) + 1
        content = content[:idx] + "\n        self.is_processing = False" + content[idx:]
    return content

content = add_processing('OfficerApprovalView', content)
content = add_processing('IngameApplyView', content)
content = add_processing('OnboardingView', content)

# For approve
approve_search = 'async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):'
approve_replace = approve_search + '\n        if self.is_processing: return\n        self.is_processing = True'
content = content.replace(approve_search, approve_replace)

# For reject
reject_search = 'async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):'
reject_replace = reject_search + '\n        if self.is_processing: return\n        self.is_processing = True'
content = content.replace(reject_search, reject_replace)

# For confirm
confirm_search = 'async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):'
confirm_replace = confirm_search + '\n        if getattr(self, "is_processing", False): return\n        self.is_processing = True'
content = content.replace(confirm_search, confirm_replace)

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print('Done add_debounce')
