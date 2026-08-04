import discord
from core.config import GUILD_NAME, GUILD_TAG

def get_onboard_data(interaction: discord.Interaction):
    thread = interaction.message.channel
    target_user_id = thread.owner_id
    embed = interaction.message.embeds[0]
    title = embed.title
    if ":" in title:
        ign_name = title.split(":", 1)[1].strip()
    else:
        ign_name = title
        
    footer = embed.footer.text if embed.footer else ""
    yob = ""
    if footer and "YOB:" in footer:
        parts = footer.split("|")
        for part in parts:
            if "YOB:" in part:
                yob = part.split("YOB:")[1].strip()
    return target_user_id, ign_name, yob, embed

class RulesConfirmView(discord.ui.View):
    def __init__(self, cog: 'Onboarding'):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Tôi đã đọc & Đồng ý Nội Quy", style=discord.ButtonStyle.primary, custom_id="onboard_rules_read")
    async def confirm_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        if interaction.user.id != target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        msg_text = (
            f"👉 **<@{target_user_id}>: Vui lòng nộp đơn (apply) vào guild `{GUILD_NAME}` trong game.**\n"
            f"Sau khi nộp xong ingame, hãy bấm nút **Đã gửi apply ingame** bên dưới để gọi Officer vào duyệt nhé!"
        )
        
        view = ApplicantConfirmView(self.cog)
        await interaction.message.edit(content=msg_text, embed=embed, view=view)

class ApplicantConfirmView(discord.ui.View):
    def __init__(self, cog: 'Onboarding'):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Đã gửi apply ingame", style=discord.ButtonStyle.green, custom_id="onboard_applicant_done")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        if interaction.user.id != target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        officer_mention = f"<@&{self.cog.config.officer_role_id}>" if self.cog.config.officer_role_id else "@Officer"
        msg_text = (
            f"✅ Thành viên mới đã xác nhận nộp đơn ingame. Mời {officer_mention} vào xem xét duyệt nhé!\n"
            "⚠️ **Lưu ý:** Thành viên đã xác nhận gửi apply ingame, Officer vui lòng kiểm tra mail apply và duyệt mail ingame trước khi bấm nút Accept"
        )
        
        view = OfficerApprovalView(self.cog)
        await interaction.message.edit(content=msg_text, embed=embed, view=view)

    @discord.ui.button(label="Chưa gửi apply ingame", style=discord.ButtonStyle.secondary, custom_id="onboard_applicant_not_done")
    async def not_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        if interaction.user.id != target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.send_message(f"⚠️ Bạn vui lòng vào game, tìm guild **{GUILD_NAME}** và nộp đơn apply. Sau khi apply xong thì quay lại đây bấm nút **Đã gửi apply ingame** nhé!", ephemeral=False)

class OfficerApprovalView(discord.ui.View):
    def __init__(self, cog: 'Onboarding'):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="onboard_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        from core.permissions import is_officer
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        guild = interaction.guild
        member = guild.get_member(target_user_id)
        if member:
            role_id = self.cog.config.member_role_id
            if not role_id:
                await interaction.followup.send("⚠️ Cảnh báo: Chưa cài đặt Member Role nên bot không thể cấp role. Dùng `/recuibot setup_roles` để cài!", ephemeral=False)
            else:
                role = guild.get_role(int(role_id))
                if not role:
                    await interaction.followup.send("⚠️ Cảnh báo: Role ID đã lưu không tồn tại (có thể role đã bị xóa). Dùng `/recuibot setup_roles` để cài lại!", ephemeral=False)
                else:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        await interaction.followup.send("⚠️ Cảnh báo: Bot không có quyền cấp Role này (Role của bot đang đứng thấp hơn Role cần cấp, hoặc bot thiếu quyền Manage Roles)!", ephemeral=False)
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Cảnh báo: Lỗi khi cấp role: {e}", ephemeral=False)
        else:
            await interaction.followup.send("⚠️ Cảnh báo: Không tìm thấy thành viên này trong server (có thể họ đã out).", ephemeral=False)
        
        for child in self.children:
            if child.custom_id in ["onboard_approve", "onboard_reject"]:
                child.disabled = True
            
        embed.color = discord.Color.green()
        embed.title = f"✅ Đã duyệt: {ign_name}"
        embed.set_footer(text=f"YOB: {yob} | Duyệt bởi {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)
        
        c_rules = f"<#{self.cog.config.rules_channel_id}>" if self.cog.config.rules_channel_id else "Kênh Rules"
        c_chat = f"<#{self.cog.config.chat_channel_id}>" if self.cog.config.chat_channel_id else "Kênh Guild-chat"
        c_question = f"<#{self.cog.config.question_channel_id}>" if self.cog.config.question_channel_id else "Kênh Hỏi đáp"
        
        welcome_msg = (
            f"🎉 Chào mừng <@{target_user_id}> đã gia nhập {GUILD_TAG}!\n\n"
            f"🔹 Ghé qua {c_chat} để đàm đạo, chém gió và giao lưu cùng anh em.\n"
            f"🔹 Bất cứ khi nào có thắc mắc hay cần hỗ trợ gì về game, bro cứ hét thẳng vào {c_question} nhé, mọi người sẽ giải đáp nhiệt tình.\n\n"
            f"Khi vào guild hãy cư xử đúng mực, kính trên nhường dưới, không toxic và không gây war nha.\n"
            f"Chúc bro chơi game vui vẻ ❤️"
        )
        await interaction.channel.send(welcome_msg)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary, custom_id="onboard_rename")
    async def rename_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        from core.permissions import is_officer
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được dùng!", ephemeral=True)
            return
            
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        guild = interaction.guild
        member = guild.get_member(target_user_id)
        if not member:
            await interaction.response.send_message("❌ Không tìm thấy user này trong server (có thể họ đã out).", ephemeral=True)
            return
            
        formatted_yob = yob
        if formatted_yob.isdigit():
            if len(formatted_yob) == 4:
                if formatted_yob.startswith("20"):
                    formatted_yob = f"2k{formatted_yob[3:]}" if formatted_yob[3:] != "0" else "2k"
                elif formatted_yob.startswith("19"):
                    formatted_yob = formatted_yob[2:]
        
        new_nick = f"[{GUILD_TAG}] {ign_name} {formatted_yob}".strip()
        if len(new_nick) > 32:
            new_nick = new_nick[:32]
            
        try:
            await member.edit(nick=new_nick)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ Đã tự động đổi tên thành `{new_nick}`!", ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Lỗi quyền: Bot không có quyền đổi tên user này (có thể role của họ cao hơn bot hoặc bot chưa có quyền Manage Nicknames).", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"❌ Có lỗi xảy ra: {e}", ephemeral=False)

    @discord.ui.button(label="Từ chối", style=discord.ButtonStyle.red, custom_id="onboard_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        from core.permissions import is_officer
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        target_user_id, ign_name, yob, embed = get_onboard_data(interaction)
        for child in self.children:
            child.disabled = True
            
        embed.color = discord.Color.red()
        embed.title = f"❌ Đã từ chối: {ign_name}"
        embed.set_footer(text=f"YOB: {yob} | Từ chối bởi {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)
