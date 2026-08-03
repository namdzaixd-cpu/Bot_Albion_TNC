import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import aiohttp
from typing import Optional

from core.config import STORAGE_DIR
from core.storage import load_json, save_json
from core.permissions import is_officer

class GlobalBlacklist:
    def __init__(self):
        self.file_path = os.path.join(STORAGE_DIR, "global_blacklist_v1.json")
        self.data = self._load()
        
    def _load(self):
        default_data = {"blacklist": []}
        if not os.path.exists(self.file_path):
            save_json(self.file_path, default_data, sync_github=True)
            return default_data
        
        data = load_json(self.file_path)
        if "blacklist" not in data:
            data["blacklist"] = []
        return data
        
    def save(self):
        save_json(self.file_path, self.data, sync_github=True)
        
    def check_blacklist(self, discord_id: str, ingame_id: str) -> Optional[dict]:
        for entry in self.data["blacklist"]:
            if entry.get("discord_id") == str(discord_id) or (ingame_id and entry.get("ingame_id") == str(ingame_id)):
                return entry
        return None
        
    def add_entry(self, discord_id: str, ingame_name: str, ingame_id: str, reason: str, officer_id: str, guild_id: str):
        # Remove old if exists
        self.data["blacklist"] = [e for e in self.data["blacklist"] if e.get("discord_id") != str(discord_id) and e.get("ingame_id") != str(ingame_id)]
        
        new_entry = {
            "discord_id": str(discord_id),
            "ingame_name": ingame_name,
            "ingame_id": str(ingame_id),
            "reason": reason,
            "added_by_discord_id": str(officer_id),
            "source_guild_id": str(guild_id),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self.data["blacklist"].append(new_entry)
        self.save()
        
    def remove_entry(self, identifier: str) -> bool:
        initial_count = len(self.data["blacklist"])
        self.data["blacklist"] = [e for e in self.data["blacklist"] 
                                  if e.get("discord_id") != str(identifier) and e.get("ingame_name", "").lower() != str(identifier).lower()]
        
        if len(self.data["blacklist"]) < initial_count:
            self.save()
            return True
        return False


class BlacklistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.blacklist_db = GlobalBlacklist()
        
    async def fetch_albion_player(self, ign: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://gameinfo-sgp.albiononline.com/api/gameinfo/search?q={ign}") as resp:
                    if resp.status != 200: return None
                    data = await resp.json()
                    players = data.get("players", [])
                    if not players: return None
                    
                    player = next((p for p in players if p["Name"].lower() == ign.lower()), None)
                    if not player: return None
                    return player
        except Exception as e:
            print(f"[Error] {e}")
            return None

    blacklist_group = app_commands.Group(name="blacklist", description="Hệ thống Global Blacklist liên minh")

    @blacklist_group.command(name="add", description="Thêm một người chơi vào danh sách đen")
    async def blacklist_add(self, interaction: discord.Interaction, user: discord.Member, ingame_name: str, reason: str):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được quyền dùng lệnh này!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        player_data = await self.fetch_albion_player(ingame_name)
        if not player_data:
            await interaction.followup.send(f"❌ Không tìm thấy nhân vật `{ingame_name}` trên hệ thống Albion SGP. Vui lòng kiểm tra lại tên.")
            return
            
        ingame_id = player_data["Id"]
        
        self.blacklist_db.add_entry(
            discord_id=user.id,
            ingame_name=player_data["Name"],
            ingame_id=ingame_id,
            reason=reason,
            officer_id=interaction.user.id,
            guild_id=interaction.guild.id
        )
        
        embed = discord.Embed(title="🚨 Đã thêm vào Blacklist", color=discord.Color.red())
        embed.add_field(name="Discord", value=f"<@{user.id}> ({user.id})", inline=False)
        embed.add_field(name="Ingame", value=f"{player_data['Name']}", inline=True)
        embed.add_field(name="Lý do", value=reason, inline=False)
        embed.set_footer(text=f"Thêm bởi {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)


    @blacklist_group.command(name="remove", description="Xóa một người chơi khỏi danh sách đen (bằng Discord ID hoặc Ingame Name)")
    async def blacklist_remove(self, interaction: discord.Interaction, identifier: str):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được quyền dùng lệnh này!", ephemeral=True)
            return
            
        success = self.blacklist_db.remove_entry(identifier)
        if success:
            await interaction.response.send_message(f"✅ Đã gỡ bỏ `{identifier}` khỏi Blacklist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Không tìm thấy ai có ID hoặc Tên là `{identifier}` trong Blacklist.", ephemeral=True)


    @blacklist_group.command(name="view", description="Xem danh sách đen hiện tại")
    async def blacklist_view(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Officer trở lên mới được quyền xem Blacklist!", ephemeral=True)
            return
            
        entries = self.blacklist_db.data.get("blacklist", [])
        if not entries:
            await interaction.response.send_message("✅ Danh sách đen hiện đang trống.", ephemeral=True)
            return
            
        embed = discord.Embed(title="📜 Global Blacklist", color=discord.Color.dark_red())
        
        for entry in entries:
            discord_mention = f"<@{entry['discord_id']}>"
            ingame = entry['ingame_name']
            reason = entry['reason']
            embed.add_field(name=f"Ingame: {ingame}", value=f"Discord: {discord_mention}\nLý do: {reason}", inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BlacklistCog(bot))
