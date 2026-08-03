import re

path = 'bot/cogs/onboarding.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update OfficerApprovalView.approve welcome_msg
old_welcome = '''        welcome_msg = (
            f"🎉 Chào mừng <@{self.target_user_id}> đã gia nhập {GUILD_TAG}!\\n\\n"
            f"🔹 Hãy đọc thật kỹ {c_rules} để nắm rõ các quy định và văn hóa hoạt động của guild.\\n"
            f"🔹 Ghé qua {c_chat} để đàm đạo, chém gió và giao lưu cùng anh em.\\n"
            f"🔹 Bất cứ khi nào có thắc mắc hay cần hỗ trợ gì về game, bro cứ hét thẳng vào {c_question} nhé, mọi người sẽ giải đáp nhiệt tình.\\n\\n"
            f"Khi vào guild hãy cư xử đúng mực, kính trên nhường dưới, không toxic và không gây war nha.\\n"
            f"Chúc bro chơi game vui vẻ ❤️"
        )'''

new_welcome = '''        welcome_msg = (
            f"🎉 Chào mừng <@{self.target_user_id}> đã gia nhập {GUILD_TAG}!\\n\\n"
            f"🔹 Ghé qua {c_chat} để đàm đạo, chém gió và giao lưu cùng anh em.\\n"
            f"🔹 Bất cứ khi nào có thắc mắc hay cần hỗ trợ gì về game, bro cứ hét thẳng vào {c_question} nhé, mọi người sẽ giải đáp nhiệt tình.\\n\\n"
            f"Khi vào guild hãy cư xử đúng mực, kính trên nhường dưới, không toxic và không gây war nha.\\n"
            f"Chúc bro chơi game vui vẻ ❤️"
        )'''

if old_welcome in content:
    content = content.replace(old_welcome, new_welcome)
else:
    print("WARNING: Could not find old_welcome")

# 2. Add RulesConfirmView
rules_confirm_view = '''
class RulesConfirmView(discord.ui.View):
    def __init__(self, cog: 'Onboarding', target_user_id: int, ign_name: str, yob: str, embed: discord.Embed):
        super().__init__(timeout=None)
        self.is_processing = False
        self.cog = cog
        self.target_user_id = target_user_id
        self.ign_name = ign_name
        self.yob = yob
        self.embed = embed

    @discord.ui.button(label="Tôi đã đọc & Đồng ý Nội Quy", style=discord.ButtonStyle.primary, custom_id="onboard_rules_read")
    async def confirm_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        if getattr(self, "is_processing", False): return
        self.is_processing = True
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        msg_text = (
            f"👉 **<@{self.target_user_id}>: Vui lòng nộp đơn (apply) vào guild `{GUILD_NAME}` trong game.**\\n"
            f"Sau khi nộp xong ingame, hãy bấm nút **Đã gửi apply ingame** bên dưới để gọi Officer vào duyệt nhé!"
        )
        
        view = ApplicantConfirmView(self.cog, self.target_user_id, self.ign_name, self.yob, self.embed)
        await interaction.message.edit(content=msg_text, embed=self.embed, view=view)

class ApplicantConfirmView(discord.ui.View):'''

if 'class ApplicantConfirmView(discord.ui.View):' in content:
    content = content.replace('class ApplicantConfirmView(discord.ui.View):', rules_confirm_view)
else:
    print("WARNING: Could not find ApplicantConfirmView")

# 3. Update process_apply_thread to use RulesConfirmView
old_process = '''            view = ApplicantConfirmView(self, thread.owner_id, api_data.get('Name'), yob, embed)
            
            msg_text = (
                f"👉 **<@{thread.owner_id}>: Vui lòng nộp đơn (apply) vào guild `{GUILD_NAME}` trong game.**\\n"
                f"Sau khi nộp xong ingame, hãy bấm nút **Đã gửi apply ingame** bên dưới để gọi Officer vào duyệt nhé!"
            )
            await thread.send(content=msg_text, embed=embed, view=view)'''

new_process = '''            view = RulesConfirmView(self, thread.owner_id, api_data.get('Name'), yob, embed)
            
            rules_channel = f"<#{self.config.rules_channel_id}>" if self.config.rules_channel_id else "Kênh Rules"
            msg_text = (
                f"⚠️ **<@{thread.owner_id}>: Vui lòng đọc thật kỹ nội quy tại {rules_channel} trước khi nộp đơn.**\\n"
                f"Sau khi đã đọc và hiểu rõ nội quy, hãy bấm nút xác nhận bên dưới (Bắt buộc)."
            )
            await thread.send(content=msg_text, embed=embed, view=view)'''

if old_process in content:
    content = content.replace(old_process, new_process)
else:
    print("WARNING: Could not find old_process")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated onboarding flow")
