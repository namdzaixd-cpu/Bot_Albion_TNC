import asyncio
import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from core.config import STORAGE_DIR
from core.permissions import is_officer
from core.storage import load_json, save_json

# ==============================================================================
# HỆ THỐNG REGISTER + GUILDCHECK (Đăng ký IGN & tự xóa role nếu rời guild)
# ==============================================================================
REGISTER_FILE = os.path.join(STORAGE_DIR, "tnc_register_v1.json")
GUILDCHECK_CONFIG_FILE = os.path.join(STORAGE_DIR, "tnc_guildcheck_v1.json")
UNRESOLVED_FILE = os.path.join(STORAGE_DIR, "tnc_unresolved_v1.json")
REGION_API_BASE = {
    "Americas": "https://gameinfo.albiononline.com/api/gameinfo",
    "Asia": "https://gameinfo-sgp.albiononline.com/api/gameinfo",
    "Europe": "https://gameinfo-ams.albiononline.com/api/gameinfo",
}

GUILDCHECK_CONFIG_DEFAULT = lambda: {"guild_id": "", "log_channel_id": "", "officer_role_id": "", "member_role_id": ""}


def load_register():
    return load_json(REGISTER_FILE, dict)


def save_register(data):
    save_json(data, REGISTER_FILE)


def load_guildcheck_config():
    return load_json(GUILDCHECK_CONFIG_FILE, GUILDCHECK_CONFIG_DEFAULT)


def save_guildcheck_config(data):
    save_json(data, GUILDCHECK_CONFIG_FILE)


def load_unresolved():
    return load_json(UNRESOLVED_FILE, dict)


def save_unresolved(data):
    save_json(data, UNRESOLVED_FILE)


async def albion_search_player(region, name):
    """Tìm player khớp TÊN TUYỆT ĐỐI (không phân biệt hoa/thường) trên đúng region. Trả None nếu không thấy/lỗi."""
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
    except Exception:
        return None
    name_lower = name.strip().lower()
    for p in data.get("players", []):
        if (p.get("Name") or "").strip().lower() == name_lower:
            return p
    return None


class GuildCheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.loop.create_task(self._guildcheck_loop())

    async def _guildcheck_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                config = load_guildcheck_config()
                if config.get("guild_id"):
                    for guild in self.bot.guilds:
                        await self.run_guildcheck(guild)
            except Exception as e:
                print(f"❌ [GuildCheck] Lỗi: {e}")
            await asyncio.sleep(6 * 3600)  # check mỗi 6 tiếng

    async def run_guildcheck(self, guild: discord.Guild):
        """Chạy toàn bộ logic check. Trả về (removed_list, error_msg)."""
        config = load_guildcheck_config()
        guild_id = config.get("guild_id")
        if not guild_id:
            return None, "❌ Chưa cấu hình Guild ID TNC! Dùng `/guildconfig guild_id:<id>` trước."

        member_role_id = config.get("member_role_id")
        if not member_role_id:
            return None, "❌ Chưa cấu hình Member Role! Dùng `/guildconfig member_role:<@role>` trước."
        role = guild.get_role(int(member_role_id))
        if not role:
            return None, "❌ Không tìm thấy role đã config (có thể role đã bị xóa), setup lại `/guildconfig member_role:<@role>`!"

        register = load_register()
        old_unresolved = load_unresolved()
        new_unresolved = {}
        removed = []

        for uid_str, info in register.items():
            member = guild.get_member(int(uid_str))
            if not member:
                continue
            ign = info.get("ign", "")
            region = info.get("region", "")
            player = await albion_search_player(region, ign)

            if player is None:
                new_unresolved[uid_str] = ign
                continue

            player_guild_id = player.get("GuildId", "")
            if player_guild_id != guild_id:
                if role in member.roles:
                    try:
                        await member.remove_roles(role, reason="[GuildCheck] Không còn trong guild Albion")
                        removed.append((member, ign))
                    except Exception as e:
                        print(f"⚠️ Không xóa được role của {member}: {e}")

        save_unresolved(new_unresolved)

        log_channel_id = config.get("log_channel_id")
        channel = guild.get_channel(int(log_channel_id)) if log_channel_id else None

        if removed and channel:
            desc = "\n".join(f"• {m.mention} (IGN: `{ign}`)" for m, ign in removed)
            embed = discord.Embed(title="🧹 GuildCheck — Đã xóa role TNC_Member", description=desc, color=0xe67e22)
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

        if set(new_unresolved.keys()) != set(old_unresolved.keys()) and channel:
            officer_role_id = config.get("officer_role_id")
            mention = f"<@&{officer_role_id}>" if officer_role_id else None
            if new_unresolved:
                desc = "\n".join(f"• <@{uid}> — IGN đăng ký: `{ign}`" for uid, ign in new_unresolved.items())
            else:
                desc = "✅ Danh sách trống, không còn ai cần xử lý tay."
            embed = discord.Embed(title="⚠️ Danh sách Unresolved đã cập nhật", description=desc, color=0xf39c12)
            try:
                await channel.send(content=mention, embed=embed)
            except Exception:
                pass

        return removed, None

    @app_commands.command(name="registertnc", description="Đăng ký nhân vật Albion để bot check guild")
    @app_commands.describe(region="Server Albion bạn đang chơi", albion_nick="Tên nhân vật trong game (chính xác)")
    @app_commands.choices(region=[
        app_commands.Choice(name="Americas", value="Americas"),
        app_commands.Choice(name="Asia", value="Asia"),
        app_commands.Choice(name="Europe", value="Europe"),
    ])
    async def registertnc_cmd(self, interaction: discord.Interaction, region: app_commands.Choice[str], albion_nick: str):
        data = load_register()
        data[str(interaction.user.id)] = {"ign": albion_nick.strip(), "region": region.value}
        save_register(data)
        await interaction.response.send_message(
            f"✅ Đã đăng ký nhân vật **{albion_nick.strip()}** (server **{region.value}**)", ephemeral=True
        )

    @app_commands.command(name="registerfor", description="Đăng ký IGN Albion cho member khác (Officer only)")
    @app_commands.describe(member="Member cần đăng ký", region="Server Albion", albion_nick="Tên nhân vật trong game")
    @app_commands.choices(region=[
        app_commands.Choice(name="Americas", value="Americas"),
        app_commands.Choice(name="Asia", value="Asia"),
        app_commands.Choice(name="Europe", value="Europe"),
    ])
    async def registerfor_cmd(self, interaction: discord.Interaction, member: discord.Member, region: app_commands.Choice[str], albion_nick: str):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        data = load_register()
        data[str(member.id)] = {"ign": albion_nick.strip(), "region": region.value}
        save_register(data)
        await interaction.response.send_message(
            f"✅ Đã đăng ký **{albion_nick.strip()}** (server **{region.value}**) cho {member.mention}", ephemeral=True
        )

    @app_commands.command(name="myign", description="Xem IGN Albion đã đăng ký")
    async def myign_cmd(self, interaction: discord.Interaction):
        data = load_register()
        info = data.get(str(interaction.user.id))
        if not info:
            return await interaction.response.send_message("❓ Bạn chưa đăng ký. Dùng `/registertnc`!", ephemeral=True)
        await interaction.response.send_message(
            f"🎮 IGN: **{info.get('ign')}** | Server: **{info.get('region')}**", ephemeral=True
        )

    @app_commands.command(name="guildconfig", description="Cấu hình Guild ID, log channel, officer role & member role cho GuildCheck (Officer only)")
    @app_commands.describe(
        guild_id="Guild ID Albion của TNC (lấy từ URL killboard guild)",
        log_channel="Channel nhận log khi xóa role / cập nhật unresolved",
        officer_role="Role sẽ bị tag khi danh sách unresolved thay đổi",
        member_role="Role sẽ bị bot tự xóa nếu thành viên rời guild Albion (vd: TNC Member)"
    )
    async def guildconfig_cmd(
        self,
        interaction: discord.Interaction,
        guild_id: str = None,
        log_channel: discord.TextChannel = None,
        officer_role: discord.Role = None,
        member_role: discord.Role = None
    ):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        config = load_guildcheck_config()
        if guild_id:
            config["guild_id"] = guild_id.strip()
        if log_channel:
            config["log_channel_id"] = str(log_channel.id)
        if officer_role:
            config["officer_role_id"] = str(officer_role.id)
        if member_role:
            config["member_role_id"] = str(member_role.id)
        save_guildcheck_config(config)

        lines = [f"🆔 Guild ID: `{config.get('guild_id') or 'chưa có'}`"]
        lines.append(f"📢 Log channel: <#{config['log_channel_id']}>" if config.get("log_channel_id") else "📢 Log channel: chưa có")
        lines.append(f"👮 Officer role: <@&{config['officer_role_id']}>" if config.get("officer_role_id") else "👮 Officer role: chưa có")
        lines.append(f"🛡️ Member role: <@&{config['member_role_id']}>" if config.get("member_role_id") else "🛡️ Member role: chưa có")
        await interaction.response.send_message("✅ Đã lưu config:\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="guildcheck", description="Chạy tay check thành viên rời guild Albion (Officer only)")
    async def guildcheck_cmd(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        removed, err = await self.run_guildcheck(interaction.guild)
        if err:
            return await interaction.followup.send(err, ephemeral=True)
        if not removed:
            return await interaction.followup.send(
                "✅ Check xong, không có ai bị xóa role. (Xem `/unresolved` nếu có người cần xử lý tay)", ephemeral=True
            )
        desc = "\n".join(f"• {m.mention} (IGN: `{ign}`)" for m, ign in removed)
        await interaction.followup.send(f"🧹 Đã xóa role `TNC_Member` của **{len(removed)}** người:\n{desc}", ephemeral=True)

    @app_commands.command(name="unresolved", description="Xem danh sách chưa xác định được guild, cần xử lý tay (Officer only)")
    async def unresolved_cmd(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        data = load_unresolved()
        if not data:
            return await interaction.response.send_message("✅ Danh sách unresolved đang trống.", ephemeral=True)
        desc = "\n".join(f"• <@{uid}> — IGN đăng ký: `{ign}`" for uid, ign in data.items())
        embed = discord.Embed(title=f"⚠️ Unresolved — {len(data)} người", description=desc, color=0xf39c12)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildCheckCog(bot))
