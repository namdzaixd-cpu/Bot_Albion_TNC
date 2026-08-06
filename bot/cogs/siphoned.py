import asyncio
import io
from datetime import datetime, timezone, timedelta

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
        meta_resp = supabase.table("sp_metadata").select("last_update").eq("id", 1).execute()
        if meta_resp.data:
            data["last_update"] = meta_resp.data[0]["last_update"]

        history_resp = supabase.table("user_economy").select("user_id, silver_pieces").execute()
        if history_resp.data:
            for row in history_resp.data:
                data["history"][row["user_id"]] = row["silver_pieces"]
    except Exception as e:
        print(f"Error loading SP from Supabase: {e}")
    return data

def save_sp(data):
    try:
        supabase.table("sp_metadata").upsert({"id": 1, "last_update": data.get("last_update", "N/A")}).execute()

        records = [{"user_id": user, "silver_pieces": sp} for user, sp in data.get("history", {}).items()]
        if records:
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                supabase.table("user_economy").upsert(records[i:i+chunk_size]).execute()
    except Exception as e:
        print(f"Error saving SP to Supabase: {e}")

def save_transactions(rows: list[dict]):
    """Ghi lịch sử từng dòng log vào sp_transactions, sau đó xóa record cũ > 1 năm."""
    try:
        if rows:
            chunk_size = 1000
            for i in range(0, len(rows), chunk_size):
                supabase.table("sp_transactions").insert(rows[i:i+chunk_size]).execute()
        # Dọn dẹp record cũ hơn 1 năm
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        supabase.table("sp_transactions").delete().lt("inserted_at", cutoff).execute()
    except Exception as e:
        print(f"Error saving sp_transactions: {e}")

def delete_sp_user(user_id):
    try:
        supabase.table("user_economy").delete().eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error deleting user {user_id} from Supabase: {e}")

def reset_sp_history():
    try:
        supabase.table("user_economy").delete().neq("user_id", "").execute()
        supabase.table("sp_metadata").upsert({"id": 1, "last_update": "N/A"}).execute()
    except Exception as e:
        print(f"Error resetting SP history: {e}")


# ==============================================================================
# PAGINATOR — dùng chung cho spcheck và sptop
# ==============================================================================

class SiphonedPaginator(discord.ui.View):
    def __init__(self, data, last_update, title="💎 TNC SIPHONED LEADERBOARD", label="Mốc Log Đã Cập Nhật:"):
        super().__init__(timeout=86400)
        self.data = data
        self.last_update = last_update
        self.title = title
        self.label = label
        self.current_page = 0
        self.per_page = 15

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_data = self.data[start:end]
        total_pages = (len(self.data) - 1) // self.per_page + 1 if self.data else 1
        embed = discord.Embed(title=self.title, color=0x9b59b6)
        embed.add_field(name=f"📅 {self.label}", value=f"`{self.last_update}`", inline=False)
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
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Sau ➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.current_page + 1) * self.per_page < len(self.data):
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()


# ==============================================================================
# CONFIRM VIEW — dùng cho /resetsp
# ==============================================================================

class ResetConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.confirmed = False

    @discord.ui.button(label="✅ Xác nhận Reset", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        reset_sp_history()
        await interaction.response.edit_message(
            content="🧹 Toàn bộ bảng xếp hạng điểm Siphoned đã được reset!",
            view=None
        )

    @discord.ui.button(label="❌ Huỷ", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="↩️ Đã huỷ thao tác reset.", view=None)


# ==============================================================================
# COG
# ==============================================================================

class SiphonedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /spupdate ──────────────────────────────────────────────────────────────
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

        # Bước 3: Xử lý cộng điểm + thu thập transactions
        count = 0
        time_set = False
        transactions = []
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
                    try:
                        log_ts = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S").isoformat()
                    except ValueError:
                        log_ts = datetime.now(timezone.utc).isoformat()
                    transactions.append({
                        "player_name": player_name,
                        "amount": amount,
                        "log_timestamp": log_ts,
                    })
                    count += 1
                except ValueError:
                    continue

        save_sp(data)
        save_transactions(transactions)
        await interaction.followup.send(
            f"✅ Xử lý thành công **{count}** dòng dữ liệu log.\n"
            f"Mốc log: `{data['last_update']}` (Đã lưu lên Supabase + ghi lịch sử)"
        )

    # ── /spcheck ───────────────────────────────────────────────────────────────
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

    # ── /sphistory ─────────────────────────────────────────────────────────────
    @app_commands.command(name="sphistory", description="Xem lịch sử đóng góp SP của một thành viên")
    @app_commands.describe(player="Tên player trong game (phân biệt hoa/thường)")
    async def sphistory(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer()
        try:
            resp = supabase.table("sp_transactions") \
                .select("amount, log_timestamp") \
                .eq("player_name", player) \
                .order("log_timestamp", desc=True) \
                .limit(20) \
                .execute()
        except Exception as e:
            return await interaction.followup.send(f"❌ Lỗi khi truy vấn dữ liệu: {e}")

        rows = resp.data if resp.data else []
        if not rows:
            return await interaction.followup.send(
                f"❓ Không tìm thấy lịch sử đóng góp nào của `{player}`.\n"
                f"*(Lịch sử chỉ có từ khi tính năng này được bật)*"
            )

        total = sum(r["amount"] for r in rows)
        desc = ""
        for i, r in enumerate(rows, 1):
            ts = r["log_timestamp"][:16] if r["log_timestamp"] else "N/A"
            desc += f"**#{i}** `{ts}` ➜ **+{r['amount']:,}** SP\n"

        embed = discord.Embed(
            title=f"📋 Lịch sử SP — {player}",
            description=desc,
            color=0x9b59b6
        )
        embed.set_footer(text=f"Tổng {len(rows)} lần đóng góp gần nhất • Tổng cộng: {total:,} SP")
        await interaction.followup.send(embed=embed)

    # ── /sptop ─────────────────────────────────────────────────────────────────
    @app_commands.command(name="sptop", description="Xem bảng xếp hạng SP theo khoảng thời gian")
    @app_commands.describe(period="Khoảng thời gian muốn xem")
    @app_commands.choices(period=[
        app_commands.Choice(name="30 ngày gần nhất", value="30d"),
        app_commands.Choice(name="3 tháng gần nhất", value="90d"),
        app_commands.Choice(name="6 tháng gần nhất", value="6m"),
        app_commands.Choice(name="Tất cả (từ khi bật tính năng)", value="all"),
    ])
    async def sptop(self, interaction: discord.Interaction, period: str):
        await interaction.response.defer()

        period_map = {"30d": 30, "90d": 90, "6m": 180}
        period_label = {"30d": "30 ngày", "90d": "3 tháng", "6m": "6 tháng", "all": "Toàn bộ lịch sử"}

        try:
            query = supabase.table("sp_transactions").select("player_name, amount")
            if period != "all":
                days = period_map[period]
                cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                query = query.gte("inserted_at", cutoff)
            resp = query.execute()
        except Exception as e:
            return await interaction.followup.send(f"❌ Lỗi khi truy vấn dữ liệu: {e}")

        rows = resp.data if resp.data else []
        if not rows:
            return await interaction.followup.send(
                f"📊 Không có dữ liệu trong **{period_label[period]}**.\n"
                f"*(Lịch sử chỉ có từ khi tính năng này được bật)*"
            )

        # Tổng hợp theo player
        totals: dict[str, int] = {}
        for r in rows:
            totals[r["player_name"]] = totals.get(r["player_name"], 0) + r["amount"]

        sorted_data = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        view = SiphonedPaginator(
            sorted_data,
            period_label[period],
            title=f"💎 TOP SP — {period_label[period].upper()}",
            label="Khoảng thời gian:"
        )
        await interaction.followup.send(embed=view.create_embed(), view=view)

    # ── /splog ─────────────────────────────────────────────────────────────────
    @app_commands.command(name="splog", description="Xem audit log các lần upload log gần nhất (Officer)")
    async def splog(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        try:
            resp = supabase.table("sp_transactions") \
                .select("log_timestamp, inserted_at") \
                .order("inserted_at", desc=True) \
                .limit(200) \
                .execute()
        except Exception as e:
            return await interaction.followup.send(f"❌ Lỗi khi truy vấn: {e}")

        rows = resp.data if resp.data else []
        if not rows:
            return await interaction.followup.send("📋 Chưa có audit log nào.")

        # Nhóm theo mốc log_timestamp (mỗi lần upload 1 mốc)
        batches: dict[str, int] = {}
        for r in rows:
            key = r["log_timestamp"][:16]
            batches[key] = batches.get(key, 0) + 1

        sorted_batches = sorted(batches.items(), key=lambda x: x[0], reverse=True)[:10]
        desc = ""
        for i, (ts, cnt) in enumerate(sorted_batches, 1):
            desc += f"**#{i}** `{ts}` — **{cnt}** dòng dữ liệu\n"

        embed = discord.Embed(title="📋 Audit Log — SP Transactions", description=desc, color=0xe67e22)
        embed.set_footer(text="Hiển thị tối đa 10 lần upload gần nhất")
        await interaction.followup.send(embed=embed)

    # ── /spexport ──────────────────────────────────────────────────────────────
    @app_commands.command(name="spexport", description="Xuất toàn bộ dữ liệu SP hiện tại ra file .txt (Officer)")
    async def spexport(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        await interaction.response.defer()

        data = load_sp()
        history = data.get("history", {})
        last_update = data.get("last_update", "N/A")

        if not history:
            return await interaction.followup.send("📊 Chưa có dữ liệu SP để xuất.")

        sorted_sp = sorted(history.items(), key=lambda x: x[1], reverse=True)

        lines = ['"Date"\t"Player"\t"Reason"\t"Amount"']
        for player, sp in sorted_sp:
            reason = "Withdrawal" if sp < 0 else "Deposit"
            lines.append(f'"{last_update}"\t"{player}"\t"{reason}"\t"{sp}"')

        content = "\n".join(lines)
        file = discord.File(io.BytesIO(content.encode("utf-8")), filename="tnc_sp_exportdata.txt")
        await interaction.followup.send(
            f"📤 Xuất thành công **{len(sorted_sp)}** thành viên.\nMốc log: `{last_update}`",
            file=file
        )

    # ── /addsp ─────────────────────────────────────────────────────────────────
    @app_commands.command(name="addsp", description="Cộng tay SP cho một thành viên (Officer)")
    @app_commands.describe(name="Tên player trong game", amt="Số SP muốn cộng")
    async def addsp(self, interaction: discord.Interaction, name: str, amt: int):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        if amt <= 0:
            return await interaction.response.send_message("⚠️ Số điểm phải lớn hơn 0!", ephemeral=True)
        data = load_sp()
        data["history"][name] = data["history"].get(name, 0) + amt
        save_sp(data)
        await interaction.response.send_message(f"💎 **[SIPHONED]** Đã cộng tay **+{amt:,}** SP cho **{name}**.")

    # ── /removesp ──────────────────────────────────────────────────────────────
    @app_commands.command(name="removesp", description="Trừ SP của một thành viên (Officer)")
    @app_commands.describe(name="Tên player trong game", amt="Số SP muốn trừ")
    async def removesp(self, interaction: discord.Interaction, name: str, amt: int):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        if amt <= 0:
            return await interaction.response.send_message("⚠️ Số điểm trừ phải lớn hơn 0!", ephemeral=True)
        data = load_sp()
        if name not in data["history"]:
            return await interaction.response.send_message(f"❓ Không tìm thấy thành viên mang tên `{name}` trong bảng dữ liệu.")
        data["history"][name] = data["history"].get(name, 0) - amt
        save_sp(data)
        await interaction.response.send_message(
            f"📉 **[SIPHONED]** Đã trừ bớt **-{amt:,}** SP của thành viên **{name}**.\n"
            f"📊 Điểm hiện tại của họ: **{data['history'][name]:,}** SP."
        )

    # ── /removesprole ──────────────────────────────────────────────────────────
    @app_commands.command(name="removesprole", description="Xóa hoàn toàn một thành viên khỏi bảng Siphoned (Officer)")
    @app_commands.describe(name="Tên player trong game (chính xác)")
    async def removesprole(self, interaction: discord.Interaction, name: str):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        data = load_sp()
        if name not in data["history"]:
            return await interaction.response.send_message(f"❓ Không tìm thấy thành viên `{name}`.")
        delete_sp_user(name)
        await interaction.response.send_message(f"🧹 Đã xóa hoàn toàn thành viên **{name}** ra khỏi bảng xếp hạng Siphoned.")

    # ── /resetsp ───────────────────────────────────────────────────────────────
    @app_commands.command(name="resetsp", description="Reset toàn bộ bảng điểm Siphoned về 0 (Officer)")
    async def resetsp(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
        view = ResetConfirmView()
        await interaction.response.send_message(
            "⚠️ Bạn có chắc muốn **reset toàn bộ bảng điểm Siphoned**?\n"
            "Hành động này **không thể hoàn tác**!",
            view=view,
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(SiphonedCog(bot))
