import os
import aiohttp
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
    def welcome_channel_id(self):
        return self.data.get("welcome_channel_id")
        
    @property
    def officer_channel_id(self):
        return self.data.get("officer_channel_id")
        
    @property
    def member_role_id(self):
        return self.data.get("member_role_id")


class OnboardingModal(discord.ui.Modal, title='Khai báo In-Game Name (IGN)'):
    ign = discord.ui.TextInput(
        label='Tên nhân vật trong Albion Online',
        style=discord.TextStyle.short,
        placeholder='Nhập chính xác tên nhân vật của bạn...',
        required=True,
        min_length=2,
        max_length=20
    )
    
    weapon = discord.ui.TextInput(
        label='Main Vũ Khí / Cấp độ',
        style=discord.TextStyle.short,
        placeholder='Ví dụ: Búa, Cung... / Mới chơi',
        required=False,
        max_length=50
    )

    def __init__(self, cog: 'Onboarding'):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ign_name = self.ign.value.strip()
        weapon_main = self.weapon.value.strip() or "Không rõ"
        
        # Gọi Albion API để lấy thông tin
        api_data = await self.cog.fetch_albion_player(ign_name)
        if not api_data:
            await interaction.followup.send(f"❌ Không tìm thấy nhân vật `{ign_name}` trên hệ thống Albion. Vui lòng kiểm tra lại tên (phân biệt hoa thường, ký tự) hoặc API Albion đang bảo trì!", ephemeral=True)
            return
            
        # Gửi thông tin sang kênh Officer
        officer_channel_id = self.cog.config.officer_channel_id
        if not officer_channel_id:
            await interaction.followup.send("⚠️ Bot chưa được cài đặt kênh Officer để gửi form. Hãy báo cho Admin!", ephemeral=True)
            return
            
        guild = interaction.guild
        officer_channel = guild.get_channel(int(officer_channel_id))
        if not officer_channel:
            await interaction.followup.send("⚠️ Không tìm thấy kênh Officer. Hãy báo cho Admin!", ephemeral=True)
            return
            
        embed = discord.Embed(title=f"📝 Đơn đăng ký mới: {ign_name}", color=discord.Color.blue())
        embed.add_field(name="Người dùng Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Tên In-game (IGN)", value=f"**{api_data.get('Name')}**", inline=True)
        embed.add_field(name="Main Vũ Khí", value=weapon_main, inline=True)
        
        fame_total = api_data.get('LifetimeStatistics', {}).get('PvE', {}).get('Total', 0)
        kill_fame = api_data.get('KillFame', 0)
        death_fame = api_data.get('DeathFame', 0)
        
        embed.add_field(name="PvE Fame", value=f"{fame_total:,}", inline=True)
        embed.add_field(name="Kill Fame", value=f"{kill_fame:,}", inline=True)
        embed.add_field(name="Death Fame", value=f"{death_fame:,}", inline=True)
        
        old_guild = api_data.get('GuildName', 'Không có')
        embed.add_field(name="Guild Hiện Tại / Cũ", value=old_guild, inline=False)
        
        view = OfficerApprovalView(self.cog, interaction.user.id, api_data.get('Name'))
        await officer_channel.send(embed=embed, view=view)
        
        await interaction.followup.send(f"✅ Đã gửi đơn thành công! Vui lòng chờ các Officer xét duyệt để được vào server.", ephemeral=True)


class WelcomeView(discord.ui.View):
    def __init__(self, cog: 'Onboarding'):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Khai báo Thông Tin (IGN)", style=discord.ButtonStyle.green, custom_id="onboard_welcome_btn", emoji="📝")
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OnboardingModal(self.cog))


class OfficerApprovalView(discord.ui.View):
    def __init__(self, cog: 'Onboarding', target_user_id: int, ign_name: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_user_id = target_user_id
        self.ign_name = ign_name

    @discord.ui.button(label="Duyệt lính", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(self.target_user_id)
        
        if member:
            try:
                await member.edit(nick=self.ign_name)
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
                        
            try:
                await member.send(f"🎉 Đơn đăng ký của bạn đã được duyệt bởi {interaction.user.display_name}! Chào mừng bạn đến với The Northern Constellations (TNC)!")
            except:
                pass
                
        # Update UI
        for child in self.children:
            child.disabled = True
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = f"✅ Đã duyệt: {self.ign_name}"
        embed.set_footer(text=f"Duyệt bởi {interaction.user.display_name}")
        
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Từ chối", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được duyệt!", ephemeral=True)
            return
            
        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(self.target_user_id)
        
        if member:
            try:
                await member.send(f"❌ Đơn đăng ký vào TNC của bạn đã bị từ chối. Vui lòng liên hệ Admin nếu có nhầm lẫn.")
            except:
                pass

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
        
    @commands.Cog.listener()
    async def on_ready(self):
        # Giữ nút bấm khai báo form luôn hoạt động
        self.bot.add_view(WelcomeView(self))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = self.config.welcome_channel_id
        if not channel_id:
            return
            
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title=f"Chào mừng {member.name} đến với TNC!",
                description="Vui lòng nhấn nút bên dưới để khai báo In-Game Name (IGN) của bạn trong Albion Online.\nHệ thống sẽ tự động tra cứu dữ liệu game của bạn và gửi cho Ban quản trị xét duyệt.",
                color=discord.Color.gold()
            )
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(content=member.mention, embed=embed, view=WelcomeView(self))
            except:
                pass

    async def fetch_albion_player(self, ign: str):
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Search player
                async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/search?q={ign}") as resp:
                    if resp.status != 200: return None
                    data = await resp.json()
                    players = data.get("players", [])
                    if not players: return None
                    
                    # Tìm chính xác player
                    player = next((p for p in players if p["Name"].lower() == ign.lower()), None)
                    if not player: return None
                    
                    player_id = player["Id"]
                
                # 2. Get detailed stats
                async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/players/{player_id}") as resp:
                    if resp.status != 200: return None
                    return await resp.json()
        except:
            return None

    # --- Lệnh quản trị ---
    onboard_group = app_commands.Group(name="onboard", description="Cài đặt tính năng tự động lọc lính mới")

    @onboard_group.command(name="set_welcome", description="Cài đặt kênh gửi lời chào và nút form")
    @app_commands.describe(channel="Chọn kênh chat (thường là sảnh chờ)")
    async def onboard_set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        self.config.data["welcome_channel_id"] = str(channel.id)
        self.config.save()
        
        embed = discord.Embed(
            title="Đăng Ký Thành Viên TNC",
            description="Vui lòng nhấn nút bên dưới để khai báo In-Game Name (IGN) Albion Online của bạn.\nHệ thống sẽ tự động tra cứu dữ liệu và chuyển cho Officer xét duyệt.",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed, view=WelcomeView(self))
        await interaction.response.send_message(f"✅ Đã đặt kênh {channel.mention} làm nơi đón khách và gửi Panel form mẫu.", ephemeral=True)

    @onboard_group.command(name="set_officer", description="Cài đặt kênh để Officer nhận thông báo duyệt form")
    @app_commands.describe(channel="Chọn kênh chat kín của Officer")
    async def onboard_set_officer(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        self.config.data["officer_channel_id"] = str(channel.id)
        self.config.save()
        await interaction.response.send_message(f"✅ Đã đặt kênh {channel.mention} làm nơi nhận Log duyệt lính.", ephemeral=True)

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
