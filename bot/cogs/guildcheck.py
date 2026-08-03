import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

from core.config import STORAGE_DIR
from core.permissions import is_officer
from core.storage import load_json, save_json

# ==============================================================================
# HỆ THỐNG GUILDCHECK THỦ CÔNG
# ==============================================================================
GUILDCHECK_CONFIG_FILE = os.path.join(STORAGE_DIR, "tnc_guildcheck_v1.json")
REGION_API_BASE = {
    "Americas": "https://gameinfo.albiononline.com/api/gameinfo",
    "Asia": "https://gameinfo-sgp.albiononline.com/api/gameinfo",
    "Europe": "https://gameinfo-ams.albiononline.com/api/gameinfo",
}

GUILDCHECK_CONFIG_DEFAULT = lambda: {"guild_id": "", "region": "Asia"}

def load_guildcheck_config():
    return load_json(GUILDCHECK_CONFIG_FILE, GUILDCHECK_CONFIG_DEFAULT)

def save_guildcheck_config(data):
    save_json(data, GUILDCHECK_CONFIG_FILE)

async def albion_search_player(region, name):
    """Tìm player khớp TÊN TUYỆT ĐỐI trên đúng region. Trả None nếu không thấy."""
    base = REGION_API_BASE.get(region)
    if not base or not name:
        return None
    url = f"{base}/search?q={name}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
    except Exception as e:
        print(f"[Error] {e}")
        return None
    name_lower = name.strip().lower()
    for p in data.get("players", []):
        if (p.get("Name") or "").strip().lower() == name_lower:
            return p
    return None

class GuildCheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="guildconfig", description="Cấu hình Guild ID và Khu vực cho máy chủ (Officer only)")
    @app_commands.describe(
        guild_id="Guild ID Albion (lấy từ URL killboard guild)",
        region="Khu vực máy chủ (Asia, Americas, Europe)"
    )
    @app_commands.choices(region=[
        app_commands.Choice(name="Châu Á (East)", value="Asia"),
        app_commands.Choice(name="Châu Mỹ (West)", value="Americas"),
        app_commands.Choice(name="Châu Âu (EU)", value="Europe")
    ])
    async def guildconfig_cmd(
        self,
        interaction: discord.Interaction,
        guild_id: str = None,
        region: app_commands.Choice[str] = None
    ):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        config = load_guildcheck_config()
        if guild_id:
            config["guild_id"] = guild_id.strip()
        if region:
            config["region"] = region.value
        save_guildcheck_config(config)

        lines = [f"🆔 Guild ID: `{config.get('guild_id') or 'chưa cấu hình'}`"]
        lines.append(f"🌍 Region: `{config.get('region') or 'Asia'}`")
        await interaction.response.send_message("✅ Đã lưu cấu hình GuildCheck:\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="guildcheck", description="Tra cứu xem một thành viên có ở trong Guild hay không")
    @app_commands.describe(ign="Tên nhân vật trong game (chính xác)")
    async def guildcheck_cmd(self, interaction: discord.Interaction, ign: str):
        config = load_guildcheck_config()
        guild_id = config.get("guild_id")
        region = config.get("region", "Asia")
        
        if not guild_id:
            return await interaction.response.send_message("❌ Chưa cấu hình Guild ID! Vui lòng nhờ Officer dùng `/guildconfig`.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=False)
        
        player = await albion_search_player(region, ign)
        
        if player is None:
            embed = discord.Embed(
                title="🔍 Kết Quả Tra Cứu", 
                description=f"❌ **Không tìm thấy người chơi `{ign}`** trên khu vực `{region}`.\nVui lòng kiểm tra lại chính tả.", 
                color=0xe74c3c
            )
            return await interaction.followup.send(embed=embed)
            
        player_guild_id = player.get("GuildId", "")
        player_guild_name = player.get("GuildName", "Không có guild")
        
        if player_guild_id == guild_id:
            embed = discord.Embed(
                title="✅ Thành Viên Hợp Lệ", 
                description=f"Người chơi **{player.get('Name')}** hiện **ĐANG** ở trong guild của chúng ta.", 
                color=0x2ecc71
            )
        else:
            embed = discord.Embed(
                title="🚨 Phát Hiện Ngoại Lai", 
                description=f"Người chơi **{player.get('Name')}** hiện **KHÔNG** ở trong guild.\nĐang ở guild: `{player_guild_name}`", 
                color=0xe67e22
            )
            
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(GuildCheckCog(bot))
