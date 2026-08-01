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
    def apply_channel_id(self):
        return self.data.get("apply_channel_id")
        
    @property
    def member_role_id(self):
        return self.data.get("member_role_id")

class OfficerApprovalView(discord.ui.View):
    def __init__(self, target_user_id: int, ign_name: str, yob: str, role_id: str):
        super().__init__(timeout=None)
        self.target_user_id = target_user_id
        self.ign_name = ign_name
        self.yob = yob
        self.role_id = role_id

    @discord.ui.button(label="Duyệt Lính", style=discord.ButtonStyle.green, custom_id="onboard_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        guild = interaction.guild
        member = guild.get_member(self.target_user_id)
        if member:
            # Format nickname
            # Ví dụ: '2000' -> '2k', '1999' -> '99'
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
                pass # Can't edit owner/admin
                
            if self.role_id:
                role = guild.get_role(int(self.role_id))
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass
        
        # Lock buttons
        for child in self.children:
            child.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = f"✅ Đã duyệt: {self.ign_name}"
        embed.set_footer(text=f"Duyệt bởi {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)
        
        # Post the specific welcome message in the thread
        welcome_msg = (
            f"-Id Discord: <@{self.target_user_id}>\n"
            f"Hãy đọc thật kỹ 《📋》𝐑𝐮𝐥𝐞𝐬 trước khi quyết định apply nhé.\n"
            f"Nếu đã sẵn sàng, hãy đổi tên ở server Discord TNC theo form: \" [TNC] Ingame Tuổi \" (Bot đã tự đổi giúp bạn).\n"
            f"Apply vào guild The Northern Constellations trong game và đợi một lát để được duyệt.\n"
            f"Sau khi vào guild, ghé 〔📰〕ᴄᴏɴᴛᴇɴᴛꜱ-ping🚩 để tham gia content cùng mọi người nhé.\n"
            f"Có thắc mắc gì về game thì vào 🤔nghìn-lẻ-một-câu-hỏi-vì-sao🤔 hỏi, anh em sẽ giải đáp cho.\n"
            f"Khi vào guild hãy cư xử đúng mực, kính trên nhường dưới, không toxic không gây war nhaa.\n"
            f"Chúc bạn một ngày vui vẻ ❤️"
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
        except:
            return None

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        apply_ch = self.config.apply_channel_id
        if not apply_ch or str(thread.parent_id) != str(apply_ch):
            return
            
        # Nghỉ 2 giây để Discord post xong message đầu tiên vào thread
        await asyncio.sleep(2)
        
        # Fetch the first message of the thread
        initial_msg = None
        async for msg in thread.history(limit=5, oldest_first=True):
            if msg.author.id == thread.owner_id:
                initial_msg = msg
                break
                
        if not initial_msg:
            return
            
        content = initial_msg.content
        
        # Extract Ingame and Năm sinh
        ign_match = re.search(r'Ingame\s*:\s*(.+)', content, re.IGNORECASE)
        yob_match = re.search(r'Năm sinh\s*:\s*(.+)', content, re.IGNORECASE)
        
        if not ign_match:
            await thread.send("⚠️ Bot không tìm thấy mục `Ingame:` trong form của bạn. Vui lòng tạo đúng mẫu để tự động tra cứu!")
            return
            
        ign = ign_match.group(1).strip()
        yob = yob_match.group(1).strip() if yob_match else ""
        
        # Gọi API kiểm tra
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
        
        view = OfficerApprovalView(thread.owner_id, api_data.get('Name'), yob, self.config.member_role_id)
        await thread.send(embed=embed, view=view)


    onboard_group = app_commands.Group(name="onboard", description="Cài đặt tính năng tự động lọc lính mới qua Diễn đàn")

    @onboard_group.command(name="set_apply_channel", description="Cài đặt kênh Diễn đàn (Forum) dùng để Nộp đơn")
    @app_commands.describe(channel="Chọn kênh diễn đàn (Apply channel)")
    async def onboard_set_apply_channel(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        self.config.data["apply_channel_id"] = str(channel.id)
        self.config.save()
        await interaction.response.send_message(f"✅ Đã đặt kênh diễn đàn {channel.mention} làm nơi Bot túc trực đọc đơn lính mới.", ephemeral=True)

    @onboard_group.command(name="set_role", description="Cài đặt Role sẽ được tự động cấp sau khi duyệt")
    @app_commands.describe(role="Chọn Role Thành viên chính thức")
    async def onboard_set_role(self, interaction: discord.Interaction, role: discord.Role):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        self.config.data["member_role_id"] = str(role.id)
        self.config.save()
        await interaction.response.send_message(f"✅ Đã cài đặt tự động cấp role `{role.name}` cho lính mới sau khi duyệt.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
