import asyncio
import os
from datetime import datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from core.permissions import is_officer
from core.database import supabase

# ==============================================================================
# HỆ THỐNG PHÂN TÍCH ĐIỂM SIPHONED (LOG ANALYZER)
# ==============================================================================

def load_sp():
    data = {"history": {}, "last_update": "Chưa có dữ liệu"}
    try:
        # Load metadata
        meta_resp = supabase.table("sp_metadata").select("last_update").eq("id", 1).execute()
        if meta_resp.data:
            data["last_update"] = meta_resp.data[0]["last_update"]
        
        # Load history
        history_resp = supabase.table("user_economy").select("user_id, silver_pieces").execute()
        if history_resp.data:
            for row in history_resp.data:
                data["history"][row["user_id"]] = row["silver_pieces"]
    except Exception as e:
        print(f"Error loading SP from Supabase: {e}")
    return data

def save_sp(data):
    try:
        # Save metadata
        supabase.table("sp_metadata").upsert({"id": 1, "last_update": data.get("last_update", "N/A")}).execute()
        
        # Save history
        records = [{"user_id": user, "silver_pieces": sp} for user, sp in data.get("history", {}).items()]
        
        if records:
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i+chunk_size]
                supabase.table("user_economy").upsert(chunk).execute()
    except Exception as e:
        print(f"Error saving SP to Supabase: {e}")

def delete_sp_user(user_id):
    try:
        supabase.table("user_economy").delete().eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error deleting user {user_id} from Supabase: {e}")

def reset_sp_history():
    try:
        # Warning: This clears the whole table
        # We can't do delete without filter in supabase python easily, so we just select all and delete in chunks or just one by one, 
        # or it's better to just delete using a filter that matches all.
        # But actually in supabase we can do delete().neq("user_id", "nothing")
        supabase.table("user_economy").delete().neq("user_id", "").execute()
        supabase.table("sp_metadata").upsert({"id": 1, "last_update": "N/A"}).execute()
    except Exception as e:
        print(f"Error resetting SP history: {e}")

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


class SiphonedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="spupdate", description="Cập nhật file log Siphoned (tự kiểm tra ngày tháng)")
    async def spupdate(self, interaction: discord.Interaction, file_log: discord.Attachment):
        await interaction.response.defer()
        if not file_log.filename.endswith('.txt'):
            return await interaction.followup.send("❌ Vui lòng đính kèm tệp văn bản định dạng `.txt`!")

        async with aiohttp.ClientSession() as session:
            async with session.get(file_log.url) as r:
                text = await r.text(encoding='utf-8', errors='ignore')

        data = load_sp()
        lines = text.strip().split('\n')

        # Bước 1: Tìm mốc thời gian mới nhất trong file
        new_latest_time = None
        for line in lines:
            if "Player" in line or not line.strip():
                continue
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
            if "Player" in line or not line.strip():
                continue
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
                except ValueError:
                    continue

        save_sp(data)
        await interaction.followup.send(f"✅ Xử lý thành công **{count}** dòng dữ liệu log.\nMốc log: `{data['last_update']}` (Đã lưu lên Supabase)")

    @app_commands.command(name="spcheck", description="Xem bảng xếp hạng tích lũy điểm Siphoned")
    async def spcheck(self, interaction: discord.Interaction):
        data = load_sp()
        history = data.get("history", {})
        last_up = data.get("last_update", "N/A")
        if not history:
            return await interaction.response.send_message("📊 Hiện tại hệ thống Siphoned chưa có dữ liệu.")
        sorted_sp = sorted(history.items(), key=lambda x: x[1], reverse=True)
        view = SiphonedPaginator(sorted_sp, last_up)
        await interaction.response.send_message(embed=view.create_embed(), view=view)

    @commands.command(name="addsp")
    async def addsp(self, ctx, name: str, amt: int):
        if not is_officer(ctx.author):
            return await ctx.send("❌ Bạn không có quyền!")
        data = load_sp()
        data["history"][name] = data["history"].get(name, 0) + amt
        save_sp(data)
        await ctx.send(f"💎 **[SIPHONED]** Đã cộng tay **+{amt:,}** SP cho **{name}**.")

    @commands.command(name="removesp")
    async def removesp(self, ctx, name: str, amt: int):
        if not is_officer(ctx.author):
            return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
        if amt <= 0:
            return await ctx.send("⚠️ Số điểm trừ phải lớn hơn 0 bro ơi!")
        data = load_sp()
        if name in data["history"]:
            data["history"][name] = data["history"].get(name, 0) - amt
            save_sp(data)
            await ctx.send(f"📉 **[SIPHONED]** Đã trừ bớt **-{amt:,}** SP của thành viên **{name}**.\n📊 Điểm hiện tại của họ: **{data['history'][name]:,}** SP.")
        else:
            await ctx.send(f"❓ Không tìm thấy thành viên mang tên `{name}` trong bảng dữ liệu.")

    @commands.command(name="removesprole")
    async def removesprole(self, ctx, *, name: str):
        if not is_officer(ctx.author):
            return await ctx.send("❌ Bạn không có quyền!")
        data = load_sp()
        if name in data["history"]:
            delete_sp_user(name)
            await ctx.send(f"🧹 Đã xóa hoàn toàn thành viên **{name}** ra khỏi bảng xếp hạng Siphoned.")
        else:
            await ctx.send(f"❓ Không tìm thấy thành viên `{name}`.")

    @commands.command(name="resetsp")
    async def resetsp(self, ctx):
        if not is_officer(ctx.author):
            return await ctx.send("❌ Bạn không có quyền!")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("⚠️ Bạn có muốn đưa toàn bộ bảng điểm Siphoned về 0? Gõ `yes`.")
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=15.0)
            if msg.content.lower() == 'yes':
                reset_sp_history()
                await ctx.send("🧹 Toàn bộ bảng xếp hạng điểm Siphoned đã được reset!")
        except asyncio.TimeoutError:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(SiphonedCog(bot))

