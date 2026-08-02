import os
import re
import aiohttp
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from core.config import STORAGE_DIR
from core.storage import load_json, save_json
from core.permissions import is_officer

class OnboardConfig:
    def __init__(self):
        self.file_path = os.path.join(STORAGE_DIR, "tnc_onboarding.json")
        self.data = load_json(self.file_path, dict)
        
    def save(self):
        save_json(self.data, self.file_path)

    @property
    def is_enabled(self):
        return self.data.get("is_enabled", True)
        
    @is_enabled.setter
    def is_enabled(self, value: bool):
        self.data["is_enabled"] = value
        self.save()

    @property
    def apply_channel_id(self):
        return self.data.get("apply_channel_id")
        
    @property
    def member_role_id(self):
        return self.data.get("member_role_id")
        
    @property
    def officer_role_id(self):
        return self.data.get("officer_role_id")
        
    @property
    def rules_channel_id(self):
        return self.data.get("rules_channel_id")
        
    @property
    def chat_channel_id(self):
        return self.data.get("chat_channel_id")
        
    @property
    def question_channel_id(self):
        return self.data.get("question_channel_id")


class OfficerApprovalView(discord.ui.View):
    def __init__(self, cog: 'Onboarding', target_user_id: int, ign_name: str, yob: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_user_id = target_user_id
        self.ign_name = ign_name
        self.yob = yob

    @discord.ui.button(label="Duyệt Đơn", style=discord.ButtonStyle.green, custom_id="onboard_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(self.target_user_id)
        if member:
            formatted_yob = self.yob
            if formatted_yob.isdigit():
                if len(formatted_yob) == 4:
                    if formatted_yob.startswith("20"):
                        formatted_yob = f"2k{formatted_yob[3:]}" if formatted_yob[3:] != "0" else "2k"
                    elif formatted_yob.startswith("19"):
                        formatted_yob = formatted_yob[2:]
            
            new_nick = f"[TNC] {self.ign_name} {formatted_yob}".strip()
            if len(new_nick) > 32:
                new_nick = new_nick[:32]
                
            try:
                await member.edit(nick=new_nick)
            except discord.Forbidden:
                pass
                
            role_id = self.cog.config.member_role_id
            if role_id:
                role = guild.get_role(int(role_id))
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass
        
        for child in self.children:
            child.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = f"✅ Đã duyệt: {self.ign_name}"
        embed.set_footer(text=f"Duyệt bởi {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)
        
        c_rules = f"<#{self.cog.config.rules_channel_id}>" if self.cog.config.rules_channel_id else "Kênh Rules"
        c_chat = f"<#{self.cog.config.chat_channel_id}>" if self.cog.config.chat_channel_id else "Kênh Guild-chat"
        c_question = f"<#{self.cog.config.question_channel_id}>" if self.cog.config.question_channel_id else "Kênh Hỏi đáp"
        
        welcome_msg = (
            f"🎉 Chào mừng <@{self.target_user_id}> đã gia nhập TNC! (Bot đã tự động đổi tên Discord giúp bạn).\n\n"
            f"🔹 Hãy đọc thật kỹ {c_rules} để nắm rõ các quy định và văn hóa hoạt động của guild.\n"
            f"🔹 Ghé qua {c_chat} để đàm đạo, chém gió và giao lưu cùng anh em.\n"
            f"🔹 Bất cứ khi nào có thắc mắc hay cần hỗ trợ gì về game, bro cứ hét thẳng vào {c_question} nhé, mọi người sẽ giải đáp nhiệt tình.\n\n"
            f"Khi vào guild hãy cư xử đúng mực, kính trên nhường dưới, không toxic và không gây war nha.\n"
            f"Chúc bro chơi game vui vẻ ❤️"
        )
        await interaction.channel.send(welcome_msg)

    @discord.ui.button(label="Từ chối", style=discord.ButtonStyle.red, custom_id="onboard_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = f"❌ Đã từ chối: {self.ign_name}"
        embed.set_footer(text=f"Từ chối bởi {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)


class ApplicantConfirmView(discord.ui.View):
    def __init__(self, cog: 'Onboarding', target_user_id: int, ign_name: str, yob: str, embed: discord.Embed):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_user_id = target_user_id
        self.ign_name = ign_name
        self.yob = yob
        self.embed = embed

    @discord.ui.button(label="Đã gửi apply ingame", style=discord.ButtonStyle.green, custom_id="onboard_applicant_done")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        officer_mention = f"<@&{self.cog.config.officer_role_id}>" if self.cog.config.officer_role_id else "@Officer"
        msg_text = f"✅ Thành viên mới đã xác nhận nộp đơn ingame. Mời {officer_mention} vào xem xét duyệt nhé!"
        
        view = OfficerApprovalView(self.cog, self.target_user_id, self.ign_name, self.yob)
        await interaction.message.edit(content=msg_text, embed=self.embed, view=view)

    @discord.ui.button(label="Chưa gửi apply ingame", style=discord.ButtonStyle.secondary, custom_id="onboard_applicant_not_done")
    async def not_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người nộp đơn!", ephemeral=True)
            return
            
        await interaction.response.send_message("⚠️ Bạn vui lòng vào game, tìm guild **The Northern Constellations** và nộp đơn apply. Sau khi apply xong thì quay lại đây bấm nút **Đã gửi apply ingame** nhé!", ephemeral=True)


class Onboarding(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = OnboardConfig()

    async def fetch_albion_player(self, ign: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/search?q={ign}") as resp:
                    if resp.status != 200: return None
                    data = await resp.json()
                    players = data.get("players", [])
                    if not players: return None
                    
                    player = next((p for p in players if p["Name"].lower() == ign.lower()), None)
                    if not player: return None
                    player_id = player["Id"]
                
                async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/players/{player_id}") as resp:
                    if resp.status != 200: return None
                    return await resp.json()
        except Exception:
            return None

    def validate_form(self, content: str):
        keywords = ["ingame", "năm sinh", "giới tính", "quốc gia", "thời gian", "mic", "chơi pc", "mobile", "role", "guild", "mục đích", "quy định"]
        count = sum(1 for kw in keywords if kw in content.lower())
        return count >= 4  

    async def process_apply_thread(self, thread: discord.Thread, msg: discord.Message = None):
        try:
            if not msg:
                try:
                    async for m in thread.history(limit=5, oldest_first=True):
                        if m.author.id == thread.owner_id:
                            msg = m
                            break
                except discord.Forbidden:
                    print(f"❌ LỖI QUYỀN: Bot không có quyền 'Đọc Lịch sử Tin nhắn' trong kênh {thread.parent.name}")
                    return
                    
            if not msg:
                return
                
            content = msg.content
            
            ign_match = re.search(r'Ingame\s*[:\-]?\s*([a-zA-Z0-9_]+)', content, re.IGNORECASE)
            yob_match = re.search(r'Năm sinh\s*[:\-]?\s*([a-zA-Z0-9]+)', content, re.IGNORECASE)
            
            if not ign_match:
                if not self.validate_form(content): return 
                await thread.send("⚠️ Bot không tìm thấy mục `Ingame:` trong đơn. Hãy viết rõ form `Ingame : Tên` nhé!")
                return
                
            if not self.validate_form(content):
                await thread.send("⚠️ Bro điền thiếu form rồi kìa, hãy điền đầy đủ form mẫu nhé!")
                return
                
            has_image = False
            if msg.attachments:
                for att in msg.attachments:
                    if att.content_type and att.content_type.startswith("image/"):
                        has_image = True
                        break
            if "http" in content.lower() and ("png" in content.lower() or "jpg" in content.lower() or "jpeg" in content.lower() or "discord" in content.lower()):
                has_image = True
                
            if not has_image:
                try:
                    async for m in thread.history(limit=10, oldest_first=True):
                        if m.author.id == thread.owner_id and (m.attachments or "http" in m.content):
                            has_image = True
                            break
                except discord.Forbidden:
                    print(f"❌ LỖI QUYỀN: Bot không có quyền 'Đọc Lịch sử Tin nhắn' trong kênh {thread.parent.name}")
                    return
    
            if not has_image:
                # Check if bot already asked for image to prevent spamming
                already_asked = False
                try:
                    async for m in thread.history(limit=10, oldest_first=True):
                        if m.author == self.bot.user and "xin thêm ảnh stat" in m.content.lower():
                            already_asked = True
                            break
                except discord.Forbidden:
                    pass
                
                if not already_asked:
                    try:
                        await thread.send("Bro ơi cho tui xin thêm ảnh stat ingame nhé.")
                    except discord.Forbidden:
                        print(f"❌ LỖI QUYỀN: Bot không có quyền 'Gửi Tin nhắn trong Chuỗi' ở kênh {thread.parent.name}")
                return
                
            ign = ign_match.group(1).strip()
            yob = yob_match.group(1).strip() if yob_match else ""

            api_data = await self.fetch_albion_player(ign)
            if not api_data:
                await thread.send(f"❌ Không tìm thấy nhân vật `{ign}` trên hệ thống Albion. Officer vui lòng kiểm tra thủ công.")
                return
                
            embed = discord.Embed(title=f"Báo cáo tự động: {api_data.get('Name')}", color=discord.Color.blue())
            
            fame_total = api_data.get('LifetimeStatistics', {}).get('PvE', {}).get('Total', 0)
            kill_fame = api_data.get('KillFame', 0)
            death_fame = api_data.get('DeathFame', 0)
            
            embed.add_field(name="PvE Fame", value=f"{fame_total:,}", inline=True)
            embed.add_field(name="Kill Fame", value=f"{kill_fame:,}", inline=True)
            embed.add_field(name="Death Fame", value=f"{death_fame:,}", inline=True)
            
            old_guild = api_data.get('GuildName', 'Không có')
            embed.add_field(name="Guild Hiện Tại / Cũ", value=old_guild, inline=False)
            
            view = ApplicantConfirmView(self, thread.owner_id, api_data.get('Name'), yob, embed)
            
            msg_text = (
                f"👉 **<@{thread.owner_id}>: Vui lòng nộp đơn (apply) vào guild `The Northern Constellations` trong game.**\n"
                f"Sau khi nộp xong ingame, hãy bấm nút **Đã gửi apply ingame** bên dưới để gọi Officer vào duyệt nhé!"
            )
            await thread.send(content=msg_text, embed=embed, view=view)
        except Exception as e:
            print(f"❌ LỖI Onboarding: {e}")


    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not self.config.is_enabled: return
        apply_ch = self.config.apply_channel_id
        if not apply_ch or str(thread.parent_id) != str(apply_ch):
            return
            
        await asyncio.sleep(2)
        await self.process_apply_thread(thread)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.config.is_enabled: return
        if message.author.bot: return
        if not isinstance(message.channel, discord.Thread): return
        
        apply_ch = self.config.apply_channel_id
        if not apply_ch or str(message.channel.parent_id) != str(apply_ch):
            return
            
        print(f"DEBUG Onboarding: Nhận tin nhắn trong kênh apply {message.channel.name}")
        
        if message.author.id != message.channel.owner_id:
            print("DEBUG Onboarding: Người gửi không phải chủ thread, bỏ qua.")
            return
            
        # Nếu đây là tin nhắn gốc (starter message) của Thread, xử lý luôn
        if message.id == message.channel.id:
            print("DEBUG Onboarding: Tin nhắn gốc của Forum, xử lý process_apply_thread.")
            await self.process_apply_thread(message.channel, msg=message)
            return
            
        async for m in message.channel.history(limit=20):
            if m.author == self.bot.user and m.embeds and "Báo cáo tự động" in str(m.embeds[0].title):
                return
                
        if message.attachments or "http" in message.content:
            await self.process_apply_thread(message.channel)


    onboard_group = app_commands.Group(name="onboard", description="Hệ thống Bot Thư Ký duyệt đơn")

    @onboard_group.command(name="toggle", description="Bật/Tắt chế độ Thư Ký tự động")
    async def onboard_toggle(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Chỉ Ban quản trị mới được dùng!", ephemeral=True)
            return
        self.config.is_enabled = not self.config.is_enabled
        status = "BẬT" if self.config.is_enabled else "TẮT"
        await interaction.response.send_message(f"✅ Đã **{status}** tính năng tự động check đơn thành viên mới.", ephemeral=True)

    @onboard_group.command(name="set_apply_channel", description="Chỉ định kênh Forum dùng để nộp đơn")
    async def onboard_set_apply_channel(self, interaction: discord.Interaction, apply: discord.abc.GuildChannel):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
        
        self.config.data["apply_channel_id"] = str(apply.id)
        self.config.save()
        await interaction.response.send_message(f"✅ Đã chỉ định kênh Apply thành công: <#{apply.id}>", ephemeral=True)

    @onboard_group.command(name="setup_channels", description="Cài đặt các kênh cần thiết để bot tag trong lời chào")
    async def onboard_setup_channels(self, interaction: discord.Interaction, 
                                     rules: discord.TextChannel,
                                     guild_chat: discord.TextChannel,
                                     question: discord.TextChannel):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
        
        self.config.data["rules_channel_id"] = str(rules.id)
        self.config.data["chat_channel_id"] = str(guild_chat.id)
        self.config.data["question_channel_id"] = str(question.id)
        self.config.save()
        await interaction.response.send_message("✅ Đã lưu cấu hình 3 kênh thành công!", ephemeral=True)

    @onboard_group.command(name="setup_roles", description="Cài đặt Role Officer và Role Member")
    async def onboard_setup_roles(self, interaction: discord.Interaction, 
                                  officer_role: discord.Role,
                                  member_role: discord.Role):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
        
        self.config.data["officer_role_id"] = str(officer_role.id)
        self.config.data["member_role_id"] = str(member_role.id)
        self.config.save()
        await interaction.response.send_message(f"✅ Đã lưu cấu hình Role!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
