import discord
from discord.ext import commands, tasks
from core.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
import datetime
import pytz

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Không thể khởi tạo Supabase client trong chat_logger: {e}")

class ChatLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_old_messages.start()

    def cog_unload(self):
        self.cleanup_old_messages.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
            
        # Bỏ qua các tin nhắn rỗng (ví dụ chỉ có ảnh mà không có chữ)
        if not message.content.strip():
            return
            
        # Bỏ qua các tin nhắn gọi lệnh (bắt đầu bằng /, !, .) để tiết kiệm dung lượng
        if message.content.startswith(("!", "/", ".")):
            return

        if not supabase: 
            return

        try:
            data = {
                "id": str(message.id),
                "user_id": str(message.author.id),
                "author_name": message.author.display_name,
                "channel_id": str(message.channel.id),
                "channel_name": getattr(message.channel, "name", "unknown"),
                "content": message.content,
                "created_at": message.created_at.isoformat()
            }
            # Chạy ngầm việc insert để không làm đứng bot
            self.bot.loop.create_task(self._insert_log(data))
        except Exception as e:
            print(f"Lỗi khi chuẩn bị log chat: {e}")

    async def _insert_log(self, data):
        try:
            # Insert log âm thầm
            supabase.table("chat_history").insert(data).execute()
        except Exception as e:
            pass # Bỏ qua lỗi ngầm để tránh spam console khi DB lỗi

    @tasks.loop(hours=24)
    async def cleanup_old_messages(self):
        """Tự động xoá tin nhắn cũ hơn 7 ngày để tiết kiệm dung lượng 0đ"""
        if not supabase: return
        try:
            # Lấy mốc thời gian 7 ngày trước
            seven_days_ago = (datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7)).isoformat()
            
            # Thực thi xoá
            supabase.table("chat_history").delete().lte("created_at", seven_days_ago).execute()
            print(f"🧹 Đã chạy tác vụ dọn dẹp tin nhắn chat cũ hơn 7 ngày trên Supabase (Dự án 0đ).")
        except Exception as e:
            print(f"Lỗi khi dọn dẹp tin nhắn cũ: {e}")

    @cleanup_old_messages.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ChatLogger(bot))
