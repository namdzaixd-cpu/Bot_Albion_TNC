import re

path = 'bot/cogs/onboarding.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_setup_channels = """    @onboard_group.command(name="setup_channels", description="Cài đặt các kênh cần thiết để bot tag trong lời chào")
    @app_commands.describe(
        rules_id="Copy ID của Kênh Rules và dán vào đây",
        guild_chat_id="Copy ID của Kênh Guild-chat và dán vào đây",
        question_id="Copy ID của Kênh Hỏi đáp và dán vào đây"
    )
    async def onboard_setup_channels(self, interaction: discord.Interaction, 
                                     rules_id: str,
                                     guild_chat_id: str,
                                     question_id: str):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
        
        def extract_id(val: str):
            import re
            m = re.search(r'\d+', val)
            return m.group(0) if m else val.strip()

        self.config.data["rules_channel_id"] = extract_id(rules_id)
        self.config.data["chat_channel_id"] = extract_id(guild_chat_id)
        self.config.data["question_channel_id"] = extract_id(question_id)
        self.config.save()
        
        await interaction.response.send_message(
            f"✅ Đã lưu cấu hình kênh:\\n"
            f"- Rules: <#{self.config.data['rules_channel_id']}>\\n"
            f"- Chat: <#{self.config.data['chat_channel_id']}>\\n"
            f"- Q&A: <#{self.config.data['question_channel_id']}>", 
            ephemeral=True
        )"""

# Regex to find the setup_channels command block
content = re.sub(
    r'    @onboard_group\.command\(name="setup_channels".*?(?=    @|async def)',
    new_setup_channels + "\n\n",
    content,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated onboarding.py")
