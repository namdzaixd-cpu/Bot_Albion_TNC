import os
import re

path = 'bot/cogs/guildcheck.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace run_guildcheck logic
new_run_guildcheck = """    async def run_guildcheck(self, guild: discord.Guild):
        \"\"\"Chạy toàn bộ logic check. Trả về (removed_list, error_msg).\"\"\"
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

        old_unresolved = load_unresolved()
        new_unresolved = {}
        removed = []

        default_region = config.get("region", "Asia")

        for member in role.members:
            # Parse IGN from nickname. Format is usually [TAG] IGN or [TAG] IGN YOB
            match = re.search(r'\[.*?\]\s*([a-zA-Z0-9_]+)', member.display_name)
            if match:
                ign = match.group(1)
            else:
                ign = member.display_name

            player = await albion_search_player(default_region, ign)

            if player is None:
                new_unresolved[str(member.id)] = ign
                continue

            player_guild_id = player.get("GuildId", "")
            if player_guild_id != guild_id:
                try:
                    await member.remove_roles(role, reason="[GuildCheck] Không còn trong guild Albion")
                    removed.append((member, ign))
                except Exception as e:
                    print(f"⚠️ Không xóa được role của {member}: {e}")

        save_unresolved(new_unresolved)

        log_channel_id = config.get("log_channel_id")
        channel = guild.get_channel(int(log_channel_id)) if log_channel_id else None

        if removed and channel:
            desc = "\\n".join(f"• {m.mention} (IGN: `{ign}`)" for m, ign in removed)
            embed = discord.Embed(title="🧹 GuildCheck — Đã xóa role Member", description=desc, color=0xe67e22)
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"[Error] {e}")

        if set(new_unresolved.keys()) != set(old_unresolved.keys()) and channel:
            officer_role_id = config.get("officer_role_id")
            mention = f"<@&{officer_role_id}>" if officer_role_id else None
            if new_unresolved:
                desc = "\\n".join(f"• <@{uid}> — IGN trích xuất: `{ign}`" for uid, ign in new_unresolved.items())
            else:
                desc = "✅ Danh sách trống, không còn ai cần xử lý tay."
            embed = discord.Embed(title="⚠️ Danh sách Unresolved đã cập nhật", description=desc, color=0xf39c12)
            try:
                await channel.send(content=mention, embed=embed)
            except Exception as e:
                print(f"[Error] {e}")

        return removed, None"""

# Use regex to replace the function run_guildcheck
content = re.sub(r'    async def run_guildcheck.*?return removed, None', new_run_guildcheck, content, flags=re.DOTALL)

# Delete commands: register_albion, registerfor, myign
content = re.sub(r'    @app_commands\.command\(name="register_albion".*?ephemeral=True\n        \)', '', content, flags=re.DOTALL)
content = re.sub(r'    @app_commands\.command\(name="registerfor".*?ephemeral=True\n        \)', '', content, flags=re.DOTALL)
content = re.sub(r'    @app_commands\.command\(name="myign".*?ephemeral=True\n        \)', '', content, flags=re.DOTALL)

# Modify guildconfig to accept region
new_guildconfig = """    @app_commands.command(name="guildconfig", description="Cấu hình Guild ID, log channel, officer role & member role cho GuildCheck (Officer only)")
    @app_commands.describe(
        guild_id="Guild ID Albion (lấy từ URL killboard guild)",
        log_channel="Channel nhận log khi xóa role / cập nhật unresolved",
        officer_role="Role sẽ bị tag khi danh sách unresolved thay đổi",
        member_role="Role sẽ bị bot tự xóa nếu thành viên rời guild Albion",
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
        log_channel: discord.TextChannel = None,
        officer_role: discord.Role = None,
        member_role: discord.Role = None,
        region: app_commands.Choice[str] = None
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
        if region:
            config["region"] = region.value
        save_guildcheck_config(config)

        lines = [f"🆔 Guild ID: `{config.get('guild_id') or 'chưa có'}`"]
        lines.append(f"📢 Log channel: <#{config['log_channel_id']}>" if config.get("log_channel_id") else "📢 Log channel: chưa có")
        lines.append(f"👮 Officer role: <@&{config['officer_role_id']}>" if config.get("officer_role_id") else "👮 Officer role: chưa có")
        lines.append(f"🛡️ Member role: <@&{config['member_role_id']}>" if config.get("member_role_id") else "🛡️ Member role: chưa có")
        lines.append(f"🌍 Region: `{config.get('region') or 'Asia'}`")
        await interaction.response.send_message("✅ Đã lưu config:\\n" + "\\n".join(lines), ephemeral=True)"""

content = re.sub(r'    @app_commands\.command\(name="guildconfig".*?ephemeral=True\)', new_guildconfig, content, flags=re.DOTALL)

# Add import re at top if missing
if 'import re' not in content:
    content = 'import re\n' + content

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
