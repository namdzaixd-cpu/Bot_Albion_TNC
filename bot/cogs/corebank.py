import os
import re
from datetime import datetime
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands

from core.config import DATA_DIR
from core.permissions import is_officer
from core.storage import load_json, save_json

# ==============================================================================
# HỆ THỐNG CORE-BANK (Tích hợp UnbelievaBoat)
# ==============================================================================
CORECONFIG_FILE = os.path.join(DATA_DIR, "tnc_coreconfig_v1.json")
CORE_CREDITED_FILE = os.path.join(DATA_DIR, "tnc_core_credited_v1.json")


def load_coreconfig():
    return load_json(CORECONFIG_FILE, lambda: {"core_channel_id": "", "bank_channel_id": "", "unbelievaboat_token": "", "emoji_map": {}})


def save_coreconfig(data):
    save_json(data, CORECONFIG_FILE)


def load_core_credited():
    return load_json(CORE_CREDITED_FILE, dict)


def save_core_credited(data):
    save_json(data, CORE_CREDITED_FILE)


def parse_emoji_input(emoji_str: str):
    """Phân tích chuỗi emoji từ lệnh slash.
    Trả về (key, display_str):
      - key: ID (custom emoji) hoặc ký tự unicode (emoji thường)
      - display_str: chuỗi hiển thị để bot in ra
    """
    emoji_str = emoji_str.strip()
    match = re.match(r'<a?:(\w+):(\d+)>', emoji_str)
    if match:
        name, eid = match.group(1), match.group(2)
        return eid, f"<:{name}:{eid}>"
    return emoji_str, emoji_str


def get_reaction_key(emoji) -> str:
    """Lấy key nhất quán cho emoji reaction (PartialEmoji)."""
    return str(emoji.id) if emoji.id else emoji.name


class CoreBankCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Tự động react vào ảnh trong kênh Core ───────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        try:
            core_config = load_coreconfig()
            if core_config.get("auto_react", False) and str(message.channel.id) == core_config.get("core_channel_id"):
                if message.attachments:
                    emoji_map = core_config.get("emoji_map", {})

                    # Xử lý tách ảnh nếu có nhiều hơn 1 ảnh
                    if len(message.attachments) > 1:
                        await message.reply("🔄 Phát hiện nhiều ảnh, bot đang tách ra thành từng tin nhắn để dễ chấm điểm...")
                        for i, att in enumerate(message.attachments):
                            try:
                                file = await att.to_file()
                                text = f"📸 Ảnh tách ra từ {message.author.mention} (Ảnh {i+1}/{len(message.attachments)})"
                                if i == 0 and message.content:
                                    text += f"\n📝 Lời nhắn gốc: {message.content}"
                                split_msg = await message.channel.send(content=text, file=file)

                                # Tự động react vào ảnh tách ra
                                if emoji_map:
                                    sorted_keys = sorted(emoji_map.keys(), key=lambda k: (emoji_map[k].get("order", 0), emoji_map[k]["value"]))
                                    for key in sorted_keys:
                                        try:
                                            emoji_str = emoji_map[key]["display"]
                                            reaction = discord.PartialEmoji.from_str(emoji_str) if ":" in emoji_str else emoji_str
                                            await split_msg.add_reaction(reaction)
                                        except Exception:
                                            pass
                            except Exception as e:
                                print(f"⚠️ [Core-Bank] Lỗi khi tách ảnh: {e}")

                        # Xóa tin nhắn gốc sau khi đã tách thành công
                        try:
                            await message.delete()
                        except Exception:
                            pass
                        return  # Đã tách ảnh xong, dừng xử lý tin nhắn gốc

                    # Nếu chỉ 1 ảnh thì react bình thường vào tin nhắn gốc
                    if emoji_map:
                        sorted_keys = sorted(emoji_map.keys(), key=lambda k: (emoji_map[k].get("order", 0), emoji_map[k]["value"]))
                        for key in sorted_keys:
                            try:
                                emoji_str = emoji_map[key]["display"]
                                reaction = discord.PartialEmoji.from_str(emoji_str) if ":" in emoji_str else emoji_str
                                await message.add_reaction(reaction)
                            except Exception:
                                pass
        except Exception as e:
            print(f"⚠️ [Core-Bank] Lỗi khi tự động react: {e}")

    # ── Lệnh cấu hình ────────────────────────────────────────────────────────

    @app_commands.command(name="coresetup", description="Cài đặt kênh cho hệ thống Core-Bank (Officer only)")
    @app_commands.describe(
        core_channel="Kênh #core-vortex nơi member đăng ảnh",
        bank_channel="Kênh bot gửi lệnh !add-money / !remove-money cho UnbelievaBoat"
    )
    async def coresetup_cmd(self, interaction: discord.Interaction,
                             core_channel: discord.TextChannel,
                             bank_channel: discord.TextChannel):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
        config = load_coreconfig()
        config["core_channel_id"] = str(core_channel.id)
        config["bank_channel_id"] = str(bank_channel.id)
        save_coreconfig(config)
        await interaction.response.send_message(
            f"✅ Đã cài đặt Core-Bank:\n"
            f"📸 Core channel: {core_channel.mention}\n"
            f"💰 Bank channel: {bank_channel.mention}",
            ephemeral=True
        )

    @app_commands.command(name="coretoken", description="Cài đặt API Token của UnbelievaBoat (Officer only)")
    @app_commands.describe(token="API Token lấy từ trang chủ UnbelievaBoat")
    async def coretoken_cmd(self, interaction: discord.Interaction, token: str):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
        config = load_coreconfig()
        config["unbelievaboat_token"] = token
        save_coreconfig(config)
        await interaction.response.send_message("✅ Đã cài đặt UnbelievaBoat API Token thành công!", ephemeral=True)

    @app_commands.command(name="coreadd", description="Thêm emoji Core với tên và giá trị silver tuỳ ý (Officer only)")
    @app_commands.describe(
        emoji="Emoji đại diện (unicode hoặc emoji server, vd: 🟢 hay <:ten:id>)",
        name="Tên Core (vd: Green Core, Xanh Lá...)",
        value="Giá trị silver tương ứng",
        order="Số thứ tự hiển thị (tùy chọn, mặc định 0)"
    )
    async def coreadd_cmd(self, interaction: discord.Interaction, emoji: str, name: str, value: int, order: int = 0):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
        if value <= 0:
            return await interaction.response.send_message("⚠️ Giá trị silver phải > 0!", ephemeral=True)
        key, display = parse_emoji_input(emoji)
        config = load_coreconfig()
        config.setdefault("emoji_map", {})[key] = {"name": name, "value": value, "display": display, "order": order}
        save_coreconfig(config)
        await interaction.response.send_message(
            f"✅ Đã thêm: {display} = **{name}** = **{value:,} silver** (STT: {order})",
            ephemeral=True
        )

    @app_commands.command(name="coreremove", description="Xóa emoji Core khỏi danh sách (Officer only)")
    @app_commands.describe(emoji="Emoji muốn xóa")
    async def coreremove_cmd(self, interaction: discord.Interaction, emoji: str):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
        key, display = parse_emoji_input(emoji)
        config = load_coreconfig()
        emoji_map = config.get("emoji_map", {})
        if key not in emoji_map:
            return await interaction.response.send_message(f"❓ Không tìm thấy emoji `{display}` trong danh sách.", ephemeral=True)
        removed = emoji_map.pop(key)
        save_coreconfig(config)
        await interaction.response.send_message(
            f"🗑️ Đã xóa: {display} = **{removed['name']}** ({removed['value']:,} silver)",
            ephemeral=True
        )

    @app_commands.command(name="coreautoreact", description="Bật/tắt tự động thả emoji vào ảnh trong kênh Core (Officer only)")
    @app_commands.describe(enable="Bật (True) hoặc Tắt (False)")
    async def coreautoreact_cmd(self, interaction: discord.Interaction, enable: bool):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
        config = load_coreconfig()
        config["auto_react"] = enable
        save_coreconfig(config)
        state = "BẬT ✅" if enable else "TẮT ❌"
        await interaction.response.send_message(f"⚙️ Tự động thả emoji vào ảnh trong kênh Core: **{state}**", ephemeral=True)

    @app_commands.command(name="corelist", description="Xem danh sách emoji Core và cấu hình hiện tại")
    async def corelist_cmd(self, interaction: discord.Interaction):
        config = load_coreconfig()
        emoji_map = config.get("emoji_map", {})
        core_ch = config.get("core_channel_id")
        bank_ch = config.get("bank_channel_id")
        token = config.get("unbelievaboat_token", "")
        auto_react = config.get("auto_react", False)

        embed = discord.Embed(title="⚙️ Cấu hình Core-Bank", color=0xf1c40f)
        embed.add_field(
            name="📌 Kênh & Cấu hình",
            value=(f"📸 Core: {f'<#{core_ch}>' if core_ch else '_Chưa cài_'}\n"
                   f"💰 Bank: {f'<#{bank_ch}>' if bank_ch else '_Chưa cài_'}\n"
                   f"🔑 Token API: **{'Đã cài ✅' if token else 'Chưa cài ❌'}**\n"
                   f"🤖 Tự động react ảnh: **{'BẬT ✅' if auto_react else 'TẮT ❌'}**"),
            inline=False
        )
        if emoji_map:
            sorted_emojis = sorted(emoji_map.values(), key=lambda x: (x.get("order", 0), x["value"]))
            lines = [f"{info['display']} **{info['name']}** — {info['value']:,} silver (STT: {info.get('order', 0)})"
                     for info in sorted_emojis]
            embed.add_field(name=f"📋 Danh sách Core ({len(emoji_map)})", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="📋 Danh sách Core", value="_Chưa có emoji nào. Dùng `/coreadd` để thêm._", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Event: Phát hiện react & gỡ react ───────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        config = load_coreconfig()
        core_ch_id = config.get("core_channel_id")
        bank_ch_id = config.get("bank_channel_id")
        emoji_map = config.get("emoji_map", {})

        # Chỉ xử lý trong kênh core đã cài
        if not core_ch_id or str(payload.channel_id) != core_ch_id:
            return

        emoji_key = get_reaction_key(payload.emoji)
        if emoji_key not in emoji_map:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        reactor = guild.get_member(payload.user_id)
        if not reactor or not is_officer(reactor):
            return  # Không phải Officer → bỏ qua

        # Kiểm tra chống cộng trùng
        credited = load_core_credited()
        credit_key = f"{payload.message_id}:{emoji_key}"
        if credit_key in credited:
            return  # Đã cộng rồi, Officer khác react sau → bỏ qua

        # Lấy tin nhắn gốc để tìm ra member đã đăng ảnh
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return
        author = message.author

        # Xác định lại tác giả nếu đó là ảnh do bot tách ra
        if author.id == self.bot.user.id and "Ảnh tách ra từ <@" in message.content:
            match = re.search(r"Ảnh tách ra từ <@!?(\d+)>", message.content)
            if match:
                actual_id = match.group(1)
                actual_member = guild.get_member(int(actual_id))
                if actual_member:
                    author = actual_member

        if author.bot:
            return

        core_info = emoji_map[emoji_key]
        core_name = core_info["name"]
        core_value = core_info["value"]
        core_disp = core_info.get("display", emoji_key)

        # Lấy bank channel
        bank_channel = guild.get_channel(int(bank_ch_id)) if bank_ch_id else None
        if not bank_channel:
            await channel.send(
                "⚠️ Chưa cài bank channel! Dùng `/coresetup` trước.",
                reference=message
            )
            return

        # Ghi nhận trước để tránh race condition giữa 2 Officer react nhanh
        credited[credit_key] = {
            "officer_id": str(reactor.id),
            "member_id": str(author.id),
            "core_name": core_name,
            "value": core_value,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_core_credited(credited)

        # Xử lý API UnbelievaBoat
        token = config.get("unbelievaboat_token")
        if not token:
            await channel.send("⚠️ Chưa cài UnbelievaBoat API Token! Hãy dùng `/coretoken`.", reference=message)
            return

        api_url = f"https://unbelievaboat.com/api/v1/guilds/{payload.guild_id}/users/{author.id}"
        headers = {"Authorization": token}
        payload_data = {"bank": core_value, "reason": f"CoreBank: {core_name}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(api_url, headers=headers, json=payload_data) as resp:
                    if resp.status not in (200, 204):
                        err_text = await resp.text()
                        await channel.send(f"⚠️ Lỗi API UnbelievaBoat ({resp.status}): {err_text}", reference=message)
                        return
        except Exception as e:
            await channel.send(f"⚠️ Lỗi kết nối API UnbelievaBoat: {e}", reference=message)
            return

        # Xác nhận dưới ảnh gốc
        await channel.send(
            f"✅ {core_disp} **{core_name}** — Đã cộng **{core_value:,} silver** vào bank của {author.mention}\n"
            f"_Ghi nhận bởi {reactor.mention}_",
            reference=message
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        config = load_coreconfig()
        core_ch_id = config.get("core_channel_id")
        bank_ch_id = config.get("bank_channel_id")
        emoji_map = config.get("emoji_map", {})

        if not core_ch_id or str(payload.channel_id) != core_ch_id:
            return

        emoji_key = get_reaction_key(payload.emoji)
        if emoji_key not in emoji_map:
            return

        credited = load_core_credited()
        credit_key = f"{payload.message_id}:{emoji_key}"
        if credit_key not in credited:
            return  # Chưa từng cộng → không cần hoàn lại

        entry = credited[credit_key]
        # Chỉ hoàn lại nếu chính Officer đó gỡ react
        if str(payload.user_id) != entry["officer_id"]:
            return

        del credited[credit_key]
        save_core_credited(credited)

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        core_info = emoji_map[emoji_key]
        core_value = core_info["value"]
        core_name = core_info["name"]
        core_disp = core_info.get("display", emoji_key)
        member = guild.get_member(int(entry["member_id"]))
        member_mention = member.mention if member else f"<@{entry['member_id']}>"
        reactor = guild.get_member(payload.user_id)
        reactor_mention = reactor.mention if reactor else f"<@{payload.user_id}>"

        token = config.get("unbelievaboat_token")
        if token:
            api_url = f"https://unbelievaboat.com/api/v1/guilds/{payload.guild_id}/users/{entry['member_id']}"
            headers = {"Authorization": token}
            payload_data = {"bank": -core_value, "reason": f"CoreBank Revert: {core_name}"}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.patch(api_url, headers=headers, json=payload_data):
                        pass
            except Exception:
                pass

        channel = guild.get_channel(payload.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(payload.message_id)
                await channel.send(
                    f"↩️ **Hoàn tác** {core_disp} {core_name} — Đã trừ lại **{core_value:,} silver** của {member_mention}\n"
                    f"_Gỡ bởi {reactor_mention}_",
                    reference=message
                )
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(CoreBankCog(bot))
