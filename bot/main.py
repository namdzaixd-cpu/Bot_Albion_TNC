import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import shutil
import tempfile
import aiohttp
import random
import asyncio
import subprocess
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread, Lock
from gtts import gTTS

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG & ĐƯỜNG DẪN DỮ LIỆU
# ==============================================================================
TOKEN = os.getenv("DISCORD_TOKEN", "")
GIT_URL = os.getenv("GITHUB_GIT_URL", "")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "712258265769050164"))

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SIPHONED_FILE = os.path.join(DATA_DIR, "tnc_sp_v32.json")

_lock = Lock()       # Lock dùng cho GitHub sync
_file_lock = Lock()  # Lock dùng cho đọc/ghi file JSON (chống race condition)
BOT_SESSION_ID = random.randint(1000, 9999)

# ==============================================================================
# 2. WEB SERVER FLASK (TREO BOT ONLINE TRÊN RENDER)
# ==============================================================================
app = Flask("")

@app.route("/")
def home():
    return f"🛡️ TNC Manager v40 [Siphoned + Massing + GuildCheck] Live! ID: {BOT_SESSION_ID}"

def run():
    app.run(host="0.0.0.0", port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==============================================================================
# 3. CƠ CHẾ CHỐNG MẤT DỮ LIỆU - TỰ ĐỘNG ĐẨY NGƯỢC LÊN GITHUB
# ==============================================================================
def sync_to_github():
    with _lock:
        try:
            subprocess.run(["git", "config", "user.name", "TNC_Data_Guard"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "guard@tnc-guild.com"], check=True, capture_output=True)
            subprocess.run(["git", "add", "tnc_sp_v32.json", "tnc_lastseen_v1.json", "tnc_massing_v1.json", "tnc_register_v1.json", "tnc_guildcheck_v1.json", "tnc_unresolved_v1.json", "tnc_tts_config_v1.json", "tnc_templates_v1.json"], check=True, capture_output=True)
            commit_res = subprocess.run(["git", "commit", "-m", f"🤖 [Auto-Save] Session {BOT_SESSION_ID}"], capture_output=True, text=True)
            if "nothing to commit" not in commit_res.stdout:
                subprocess.run(["git", "push", GIT_URL, "main"], check=True, capture_output=True)
                print("📊 [Data-Guard] Đồng bộ GitHub thành công!")
            else:
                print("📊 [Data-Guard] Không có thay đổi dữ liệu cần sao lưu.")
        except Exception as e:
            print(f"❌ [Data-Guard] Lỗi Auto-Sync: {e}")

# ==============================================================================
# 4. GIAO DIỆN PHÂN TRANG (PAGINATION) BẢNG ĐIỂM SIPHONED
# ==============================================================================
class SiphonedPaginator(discord.ui.View):
    def __init__(self, data, last_update):
        super().__init__(timeout=86400)
        self.data = data
        self.last_update = last_update
        self.current_page = 0
        self.per_page = 15

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_data = self.data[start:end]
        total_pages = (len(self.data) - 1) // self.per_page + 1 if self.data else 1
        embed = discord.Embed(title="💎 TNC SIPHONED LEADERBOARD", color=0x9b59b6)
        embed.add_field(name="📅 Mốc Log Đã Cập Nhật:", value=f"`{self.last_update}`", inline=False)
        desc = ""
        for i, (player, value) in enumerate(page_data, start + 1):
            desc += f"**#{i}** `{player}` ➜ **{value:,}**\n"
        embed.description = desc if desc else "Không có dữ liệu đóng góp."
        embed.set_footer(text=f"Trang {self.current_page + 1}/{total_pages} • Tổng số: {len(self.data)} người")
        return embed

    @discord.ui.button(label="⬅️ Trước", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Sau ➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.current_page + 1) * self.per_page < len(self.data):
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

# ==============================================================================
# 5. KHỞI TẠO BOT CORE
# ==============================================================================
class TNCBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=["!", "."], intents=intents, help_command=None)

    async def setup_hook(self):
        GUILD = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=GUILD)
        synced = await self.tree.sync(guild=GUILD)
        print(f"✅ Đã sync {len(synced)} slash commands vào guild!")

        # Khôi phục các party Massing sau khi bot restart (đăng ký lại nút với Discord)
        loaded = load_massing()
        if loaded:
            active_parties.update(loaded)
            restored = 0
            for pid in list(active_parties.keys()):
                try:
                    self.add_view(PartyView(pid))
                    restored += 1
                except Exception as e:
                    print(f"⚠️ Không khôi phục được party {pid}: {e}")
            print(f"🔄 Đã khôi phục {restored} party Massing sau restart!")

bot = TNCBot()

def load_db(path, db_type="sp"):
    for try_path in [path, path + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {path}")
    return {"history": {}, "last_update": "Chưa có dữ liệu"}

def save_db(data, path):
    with _file_lock:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(path):
            shutil.copy2(path, path + ".bak")
        os.replace(tmp_path, path)
    Thread(target=sync_to_github).start()

def is_officer(member):
    if not hasattr(member, "roles"): return False
    valid_roles = ["officer", "guild master", "admin", "phó hội", "chủ hội"]
    return any(r.name.lower() in valid_roles for r in member.roles)

# ==============================================================================
# 6. HỆ THỐNG PHÂN TÍCH ĐIỂM SIPHONED (LOG ANALYZER)
# ==============================================================================
@bot.tree.command(name="spupdate", description="Cập nhật file log Siphoned (tự kiểm tra ngày tháng)")
async def spupdate(interaction: discord.Interaction, file_log: discord.Attachment):
    await interaction.response.defer()
    if not file_log.filename.endswith('.txt'):
        return await interaction.followup.send("❌ Vui lòng đính kèm tệp văn bản định dạng `.txt`!")

    async with aiohttp.ClientSession() as session:
        async with session.get(file_log.url) as r:
            text = await r.text(encoding='utf-8', errors='ignore')

    data = load_db(SIPHONED_FILE, "sp")
    lines = text.strip().split('\n')

    # Bước 1: Tìm mốc thời gian mới nhất trong file
    new_latest_time = None
    for line in lines:
        if "Player" in line or not line.strip(): continue
        parts = [p.strip().replace('"', '') for p in line.split('\t') if p.strip()]
        if len(parts) >= 4:
            try:
                new_latest_time = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                break
            except ValueError:
                continue

    if new_latest_time is None:
        return await interaction.followup.send("❌ Không đọc được mốc thời gian hợp lệ từ file log!")

    # Bước 2: Chặn nếu file cũ hơn hoặc trùng mốc đã lưu
    old_last_update_str = data.get("last_update", None)
    if old_last_update_str and old_last_update_str not in ("Chưa có dữ liệu", "N/A"):
        try:
            old_last_update = datetime.strptime(old_last_update_str, "%Y-%m-%d %H:%M:%S")
            if new_latest_time <= old_last_update:
                return await interaction.followup.send(
                    f"❌ **Log này cũ hơn hoặc trùng với mốc đã cập nhật, từ chối xử lý!**\n"
                    f"📅 Mốc hiện tại trong hệ thống: `{old_last_update_str}`\n"
                    f"📅 Mốc mới nhất trong file vừa gửi: `{new_latest_time}`\n"
                    f"⚠️ Vui lòng upload file log **mới hơn** mốc trên để tránh trùng/lùi dữ liệu."
                )
        except ValueError:
            pass

    # Bước 3: Xử lý cộng điểm
    count = 0
    time_set = False
    for line in lines:
        if "Player" in line or not line.strip(): continue
        parts = [p.strip().replace('"', '') for p in line.split('\t') if p.strip()]
        if len(parts) >= 4:
            if not time_set:
                data["last_update"] = parts[0]
                time_set = True
            try:
                player_name = parts[1]
                amount = int(parts[3])
                data["history"][player_name] = data["history"].get(player_name, 0) + amount
                count += 1
            except ValueError: continue

    save_db(data, SIPHONED_FILE)
    await interaction.followup.send(f"✅ Xử lý thành công **{count}** dòng dữ liệu log.\nMốc log: `{data['last_update']}` (Đã Sync GitHub!)")


@bot.tree.command(name="spcheck", description="Xem bảng xếp hạng tích lũy điểm Siphoned")
async def spcheck(interaction: discord.Interaction):
    data = load_db(SIPHONED_FILE, "sp")
    history = data.get("history", {})
    last_up = data.get("last_update", "N/A")
    if not history:
        return await interaction.response.send_message("📊 Hiện tại hệ thống Siphoned chưa có dữ liệu.")
    sorted_sp = sorted(history.items(), key=lambda x: x[1], reverse=True)
    view = SiphonedPaginator(sorted_sp, last_up)
    await interaction.response.send_message(embed=view.create_embed(), view=view)


@bot.command(name="addsp")
async def addsp(ctx, name: str, amt: int):
    if not is_officer(ctx.author): return await ctx.send("❌ Bạn không có quyền!")
    data = load_db(SIPHONED_FILE, "sp")
    data["history"][name] = data["history"].get(name, 0) + amt
    save_db(data, SIPHONED_FILE)
    await ctx.send(f"💎 **[SIPHONED]** Đã cộng tay **+{amt:,}** SP cho **{name}**.")


@bot.command(name="removesp")
async def removesp(ctx, name: str, amt: int):
    if not is_officer(ctx.author):
        return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
    if amt <= 0:
        return await ctx.send("⚠️ Số điểm trừ phải lớn hơn 0 bro ơi!")
    data = load_db(SIPHONED_FILE, "sp")
    if name in data["history"]:
        data["history"][name] = data["history"].get(name, 0) - amt
        save_db(data, SIPHONED_FILE)
        await ctx.send(f"📉 **[SIPHONED]** Đã trừ bớt **-{amt:,}** SP của thành viên **{name}**.\n📊 Điểm hiện tại của họ: **{data['history'][name]:,}** SP.")
    else:
        await ctx.send(f"❓ Không tìm thấy thành viên mang tên `{name}` trong bảng dữ liệu.")


@bot.command(name="removesprole")
async def removesprole(ctx, *, name: str):
    if not is_officer(ctx.author): return await ctx.send("❌ Bạn không có quyền!")
    data = load_db(SIPHONED_FILE, "sp")
    if name in data["history"]:
        del data["history"][name]
        save_db(data, SIPHONED_FILE)
        await ctx.send(f"🧹 Đã xóa hoàn toàn thành viên **{name}** ra khỏi bảng xếp hạng Siphoned.")
    else:
        await ctx.send(f"❓ Không tìm thấy thành viên `{name}`.")


@bot.command(name="resetsp")
async def resetsp(ctx):
    if not is_officer(ctx.author): return await ctx.send("❌ Bạn không có quyền!")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    await ctx.send("⚠️ Bạn có muốn đưa toàn bộ bảng điểm Siphoned về 0? Gõ `yes`.")
    try:
        msg = await bot.wait_for('message', check=check, timeout=15.0)
        if msg.content.lower() == 'yes':
            save_db({"history": {}, "last_update": "N/A"}, SIPHONED_FILE)
            await ctx.send("🧹 Toàn bộ bảng xếp hạng điểm Siphoned đã được reset!")
    except asyncio.TimeoutError: pass

# ==============================================================================
# 7. HỆ THỐNG MASSING
# ==============================================================================
MASSING_FILE = os.path.join(DATA_DIR, "tnc_massing_v1.json")
active_parties = {}
role_icons = {"Tank": "🛡️", "Heal": "💚", "SP": "💜", "DPS": "⚔️", "Caller": "👑"}


def load_massing():
    for try_path in [MASSING_FILE, MASSING_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {MASSING_FILE}")
    return {}

def save_massing():
    with _file_lock:
        tmp_path = MASSING_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(active_parties, f, ensure_ascii=False, indent=4)
        if os.path.exists(MASSING_FILE):
            shutil.copy2(MASSING_FILE, MASSING_FILE + ".bak")
        os.replace(tmp_path, MASSING_FILE)
    Thread(target=sync_to_github).start()


def parse_role_block(raw_text):
    roles = []
    weapon_slots = {}
    for raw_line in raw_text.strip().split('\n'):
        raw_line = raw_line.strip()
        if not raw_line or ':' not in raw_line:
            continue
        segments = [s.strip() for s in raw_line.split(':')]
        role_name = segments[0]
        if not role_name:
            continue
        rest = segments[1:]
        if len(rest) == 1 and rest[0].isdigit():
            limit = int(rest[0])
            if limit > 0:
                roles.append(role_name)
                weapon_slots[role_name] = [(role_name, limit)]
            continue
        weapon_part = ":".join(rest)
        if not weapon_part:
            continue
        wlist = []
        for chunk in weapon_part.split(','):
            chunk = chunk.strip()
            if ':' not in chunk:
                continue
            wname, _, wlimit = chunk.rpartition(':')
            wname = wname.strip()
            if wname and wlimit.strip().isdigit() and int(wlimit.strip()) > 0:
                wlist.append((wname, int(wlimit.strip())))
        if wlist:
            roles.append(role_name)
            weapon_slots[role_name] = wlist
    return roles, weapon_slots


def format_role_block(roles, weapon_slots):
    """Dựng lại text block role:weapon:limit từ dữ liệu roles/weapon_slots (dùng để pre-fill modal khi Copy/Template)."""
    lines = []
    for role in roles:
        wlist = weapon_slots.get(role, [])
        if not wlist:
            continue
        if len(wlist) == 1 and wlist[0][0] == role:
            lines.append(f"{role}:{wlist[0][1]}")
        else:
            parts = ",".join(f"{w}:{l}" for w, l in wlist)
            lines.append(f"{role}:{parts}")
    return "\n".join(lines)


TEMPLATES_FILE = os.path.join(DATA_DIR, "tnc_templates_v1.json")

def load_templates():
    for try_path in [TEMPLATES_FILE, TEMPLATES_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {TEMPLATES_FILE}")
    return {}

def save_templates(data):
    with _file_lock:
        tmp_path = TEMPLATES_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(TEMPLATES_FILE):
            shutil.copy2(TEMPLATES_FILE, TEMPLATES_FILE + ".bak")
        os.replace(tmp_path, TEMPLATES_FILE)
    Thread(target=sync_to_github).start()


def build_party_embed(party):
    total_filled = sum(len(members) for wmap in party["slots"].values() for members in wmap.values())
    total_slots = sum(limit for wlist in party["weapon_slots"].values() for _, limit in wlist)
    is_full = total_slots > 0 and total_filled >= total_slots

    embed = discord.Embed(title=party["name"], color=0xe74c3c)
    embed.add_field(name="👑 Caller", value=party["caller"] or "_Chưa có_", inline=True)
    embed.add_field(name="🕐 Time", value=party["time"] or "_Chưa rõ_", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="─────────────────", inline=False)

    for role in party["roles"]:
        icon = role_icons.get(role, "🔹")
        wlist = party["weapon_slots"][role]
        lines = []
        for weapon, limit in wlist:
            members = party["slots"][role].get(weapon, [])
            member_str = "\n".join(f"<@{uid}>" for uid in members) if members else "_Chưa có ai_"
            if len(wlist) == 1 and wlist[0][0] == role:
                lines.append(f"**{role}** {len(members)}/{limit}\n{member_str}")
            else:
                lines.append(f"**{weapon}** {len(members)}/{limit}\n{member_str}")
        embed.add_field(name=f"{icon} {role}", value="\n\n".join(lines) if lines else "_Trống_", inline=True)

    if total_slots > 0:
        status = "🟢 **FULL**" if is_full else f"🟡 **{total_filled}/{total_slots}**"
        embed.add_field(name="\u200b", value=f"─────────────────\n👥 {status}", inline=False)

    fills = party.get("fills", [])
    if fills:
        embed.add_field(name=f"🔄 Fill ({len(fills)} người)", value="\n".join(f"• <@{uid}>" for uid in fills), inline=False)
    elif is_full:
        embed.add_field(name="🔄 Fill", value="_Party đã full — bấm nút Fill để vào danh sách dự bị!_", inline=False)

    if party.get("note"):
        embed.add_field(name="📝 Ghi chú", value=party["note"], inline=False)

    return embed


def can_manage(party, member):
    return member.id == party["creator"] or is_officer(member)


class SlotPickSelect(discord.ui.Select):
    def __init__(self, party, parent_view, target_uid, mode):
        self.party_id = party["id"]
        self.target_uid = target_uid
        self.mode = mode
        self.parent_view = parent_view
        options = []
        for role in party["roles"]:
            for weapon, limit in party["weapon_slots"][role]:
                members = party["slots"][role].get(weapon, [])
                if len(members) >= limit:
                    continue
                display = role if (len(party["weapon_slots"][role]) == 1 and party["weapon_slots"][role][0][0] == role) else f"{role} - {weapon}"
                options.append(discord.SelectOption(label=f"{display} ({len(members)}/{limit})", value=f"{role}|{weapon}"))
        if not options:
            options.append(discord.SelectOption(label="Không còn slot trống", value="none"))
        super().__init__(placeholder="Chọn slot...", options=options[:25], min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if self.values[0] == "none":
            return await interaction.response.send_message("❌ Không còn slot trống nào!", ephemeral=True)
        role, weapon = self.values[0].split("|", 1)
        limit = dict(party["weapon_slots"][role])[weapon]
        current = party["slots"][role].setdefault(weapon, [])
        if len(current) >= limit:
            return await interaction.response.send_message("❌ Slot vừa đầy, thử lại!", ephemeral=True)
        if self.mode == "move":
            self.parent_view._remove_member_everywhere(party, self.target_uid)
        current.append(self.target_uid)
        save_massing()
        self.parent_view.rebuild_buttons()
        await interaction.response.edit_message(
            content=f"✅ Đã {'thêm' if self.mode=='add' else 'chuyển'} <@{self.target_uid}> vào **{role}-{weapon}**.",
            embed=None, view=None
        )
        try:
            await self.parent_view.refresh_original(interaction, party)
        except Exception:
            pass


class SlotPickView(discord.ui.View):
    def __init__(self, party, parent_view, target_uid, mode):
        super().__init__(timeout=86400)
        self.add_item(SlotPickSelect(party, parent_view, target_uid, mode))


class MemberPickSelect(discord.ui.Select):
    def __init__(self, party, parent_view, mode, guild):
        self.party_id = party["id"]
        self.mode = mode
        self.parent_view = parent_view
        member_ids = set()
        for role in party["roles"]:
            for weapon in party["slots"][role]:
                member_ids.update(party["slots"][role][weapon])
        member_ids.update(party.get("fills", []))
        options = []
        for uid in member_ids:
            member = guild.get_member(uid)
            name = member.display_name if member else f"User {uid}"
            options.append(discord.SelectOption(label=name, value=str(uid)))
        if not options:
            options.append(discord.SelectOption(label="Chưa có ai trong party", value="none"))
        super().__init__(placeholder="Chọn thành viên...", options=options[:25], min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if self.values[0] == "none":
            return await interaction.response.send_message("❌ Party chưa có ai để chọn!", ephemeral=True)
        target_uid = int(self.values[0])
        if self.mode == "kick":
            self.parent_view._remove_member_everywhere(party, target_uid)
            save_massing()
            self.parent_view.rebuild_buttons()
            await interaction.response.edit_message(content=f"✅ Đã kick <@{target_uid}> khỏi party.", view=None)
            try:
                await self.parent_view.refresh_original(interaction, party)
            except Exception:
                pass
        else:
            await interaction.response.edit_message(
                content=f"👉 Chọn slot mới muốn chuyển <@{target_uid}> vào:",
                view=SlotPickView(party, self.parent_view, target_uid, "move")
            )


class MemberPickView(discord.ui.View):
    def __init__(self, party, parent_view, mode, guild):
        super().__init__(timeout=86400)
        self.add_item(MemberPickSelect(party, parent_view, mode, guild))


class AddMemberSelect(discord.ui.UserSelect):
    def __init__(self, party, parent_view):
        self.party_id = party["id"]
        self.parent_view = parent_view
        super().__init__(placeholder="Tìm và chọn thành viên cần thêm...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        target = self.values[0]
        target_uid = target.id
        in_party_ids = set()
        for role in party["roles"]:
            for weapon in party["slots"][role]:
                in_party_ids.update(party["slots"][role][weapon])
        in_party_ids.update(party.get("fills", []))
        if target_uid in in_party_ids:
            return await interaction.response.send_message(
                f"⚠️ **{target.display_name}** đã có trong party rồi!", ephemeral=True
            )
        await interaction.response.edit_message(
            content=f"👉 Chọn slot muốn thêm **{target.display_name}** vào:",
            view=SlotPickView(party, self.parent_view, target_uid, "add")
        )


class AddMemberView(discord.ui.View):
    def __init__(self, party, parent_view, guild=None):
        super().__init__(timeout=86400)
        self.add_item(AddMemberSelect(party, parent_view))


class PartyView(discord.ui.View):
    def __init__(self, party_id):
        super().__init__(timeout=None)
        self.party_id = party_id
        self.rebuild_buttons()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        try:
            await interaction.response.send_message("❌ Party hết hạn do bot restart. Tạo party mới nhé!", ephemeral=True)
        except: pass

    async def refresh_original(self, interaction, party):
        try:
            msg = await interaction.channel.fetch_message(int(self.party_id))
            await msg.edit(embed=build_party_embed(party), view=self)
        except Exception as e:
            print(f"⚠️ Không refresh được message gốc: {e}")

    def rebuild_buttons(self):
        self.clear_items()
        party = active_parties.get(self.party_id)
        if not party: return

        is_party_full = self._is_full(party)
        styles = [discord.ButtonStyle.blurple, discord.ButtonStyle.green, discord.ButtonStyle.gray, discord.ButtonStyle.primary]
        style_idx = 0

        for role in party["roles"]:
            wlist = party["weapon_slots"][role]
            is_single = len(wlist) == 1 and wlist[0][0] == role
            for weapon, limit in wlist:
                members = party["slots"][role].get(weapon, [])
                filled = len(members)
                label = f"{role} {filled}/{limit}" if is_single else f"{role}-{weapon} {filled}/{limit}"
                btn = discord.ui.Button(
                    label=label,
                    style=styles[style_idx % len(styles)],
                    custom_id=f"join_{self.party_id}_{role}_{weapon}",
                    disabled=filled >= limit
                )
                btn.callback = self.make_join_callback(role, weapon)
                self.add_item(btn)
            style_idx += 1

        if party["roles"]:
            fill_btn = discord.ui.Button(
                label=f"🔄 Fill ({len(party.get('fills', []))})",
                style=discord.ButtonStyle.secondary,
                custom_id=f"fill_{self.party_id}",
                disabled=not is_party_full
            )
            fill_btn.callback = self.fill_callback
            self.add_item(fill_btn)

        leave_btn = discord.ui.Button(label="❌ Leave", style=discord.ButtonStyle.red, custom_id=f"leave_{self.party_id}")
        leave_btn.callback = self.leave_callback
        self.add_item(leave_btn)

        add_btn = discord.ui.Button(label="➕ Add", style=discord.ButtonStyle.success, custom_id=f"add_{self.party_id}")
        add_btn.callback = self.add_callback
        self.add_item(add_btn)

        move_btn = discord.ui.Button(label="🔀 Move", style=discord.ButtonStyle.primary, custom_id=f"move_{self.party_id}")
        move_btn.callback = self.move_callback
        self.add_item(move_btn)

        kick_btn = discord.ui.Button(label="👋 Kick", style=discord.ButtonStyle.danger, custom_id=f"kick_{self.party_id}")
        kick_btn.callback = self.kick_callback
        self.add_item(kick_btn)

        note_btn = discord.ui.Button(label="📝 Note", style=discord.ButtonStyle.secondary, custom_id=f"note_{self.party_id}")
        note_btn.callback = self.note_callback
        self.add_item(note_btn)

        del_btn = discord.ui.Button(label="🗑️ Delete", style=discord.ButtonStyle.danger, custom_id=f"delete_{self.party_id}")
        del_btn.callback = self.delete_callback
        self.add_item(del_btn)

        copy_btn = discord.ui.Button(label="📋 Copy", style=discord.ButtonStyle.secondary, custom_id=f"copy_{self.party_id}")
        copy_btn.callback = self.copy_callback
        self.add_item(copy_btn)

        savetpl_btn = discord.ui.Button(label="💾 Save Template", style=discord.ButtonStyle.secondary, custom_id=f"savetpl_{self.party_id}")
        savetpl_btn.callback = self.save_template_callback
        self.add_item(savetpl_btn)

        ping_btn = discord.ui.Button(label="📢 Ping All", style=discord.ButtonStyle.secondary, custom_id=f"ping_{self.party_id}")
        ping_btn.callback = self.ping_callback
        self.add_item(ping_btn)

    def _is_full(self, party):
        total_filled = sum(len(m) for wmap in party["slots"].values() for m in wmap.values())
        total_slots = sum(limit for wlist in party["weapon_slots"].values() for _, limit in wlist)
        return total_slots > 0 and total_filled >= total_slots

    def _remove_member_everywhere(self, party, uid):
        removed = False
        for role in party["roles"]:
            for weapon in list(party["slots"][role].keys()):
                if uid in party["slots"][role][weapon]:
                    party["slots"][role][weapon].remove(uid)
                    removed = True
        if uid in party.get("fills", []):
            party["fills"].remove(uid)
            removed = True
        return removed

    def make_join_callback(self, role, weapon):
        async def callback(interaction: discord.Interaction):
            party = active_parties.get(self.party_id)
            if not party:
                return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
            uid = interaction.user.id
            self._remove_member_everywhere(party, uid)
            limit = dict(party["weapon_slots"][role])[weapon]
            current = party["slots"][role].setdefault(weapon, [])
            if len(current) >= limit:
                return await interaction.response.send_message(f"❌ Slot **{role}-{weapon}** vừa đầy!", ephemeral=True)
            current.append(uid)
            save_massing()
            self.rebuild_buttons()
            await interaction.response.edit_message(embed=build_party_embed(party), view=self)
        return callback

    async def fill_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not self._is_full(party):
            return await interaction.response.send_message("⚠️ Party chưa full!", ephemeral=True)
        uid = interaction.user.id
        for role in party["roles"]:
            for weapon in party["slots"][role]:
                if uid in party["slots"][role][weapon]:
                    return await interaction.response.send_message("⚠️ Bạn đã có slot chính thức rồi!", ephemeral=True)
        if uid in party.get("fills", []):
            return await interaction.response.send_message("⚠️ Bạn đã trong danh sách Fill rồi!", ephemeral=True)
        party.setdefault("fills", []).append(uid)
        save_massing()
        self.rebuild_buttons()
        await interaction.response.edit_message(embed=build_party_embed(party), view=self)

    async def leave_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        uid = interaction.user.id
        if not self._remove_member_everywhere(party, uid):
            return await interaction.response.send_message("⚠️ Bạn chưa đăng ký party này.", ephemeral=True)
        save_massing()
        self.rebuild_buttons()
        await interaction.response.edit_message(embed=build_party_embed(party), view=self)

    async def add_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới dùng được!", ephemeral=True)
        if not party["roles"]:
            return await interaction.response.send_message("❌ Party này không có role nào!", ephemeral=True)
        await interaction.response.send_message("👉 Chọn thành viên cần thêm:", view=AddMemberView(party, self, interaction.guild), ephemeral=True)

    async def move_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới dùng được!", ephemeral=True)
        await interaction.response.send_message("👉 Chọn thành viên muốn chuyển slot:", view=MemberPickView(party, self, "move", interaction.guild), ephemeral=True)

    async def kick_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới dùng được!", ephemeral=True)
        await interaction.response.send_message("👉 Chọn thành viên muốn kick:", view=MemberPickView(party, self, "kick", interaction.guild), ephemeral=True)

    async def note_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới sửa được!", ephemeral=True)
        await interaction.response.send_modal(NoteModal(self.party_id, self))

    async def delete_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo hoặc Officer mới xóa được!", ephemeral=True)
        del active_parties[self.party_id]
        save_massing()
        await interaction.response.edit_message(content="🗑️ **Party đã bị xóa.**", embed=None, view=None)

    async def copy_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        roles_text = format_role_block(party["roles"], party["weapon_slots"])
        modal = MassingModal(
            prefill_roles=roles_text,
            prefill_note=party.get("note", ""),
            prefill_caller=party.get("caller", "")
        )
        await interaction.response.send_modal(modal)

    async def save_template_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới dùng được!", ephemeral=True)
        if not party["roles"]:
            return await interaction.response.send_message("❌ Party này không có role nào để lưu template!", ephemeral=True)
        await interaction.response.send_modal(SaveTemplateModal(party))

    async def ping_callback(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        if not can_manage(party, interaction.user):
            return await interaction.response.send_message("❌ Chỉ người tạo party hoặc Officer mới dùng được!", ephemeral=True)
        member_ids = set()
        for role in party["roles"]:
            for weapon in party["slots"][role]:
                member_ids.update(party["slots"][role][weapon])
        member_ids.update(party.get("fills", []))
        if not member_ids:
            return await interaction.response.send_message("⚠️ Party chưa có ai để ping!", ephemeral=True)
        await interaction.response.send_modal(PingAllModal(list(member_ids)))


class MassingModal(discord.ui.Modal, title="⚔️ Tạo Massing"):
    party_name = discord.ui.TextInput(label="Tên Party", placeholder="Ví dụ: PVP: SMC, Bom Squad, RZ Brawl Clap...", max_length=80)
    party_time = discord.ui.TextInput(label="Thời gian (có thể để trống)", placeholder="Ví dụ: 5/6 20:00", required=False, max_length=30)
    party_caller = discord.ui.TextInput(label="Caller (có thể để trống)", placeholder="Tên Caller hoặc để trống...", required=False, max_length=50)
    party_roles = discord.ui.TextInput(
        label="Role (mỗi role 1 dòng, có thể để trống)",
        placeholder="DPS:Realm:2,Iron:1\nHeal:Hallow:1,Redemption:1\nTank:2\nSP:1",
        style=discord.TextStyle.paragraph, required=False, max_length=500
    )
    party_note = discord.ui.TextInput(
        label="Ghi chú (có thể để trống)",
        placeholder="Ví dụ: Fill pt1 trước, all heal mặc giáp da...",
        style=discord.TextStyle.paragraph, required=False, max_length=300
    )

    def __init__(self, prefill_roles=None, prefill_note=None, prefill_caller=None):
        super().__init__()
        if prefill_roles:
            self.party_roles.default = prefill_roles
        if prefill_note:
            self.party_note.default = prefill_note
        if prefill_caller:
            self.party_caller.default = prefill_caller

    async def on_submit(self, interaction: discord.Interaction):
        caller = self.party_caller.value.strip() if self.party_caller.value else ""
        time_str = self.party_time.value.strip() if self.party_time.value else ""
        note = self.party_note.value.strip() if self.party_note.value else ""
        roles, weapon_slots = parse_role_block(self.party_roles.value or "")
        party_id = str(interaction.id)
        party_data = {
            "id": party_id,
            "name": self.party_name.value.strip(),
            "caller": caller, "time": time_str,
            "roles": roles, "weapon_slots": weapon_slots,
            "slots": {r: {} for r in roles},
            "fills": [], "note": note,
            "creator": interaction.user.id
        }
        active_parties[party_id] = party_data
        view = PartyView(party_id)
        await interaction.response.send_message(embed=build_party_embed(party_data), view=view)
        msg = await interaction.original_response()
        active_parties[str(msg.id)] = active_parties.pop(party_id)
        active_parties[str(msg.id)]["id"] = str(msg.id)
        view.party_id = str(msg.id)
        save_massing()
        await msg.edit(embed=build_party_embed(active_parties[str(msg.id)]), view=view)


class NoteModal(discord.ui.Modal, title="📝 Sửa Ghi chú"):
    note_text = discord.ui.TextInput(
        label="Ghi chú", placeholder="Ví dụ: Fill pt1 trước, all heal mặc giáp da...",
        style=discord.TextStyle.paragraph, required=False, max_length=300
    )

    def __init__(self, party_id, parent_view):
        super().__init__()
        self.party_id = party_id
        self.parent_view = parent_view
        party = active_parties.get(party_id)
        if party and party.get("note"):
            self.note_text.default = party["note"]

    async def on_submit(self, interaction: discord.Interaction):
        party = active_parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("❌ Party hết hạn do bot restart.", ephemeral=True)
        party["note"] = self.note_text.value.strip() if self.note_text.value else ""
        save_massing()
        await interaction.response.edit_message(embed=build_party_embed(party), view=self.parent_view)


class ConfirmOverwriteTemplateView(discord.ui.View):
    def __init__(self, name, key, party):
        super().__init__(timeout=30)
        self.name = name
        self.key = key
        self.party = party

    @discord.ui.button(label="✅ Ghi đè", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        templates = load_templates()
        templates[self.key] = {
            "display_name": self.name,
            "roles": self.party["roles"],
            "weapon_slots": self.party["weapon_slots"],
            "note": self.party.get("note", "")
        }
        save_templates(templates)
        await interaction.response.edit_message(content=f"✅ Đã ghi đè template **{self.name}**!", view=None)

    @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🚫 Đã hủy, không ghi đè template.", view=None)


class SaveTemplateModal(discord.ui.Modal, title="💾 Lưu Template"):
    template_name = discord.ui.TextInput(
        label="Tên Template", placeholder="Ví dụ: PVP Standard, ZvZ 20...", max_length=50
    )

    def __init__(self, party):
        super().__init__()
        self.party = party

    async def on_submit(self, interaction: discord.Interaction):
        name = self.template_name.value.strip()
        key = name.lower()
        templates = load_templates()
        if key in templates:
            view = ConfirmOverwriteTemplateView(name, key, self.party)
            return await interaction.response.send_message(
                f"⚠️ Template **{name}** đã tồn tại. Bạn có muốn ghi đè không?", view=view, ephemeral=True
            )
        templates[key] = {
            "display_name": name,
            "roles": self.party["roles"],
            "weapon_slots": self.party["weapon_slots"],
            "note": self.party.get("note", "")
        }
        save_templates(templates)
        await interaction.response.send_message(f"✅ Đã lưu template **{name}**!", ephemeral=True)


class PingAllModal(discord.ui.Modal, title="📢 Ping All Party"):
    ping_message = discord.ui.TextInput(
        label="Nội dung nhắn",
        placeholder="Ví dụ: Chuẩn bị mass, tập hợp nhanh!",
        style=discord.TextStyle.paragraph, required=True, max_length=300
    )

    def __init__(self, member_ids):
        super().__init__()
        self.member_ids = member_ids

    async def on_submit(self, interaction: discord.Interaction):
        mentions = " ".join(f"<@{uid}>" for uid in self.member_ids)
        content = f"📢 {self.ping_message.value.strip()}\n{mentions}"
        await interaction.response.send_message(content)


async def template_autocomplete(interaction: discord.Interaction, current: str):
    templates = load_templates()
    choices = []
    for key, t in templates.items():
        name = t.get("display_name", key)
        if current.lower() in name.lower():
            choices.append(app_commands.Choice(name=name, value=key))
    return choices[:25]


@bot.tree.command(name="massing", description="Tạo party Massing (PVP/PVE/...) cho Guild TNC")
@app_commands.describe(template="Dùng template đã lưu (không bắt buộc, để trống nếu tạo mới hoàn toàn)")
@app_commands.autocomplete(template=template_autocomplete)
async def massing_slash(interaction: discord.Interaction, template: str = None):
    try:
        if template:
            templates = load_templates()
            t = templates.get(template.lower())
            if not t:
                return await interaction.response.send_message(f"❌ Không tìm thấy template `{template}`!", ephemeral=True)
            roles_text = format_role_block(t.get("roles", []), t.get("weapon_slots", {}))
            modal = MassingModal(prefill_roles=roles_text, prefill_note=t.get("note", ""))
        else:
            modal = MassingModal()
        await interaction.response.send_modal(modal)
    except discord.HTTPException:
        pass


@bot.tree.command(name="masstemplatelist", description="Xem danh sách template Massing hiện có")
async def masstemplatelist_cmd(interaction: discord.Interaction):
    templates = load_templates()
    if not templates:
        return await interaction.response.send_message("📋 Chưa có template nào được lưu.", ephemeral=True)
    lines = []
    for key, t in templates.items():
        name = t.get("display_name", key)
        role_count = len(t.get("roles", []))
        slot_count = sum(limit for wlist in t.get("weapon_slots", {}).values() for _, limit in wlist)
        lines.append(f"• **{name}** — {role_count} role, {slot_count} slot")
    embed = discord.Embed(title=f"📋 Template Massing ({len(templates)})", description="\n".join(lines), color=0x3498db)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="masstemplatedelete", description="Xóa template Massing (Officer only)")
@app_commands.describe(template="Tên template cần xóa")
@app_commands.autocomplete(template=template_autocomplete)
async def masstemplatedelete_cmd(interaction: discord.Interaction, template: str):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Chỉ Officer mới dùng được lệnh này!", ephemeral=True)
    templates = load_templates()
    key = template.lower()
    if key not in templates:
        return await interaction.response.send_message(f"❓ Không tìm thấy template `{template}`.", ephemeral=True)
    name = templates[key].get("display_name", template)
    del templates[key]
    save_templates(templates)
    await interaction.response.send_message(f"🧹 Đã xóa template **{name}**.", ephemeral=True)


# ==============================================================================
# 8. HỆ THỐNG FILTER THÀNH VIÊN
# ==============================================================================
LASTSEEN_FILE = os.path.join(DATA_DIR, "tnc_lastseen_v1.json")
lastseen_cache = {}
lastseen_dirty = False

def load_lastseen():
    for try_path in [LASTSEEN_FILE, LASTSEEN_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {LASTSEEN_FILE}")
    return {}

def save_lastseen(data):
    with _file_lock:
        tmp_path = LASTSEEN_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(LASTSEEN_FILE):
            shutil.copy2(LASTSEEN_FILE, LASTSEEN_FILE + ".bak")
        os.replace(tmp_path, LASTSEEN_FILE)

async def lastseen_flush_loop():
    global lastseen_dirty
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300)
        if lastseen_dirty:
            save_lastseen(lastseen_cache)
            lastseen_dirty = False
            print("💾 [LastSeen] Đã lưu xuống file (định kỳ 5 phút).")

@bot.event
async def on_message(message):
    global lastseen_dirty
    if message.author.bot:
        return
    lastseen_cache[str(message.author.id)] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    lastseen_dirty = True

    # [Core-Bank] Tự động react vào ảnh nếu tính năng được bật
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
                    return # Đã tách ảnh xong, dừng xử lý tin nhắn gốc

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


    # [ALO-TTS] Tự động đọc chat trong voice channel bot đang có mặt
    if message.guild and isinstance(message.channel, discord.VoiceChannel) and not message.content.startswith(("!", ".")):
        session = voice_sessions.get(message.guild.id)
        if session and session.get("channel_id") == message.channel.id:
            text = clean_text_for_tts(message)
            if text:
                await enqueue_tts(message.guild, text, message.author.display_name)

    await bot.process_commands(message)





# ==============================================================================
# 9. HỆ THỐNG REGISTER + GUILDCHECK (Đăng ký IGN & tự xóa role nếu rời guild)
# ==============================================================================
REGISTER_FILE = os.path.join(DATA_DIR, "tnc_register_v1.json")
GUILDCHECK_CONFIG_FILE = os.path.join(DATA_DIR, "tnc_guildcheck_v1.json")
UNRESOLVED_FILE = os.path.join(DATA_DIR, "tnc_unresolved_v1.json")
REGION_API_BASE = {
    "Americas": "https://gameinfo.albiononline.com/api/gameinfo",
    "Asia": "https://gameinfo-sgp.albiononline.com/api/gameinfo",
    "Europe": "https://gameinfo-ams.albiononline.com/api/gameinfo",
}


def load_register():
    for try_path in [REGISTER_FILE, REGISTER_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {REGISTER_FILE}")
    return {}

def save_register(data):
    with _file_lock:
        tmp_path = REGISTER_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(REGISTER_FILE):
            shutil.copy2(REGISTER_FILE, REGISTER_FILE + ".bak")
        os.replace(tmp_path, REGISTER_FILE)
    Thread(target=sync_to_github).start()

def load_guildcheck_config():
    for try_path in [GUILDCHECK_CONFIG_FILE, GUILDCHECK_CONFIG_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {GUILDCHECK_CONFIG_FILE}")
    return {"guild_id": "", "log_channel_id": "", "officer_role_id": "", "member_role_id": ""}

def save_guildcheck_config(data):
    with _file_lock:
        tmp_path = GUILDCHECK_CONFIG_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(GUILDCHECK_CONFIG_FILE):
            shutil.copy2(GUILDCHECK_CONFIG_FILE, GUILDCHECK_CONFIG_FILE + ".bak")
        os.replace(tmp_path, GUILDCHECK_CONFIG_FILE)
    Thread(target=sync_to_github).start()

def load_unresolved():
    for try_path in [UNRESOLVED_FILE, UNRESOLVED_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {UNRESOLVED_FILE}")
    return {}

def save_unresolved(data):
    with _file_lock:
        tmp_path = UNRESOLVED_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(UNRESOLVED_FILE):
            shutil.copy2(UNRESOLVED_FILE, UNRESOLVED_FILE + ".bak")
        os.replace(tmp_path, UNRESOLVED_FILE)
    Thread(target=sync_to_github).start()


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


@bot.tree.command(name="registertnc", description="Đăng ký nhân vật Albion để bot check guild")
@app_commands.describe(region="Server Albion bạn đang chơi", albion_nick="Tên nhân vật trong game (chính xác)")
@app_commands.choices(region=[
    app_commands.Choice(name="Americas", value="Americas"),
    app_commands.Choice(name="Asia", value="Asia"),
    app_commands.Choice(name="Europe", value="Europe"),
])
async def registertnc_cmd(interaction: discord.Interaction, region: app_commands.Choice[str], albion_nick: str):
    data = load_register()
    data[str(interaction.user.id)] = {"ign": albion_nick.strip(), "region": region.value}
    save_register(data)
    await interaction.response.send_message(
        f"✅ Đã đăng ký nhân vật **{albion_nick.strip()}** (server **{region.value}**)", ephemeral=True
    )


@bot.tree.command(name="registerfor", description="Đăng ký IGN Albion cho member khác (Officer only)")
@app_commands.describe(member="Member cần đăng ký", region="Server Albion", albion_nick="Tên nhân vật trong game")
@app_commands.choices(region=[
    app_commands.Choice(name="Americas", value="Americas"),
    app_commands.Choice(name="Asia", value="Asia"),
    app_commands.Choice(name="Europe", value="Europe"),
])
async def registerfor_cmd(interaction: discord.Interaction, member: discord.Member, region: app_commands.Choice[str], albion_nick: str):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    data = load_register()
    data[str(member.id)] = {"ign": albion_nick.strip(), "region": region.value}
    save_register(data)
    await interaction.response.send_message(
        f"✅ Đã đăng ký **{albion_nick.strip()}** (server **{region.value}**) cho {member.mention}", ephemeral=True
    )


@bot.tree.command(name="myign", description="Xem IGN Albion đã đăng ký")
async def myign_cmd(interaction: discord.Interaction):
    data = load_register()
    info = data.get(str(interaction.user.id))
    if not info:
        return await interaction.response.send_message("❓ Bạn chưa đăng ký. Dùng `/registertnc`!", ephemeral=True)
    await interaction.response.send_message(
        f"🎮 IGN: **{info.get('ign')}** | Server: **{info.get('region')}**", ephemeral=True
    )


@bot.tree.command(name="guildconfig", description="Cấu hình Guild ID, log channel, officer role & member role cho GuildCheck (Officer only)")
@app_commands.describe(
    guild_id="Guild ID Albion của TNC (lấy từ URL killboard guild)",
    log_channel="Channel nhận log khi xóa role / cập nhật unresolved",
    officer_role="Role sẽ bị tag khi danh sách unresolved thay đổi",
    member_role="Role sẽ bị bot tự xóa nếu thành viên rời guild Albion (vd: TNC Member)"
)
async def guildconfig_cmd(
    interaction: discord.Interaction,
    guild_id: str = None,
    log_channel: discord.TextChannel = None,
    officer_role: discord.Role = None,
    member_role: discord.Role = None
):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    config = load_guildcheck_config()
    if guild_id: config["guild_id"] = guild_id.strip()
    if log_channel: config["log_channel_id"] = str(log_channel.id)
    if officer_role: config["officer_role_id"] = str(officer_role.id)
    if member_role: config["member_role_id"] = str(member_role.id)
    save_guildcheck_config(config)

    lines = [f"🆔 Guild ID: `{config.get('guild_id') or 'chưa có'}`"]
    lines.append(f"📢 Log channel: <#{config['log_channel_id']}>" if config.get("log_channel_id") else "📢 Log channel: chưa có")
    lines.append(f"👮 Officer role: <@&{config['officer_role_id']}>" if config.get("officer_role_id") else "👮 Officer role: chưa có")
    lines.append(f"🛡️ Member role: <@&{config['member_role_id']}>" if config.get("member_role_id") else "🛡️ Member role: chưa có")
    await interaction.response.send_message("✅ Đã lưu config:\n" + "\n".join(lines), ephemeral=True)


async def run_guildcheck(guild: discord.Guild):
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
        try: await channel.send(embed=embed)
        except Exception: pass

    if set(new_unresolved.keys()) != set(old_unresolved.keys()) and channel:
        officer_role_id = config.get("officer_role_id")
        mention = f"<@&{officer_role_id}>" if officer_role_id else None
        if new_unresolved:
            desc = "\n".join(f"• <@{uid}> — IGN đăng ký: `{ign}`" for uid, ign in new_unresolved.items())
        else:
            desc = "✅ Danh sách trống, không còn ai cần xử lý tay."
        embed = discord.Embed(title="⚠️ Danh sách Unresolved đã cập nhật", description=desc, color=0xf39c12)
        try: await channel.send(content=mention, embed=embed)
        except Exception: pass

    return removed, None


@bot.tree.command(name="guildcheck", description="Chạy tay check thành viên rời guild Albion (Officer only)")
async def guildcheck_cmd(interaction: discord.Interaction):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    removed, err = await run_guildcheck(interaction.guild)
    if err:
        return await interaction.followup.send(err, ephemeral=True)
    if not removed:
        return await interaction.followup.send(
            "✅ Check xong, không có ai bị xóa role. (Xem `/unresolved` nếu có người cần xử lý tay)", ephemeral=True
        )
    desc = "\n".join(f"• {m.mention} (IGN: `{ign}`)" for m, ign in removed)
    await interaction.followup.send(f"🧹 Đã xóa role `TNC_Member` của **{len(removed)}** người:\n{desc}", ephemeral=True)


@bot.tree.command(name="unresolved", description="Xem danh sách chưa xác định được guild, cần xử lý tay (Officer only)")
async def unresolved_cmd(interaction: discord.Interaction):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    data = load_unresolved()
    if not data:
        return await interaction.response.send_message("✅ Danh sách unresolved đang trống.", ephemeral=True)
    desc = "\n".join(f"• <@{uid}> — IGN đăng ký: `{ign}`" for uid, ign in data.items())
    embed = discord.Embed(title=f"⚠️ Unresolved — {len(data)} người", description=desc, color=0xf39c12)
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def guildcheck_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            config = load_guildcheck_config()
            if config.get("guild_id"):
                for guild in bot.guilds:
                    await run_guildcheck(guild)
        except Exception as e:
            print(f"❌ [GuildCheck] Lỗi: {e}")
        await asyncio.sleep(6 * 3600)  # check mỗi 6 tiếng

# ==============================================================================
# 11. HỆ THỐNG TTS VOICE "ALO" (Bot join voice, đọc chat bằng giọng Google TTS)
# ==============================================================================
TTS_CONFIG_FILE = os.path.join(DATA_DIR, "tnc_tts_config_v1.json")

# voice_sessions[guild_id] = {"channel_id": int, "intentional_leave": bool}
voice_sessions = {}
# mute_state[guild_id] = True/False (tạm tắt tiếng đọc, bot vẫn ở lại voice)
mute_state = {}
# tts_queues[guild_id] = asyncio.Queue chứa text cần đọc
tts_queues = {}
# tts_workers[guild_id] = asyncio.Task đang xử lý queue
tts_workers = {}

MENTION_RE = re.compile(r"<@!?(\d+)>")
CHANNEL_MENTION_RE = re.compile(r"<#(\d+)>")
CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):\d+>")
URL_RE = re.compile(r"https?://\S+")


def load_tts_config():
    for try_path in [TTS_CONFIG_FILE, TTS_CONFIG_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    print(f"❌ [Data] Không đọc được dữ liệu từ: {TTS_CONFIG_FILE}")
    return {"read_name": {}, "rejoin": {}}

def save_tts_config(data):
    with _file_lock:
        tmp_path = TTS_CONFIG_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(TTS_CONFIG_FILE):
            shutil.copy2(TTS_CONFIG_FILE, TTS_CONFIG_FILE + ".bak")
        os.replace(tmp_path, TTS_CONFIG_FILE)
    Thread(target=sync_to_github).start()


def clean_text_for_tts(message: discord.Message) -> str:
    """Làm sạch nội dung tin nhắn trước khi đưa qua TTS (mention, link, emoji custom...)."""
    text = message.content or ""
    text = URL_RE.sub("đường link", text)

    def repl_mention(m):
        uid = int(m.group(1))
        member = message.guild.get_member(uid) if message.guild else None
        return member.display_name if member else "ai đó"

    def repl_channel(m):
        ch = message.guild.get_channel(int(m.group(1))) if message.guild else None
        return f"kênh {ch.name}" if ch else "một kênh"

    text = MENTION_RE.sub(repl_mention, text)
    text = CHANNEL_MENTION_RE.sub(repl_channel, text)
    text = CUSTOM_EMOJI_RE.sub(lambda m: m.group(1), text)
    return text.strip()


def generate_tts_file(text: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".mp3", dir=DATA_DIR)
    os.close(fd)
    tts = gTTS(text=text, lang="vi")
    tts.save(path)
    return path


async def enqueue_tts(guild: discord.Guild, text: str, author_name: str):
    if not text or not text.strip():
        return
    gid = guild.id
    config = load_tts_config()
    read_name = config.get("read_name", {}).get(str(gid), True)
    full_text = f"{author_name} nói: {text}" if read_name else text

    if gid not in tts_queues:
        tts_queues[gid] = asyncio.Queue()
    await tts_queues[gid].put(full_text)

    if gid not in tts_workers or tts_workers[gid].done():
        tts_workers[gid] = bot.loop.create_task(tts_worker(gid))


async def tts_worker(guild_id):
    queue = tts_queues[guild_id]
    while not queue.empty():
        text = await queue.get()
        if mute_state.get(guild_id):
            continue
        session = voice_sessions.get(guild_id)
        if not session:
            continue
        guild = bot.get_guild(guild_id)
        vc = guild.voice_client if guild else None
        if not vc or not vc.is_connected():
            continue

        try:
            path = await bot.loop.run_in_executor(None, generate_tts_file, text)
        except Exception as e:
            print(f"❌ [ALO-TTS] Lỗi tạo audio: {e}")
            continue

        finished = asyncio.Event()

        def after_play(err, path=path):
            try:
                os.remove(path)
            except Exception:
                pass
            bot.loop.call_soon_threadsafe(finished.set)

        try:
            while vc.is_playing():
                await asyncio.sleep(0.5)
            # Giới hạn tối đa 1 phút/đoạn bằng option ffmpeg "-t 60"
            vc.play(discord.FFmpegPCMAudio(path, options="-t 60"), after=after_play)
            await finished.wait()
        except Exception as e:
            print(f"❌ [ALO-TTS] Lỗi phát audio: {e}")


@bot.tree.command(name="alojoin", description="Bot join (hoặc kéo qua) voice channel bạn đang đứng")
async def alojoin_cmd(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        return await interaction.response.send_message("❌ Bạn phải đang ở trong 1 voice channel!", ephemeral=True)
    channel = interaction.user.voice.channel
    guild = interaction.guild
    vc = guild.voice_client

    if vc and vc.channel.id == channel.id:
        return await interaction.response.send_message(f"✅ Bot đã ở **{channel.name}** rồi!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    try:
        if vc:
            await vc.move_to(channel)
        else:
            await channel.connect()
        voice_sessions[guild.id] = {"channel_id": channel.id, "intentional_leave": False}
        mute_state[guild.id] = False
        await interaction.followup.send(f"✅ Bot đã vào **{channel.name}**! Cứ nhắn chat trong voice là bot đọc.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Không thể join voice: {e}", ephemeral=True)


@bot.tree.command(name="aloleave", description="Bot rời voice hiện tại")
async def aloleave_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    vc = guild.voice_client
    if not vc:
        return await interaction.response.send_message("❌ Bot không ở voice nào cả!", ephemeral=True)

    session = voice_sessions.get(guild.id, {})
    session["intentional_leave"] = True
    voice_sessions[guild.id] = session

    channel_name = vc.channel.name
    await vc.disconnect()
    voice_sessions.pop(guild.id, None)
    mute_state.pop(guild.id, None)
    await interaction.response.send_message(f"👋 Bot đã rời **{channel_name}**.", ephemeral=True)


@bot.tree.command(name="alonametoggle", description="Bật/tắt đọc tên người gửi trước nội dung (áp dụng toàn server)")
async def alonametoggle_cmd(interaction: discord.Interaction):
    config = load_tts_config()
    read_name_cfg = config.setdefault("read_name", {})
    gid = str(interaction.guild.id)
    current = read_name_cfg.get(gid, True)
    read_name_cfg[gid] = not current
    save_tts_config(config)
    state = "BẬT ✅" if read_name_cfg[gid] else "TẮT ❌"
    await interaction.response.send_message(f"🔊 Đọc tên người gửi: **{state}** (áp dụng cho toàn bộ server)", ephemeral=True)


@bot.tree.command(name="alo", description="Gửi TTS vào 1 voice channel cụ thể mà không cần đang đứng trong đó")
@app_commands.describe(voice="Voice channel bot đang có mặt", noi_dung="Nội dung muốn đọc")
async def alo_cmd(interaction: discord.Interaction, voice: discord.VoiceChannel, noi_dung: str):
    guild = interaction.guild
    vc = guild.voice_client
    if not vc or vc.channel.id != voice.id:
        return await interaction.response.send_message(f"❌ Bot chưa vào voice **{voice.name}**! Dùng `/alojoin` trước.", ephemeral=True)
    if mute_state.get(guild.id):
        return await interaction.response.send_message("🔇 Bot đang bị mute ở voice này, dùng `/alounmute` trước.", ephemeral=True)

    await enqueue_tts(guild, noi_dung.strip(), interaction.user.display_name)
    await interaction.response.send_message(f"📢 Đã gửi vào hàng chờ đọc ở **{voice.name}**!", ephemeral=True)


@bot.tree.command(name="aloconfig", description="Cấu hình tự động rejoin khi bị kick/rớt mạng cho 1 voice channel (Officer only)")
@app_commands.describe(rejoin="Bật/tắt tự động rejoin", voice="Voice channel cần config (mặc định = voice bot đang ở)")
@app_commands.choices(rejoin=[
    app_commands.Choice(name="Bật", value="on"),
    app_commands.Choice(name="Tắt", value="off"),
])
async def aloconfig_cmd(interaction: discord.Interaction, rejoin: app_commands.Choice[str], voice: discord.VoiceChannel = None):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

    target_channel = voice
    if not target_channel:
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Bot chưa ở voice nào, vui lòng chỉ định `voice:`!", ephemeral=True)
        target_channel = vc.channel

    config = load_tts_config()
    rejoin_cfg = config.setdefault("rejoin", {})
    rejoin_cfg[str(target_channel.id)] = (rejoin.value == "on")
    save_tts_config(config)
    state = "BẬT ✅" if rejoin.value == "on" else "TẮT ❌"
    await interaction.response.send_message(f"⚙️ Tự động rejoin cho **{target_channel.name}**: **{state}**", ephemeral=True)


@bot.tree.command(name="alomute", description="Tạm tắt tiếng đọc TTS ở voice hiện tại (bot vẫn ở lại)")
async def alomute_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild.voice_client:
        return await interaction.response.send_message("❌ Bot không ở voice nào cả!", ephemeral=True)
    mute_state[guild.id] = True
    await interaction.response.send_message("🔇 Đã tắt tiếng đọc TTS (bot vẫn ở lại voice).", ephemeral=True)


@bot.tree.command(name="alounmute", description="Bật lại tiếng đọc TTS ở voice hiện tại")
async def alounmute_cmd(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild.voice_client:
        return await interaction.response.send_message("❌ Bot không ở voice nào cả!", ephemeral=True)
    mute_state[guild.id] = False
    await interaction.response.send_message("🔊 Đã bật lại tiếng đọc TTS.", ephemeral=True)


@bot.event
async def on_voice_state_update(member, before, after):
    """Xử lý tự động rejoin khi bot bị kick khỏi voice / rớt mạng."""
    if member.id != bot.user.id:
        return
    guild = member.guild

    if before.channel is not None and after.channel is None:
        session = voice_sessions.get(guild.id)
        if session and session.get("intentional_leave"):
            voice_sessions.pop(guild.id, None)
            mute_state.pop(guild.id, None)
            return

        channel_id = before.channel.id
        rejoin_cfg = load_tts_config().get("rejoin", {})
        if rejoin_cfg.get(str(channel_id)):
            await asyncio.sleep(3)
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.connect()
                    voice_sessions[guild.id] = {"channel_id": channel.id, "intentional_leave": False}
                    print(f"🔄 [ALO] Đã tự rejoin lại {channel.name}")
                except Exception as e:
                    print(f"⚠️ [ALO] Rejoin thất bại: {e}")
                    voice_sessions.pop(guild.id, None)
            else:
                voice_sessions.pop(guild.id, None)
        else:
            voice_sessions.pop(guild.id, None)
            mute_state.pop(guild.id, None)


# ==============================================================================
# 10. HỆ THỐNG CORE-BANK (Tích hợp UnbelievaBoat)
# ==============================================================================
CORECONFIG_FILE = os.path.join(DATA_DIR, "tnc_coreconfig_v1.json")
CORE_CREDITED_FILE = os.path.join(DATA_DIR, "tnc_core_credited_v1.json")


def load_coreconfig():
    for try_path in [CORECONFIG_FILE, CORECONFIG_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    return {"core_channel_id": "", "bank_channel_id": "", "emoji_map": {}}

def save_coreconfig(data):
    with _file_lock:
        tmp = CORECONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(CORECONFIG_FILE):
            shutil.copy2(CORECONFIG_FILE, CORECONFIG_FILE + ".bak")
        os.replace(tmp, CORECONFIG_FILE)

def load_core_credited():
    for try_path in [CORE_CREDITED_FILE, CORE_CREDITED_FILE + ".bak"]:
        if os.path.exists(try_path):
            with open(try_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ [Data] File {try_path} bị lỗi: {e}. Thử bản backup...")
    return {}

def save_core_credited(data):
    with _file_lock:
        tmp = CORE_CREDITED_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if os.path.exists(CORE_CREDITED_FILE):
            shutil.copy2(CORE_CREDITED_FILE, CORE_CREDITED_FILE + ".bak")
        os.replace(tmp, CORE_CREDITED_FILE)

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


# ── Lệnh cấu hình ──────────────────────────────────────────────────────────────

@bot.tree.command(name="coresetup", description="Cài đặt kênh cho hệ thống Core-Bank (Officer only)")
@app_commands.describe(
    core_channel="Kênh #core-vortex nơi member đăng ảnh",
    bank_channel="Kênh bot gửi lệnh !add-money / !remove-money cho UnbelievaBoat"
)
async def coresetup_cmd(interaction: discord.Interaction,
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


@bot.tree.command(name="coreadd", description="Thêm emoji Core với tên và giá trị silver tuỳ ý (Officer only)")
@app_commands.describe(
    emoji="Emoji đại diện (unicode hoặc emoji server, vd: 🟢 hay <:ten:id>)",
    name="Tên Core (vd: Green Core, Xanh Lá...)",
    value="Giá trị silver tương ứng",
    order="Số thứ tự hiển thị (tùy chọn, mặc định 0)"
)
async def coreadd_cmd(interaction: discord.Interaction, emoji: str, name: str, value: int, order: int = 0):
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


@bot.tree.command(name="coreremove", description="Xóa emoji Core khỏi danh sách (Officer only)")
@app_commands.describe(emoji="Emoji muốn xóa")
async def coreremove_cmd(interaction: discord.Interaction, emoji: str):
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


@bot.tree.command(name="coreautoreact", description="Bật/tắt tự động thả emoji vào ảnh trong kênh Core (Officer only)")
@app_commands.describe(enable="Bật (True) hoặc Tắt (False)")
async def coreautoreact_cmd(interaction: discord.Interaction, enable: bool):
    if not is_officer(interaction.user):
        return await interaction.response.send_message("❌ Chỉ Officer mới dùng được!", ephemeral=True)
    config = load_coreconfig()
    config["auto_react"] = enable
    save_coreconfig(config)
    state = "BẬT ✅" if enable else "TẮT ❌"
    await interaction.response.send_message(f"⚙️ Tự động thả emoji vào ảnh trong kênh Core: **{state}**", ephemeral=True)


@bot.tree.command(name="corelist", description="Xem danh sách emoji Core và cấu hình hiện tại")
async def corelist_cmd(interaction: discord.Interaction):
    config = load_coreconfig()
    emoji_map = config.get("emoji_map", {})
    core_ch = config.get("core_channel_id")
    bank_ch = config.get("bank_channel_id")
    auto_react = config.get("auto_react", False)
    
    embed = discord.Embed(title="⚙️ Cấu hình Core-Bank", color=0xf1c40f)
    embed.add_field(
        name="📌 Kênh",
        value=(f"📸 Core: {f'<#{core_ch}>' if core_ch else '_Chưa cài_'}\n"
               f"💰 Bank: {f'<#{bank_ch}>' if bank_ch else '_Chưa cài_'}\n"
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


# ── Event: Phát hiện react & gỡ react ──────────────────────────────────────────

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    config = load_coreconfig()
    core_ch_id = config.get("core_channel_id")
    bank_ch_id = config.get("bank_channel_id")
    emoji_map  = config.get("emoji_map", {})

    # Chỉ xử lý trong kênh core đã cài
    if not core_ch_id or str(payload.channel_id) != core_ch_id:
        return

    emoji_key = get_reaction_key(payload.emoji)
    if emoji_key not in emoji_map:
        return

    guild = bot.get_guild(payload.guild_id)
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
    if author.id == bot.user.id and "Ảnh tách ra từ <@" in message.content:
        match = re.search(r"Ảnh tách ra từ <@!?(\d+)>", message.content)
        if match:
            actual_id = match.group(1)
            actual_member = guild.get_member(int(actual_id))
            if actual_member:
                author = actual_member

    if author.bot:
        return

    core_info  = emoji_map[emoji_key]
    core_name  = core_info["name"]
    core_value = core_info["value"]
    core_disp  = core_info.get("display", emoji_key)

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
        "member_id":  str(author.id),
        "core_name":  core_name,
        "value":      core_value,
        "timestamp":  datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_core_credited(credited)

    # Gửi lệnh cho UnbelievaBoat
    await bank_channel.send(f"!add-money {author.mention} {core_value}")

    # Xác nhận dưới ảnh gốc
    await channel.send(
        f"✅ {core_disp} **{core_name}** — Đã cộng **{core_value:,} silver** vào bank của {author.mention}\n"
        f"_Ghi nhận bởi {reactor.mention}_",
        reference=message
    )


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    config = load_coreconfig()
    core_ch_id = config.get("core_channel_id")
    bank_ch_id = config.get("bank_channel_id")
    emoji_map  = config.get("emoji_map", {})

    if not core_ch_id or str(payload.channel_id) != core_ch_id:
        return

    emoji_key = get_reaction_key(payload.emoji)
    if emoji_key not in emoji_map:
        return

    credited   = load_core_credited()
    credit_key = f"{payload.message_id}:{emoji_key}"
    if credit_key not in credited:
        return  # Chưa từng cộng → không cần hoàn lại

    entry = credited[credit_key]
    # Chỉ hoàn lại nếu chính Officer đó gỡ react
    if str(payload.user_id) != entry["officer_id"]:
        return

    del credited[credit_key]
    save_core_credited(credited)

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    core_info  = emoji_map[emoji_key]
    core_value = core_info["value"]
    core_name  = core_info["name"]
    core_disp  = core_info.get("display", emoji_key)
    member     = guild.get_member(int(entry["member_id"]))
    member_mention  = member.mention if member else f"<@{entry['member_id']}>"
    reactor    = guild.get_member(payload.user_id)
    reactor_mention = reactor.mention if reactor else f"<@{payload.user_id}>"

    bank_channel = guild.get_channel(int(bank_ch_id)) if bank_ch_id else None
    if bank_channel:
        await bank_channel.send(f"!remove-money {member_mention} {core_value}")

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


# ==============================================================================
# 11. KHỞI CHẠY HỆ THỐNG
# ==============================================================================
@bot.event
async def on_ready():
    lastseen_cache.update(load_lastseen())
    bot.loop.create_task(guildcheck_loop())
    bot.loop.create_task(lastseen_flush_loop())
    print(f"🔍 [Check] ffmpeg path: {shutil.which('ffmpeg')}")
    print(f"✅ TNC Bot v40 [Siphoned + Massing + GuildCheck + ALO-TTS + CoreBank] Online! Session: {BOT_SESSION_ID}")

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)