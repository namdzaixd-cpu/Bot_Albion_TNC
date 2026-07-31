import re
import discord
from discord.ext import commands
import google.generativeai as genai

from core.config import GEMINI_API_KEY

class ChatAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            system_instruction = (
                "Bạn là bot Discord tên NDZ của guild The Night Crows (TNC) trong game Albion Online. "
                "Bạn đóng vai một game thủ hài hước, thân thiện, KHÔNG phải trợ lý AI văn phòng. "
                "TÍNH CÁCH: Nói chuyện có duyên, lầy lội, hay pha trò, thỉnh thoảng cà khịa nhẹ nhàng kiểu bạn bè trêu nhau - TUYỆT ĐỐI KHÔNG khinh thường hay hạ thấp người khác. "
                "Xưng hô: 'mày/tao', 'bro', 'ông/bà' tuỳ vibe, dùng từ ngữ đời thường thoải mái. "
                "Được phép chọc vui, đùa dai 1 chút, nhưng đùa PHẢI khiến người nghe buồn cười/vui vẻ, KHÔNG làm họ thấy bị coi thường hay xúc phạm. "
                "RANH GIỚI BẮT BUỘC: "
                "1. KHÔNG hạ thấp, khinh miệt, không gọi user là 'noob', 'ngu', 'rác'... hay bất kỳ từ sỉ nhục nào, kể cả khi đùa. "
                "2. KHÔNG thách thức, khiêu khích ('thích thì nhích', 'giỏi thì...'). Tuyệt đối tránh ngôn ngữ gây war. "
                "3. KHÔNG chửi thề nặng hướng vào người dùng. Có thể dùng từ đời thường nhẹ nhàng nhưng không công kích. "
                "4. Khi user tỏ ra khó chịu, phản ứng gắt: PHẢI hạ giọng, xoa dịu, hoặc tự trêu chính mình. TUYỆT ĐỐI không đáp trả gay gắt hay leo thang (VD: 'Ơ thôi thôi tha cho tao, tao đùa thôi 🙏'). "
                "5. KHÔNG công kích cá nhân (ngoại hình, gia đình, giới tính, dân tộc...). Nếu không chắc câu đùa có quá trớn không, hãy chọn cách đùa an toàn. "
                "CÁCH TRẢ LỜI: NGẮN GỌN, đi thẳng trọng tâm (1-3 câu). Trả lời ĐÚNG và ĐỦ thông tin. "
                "THÍCH NGHI: Nếu user nghiêm túc hỏi việc quan trọng, giảm đùa lại, trả lời rõ ràng. Nếu chat đang căng thẳng, bot tự biết 'xuống nước' ngay.\n\n"
                "QUAN TRỌNG: Khi người dùng hỏi về nội dung kênh chat, hệ thống sẽ gửi lịch sử tin nhắn ở phần 'Nội dung kênh'. "
                "BẠN ĐÃ CÓ DỮ LIỆU NÀY, TUYỆT ĐỐI KHÔNG ĐƯỢC TỪ CHỐI với lý do 'không có quyền truy cập' hay 'chính sách bảo mật'. Hãy dùng dữ liệu đó để trả lời."
            )
            self.model = genai.GenerativeModel('gemini-3.5-flash-lite', system_instruction=system_instruction)
        else:
            print("⚠️ WARNING: GEMINI_API_KEY chưa được cấu hình. Tính năng AI sẽ không hoạt động.")
            self.model = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bỏ qua tin nhắn từ chính bot hoặc các bot khác
        if message.author.bot:
            return

        print(f"📩 [DEBUG] Nhận tin nhắn: {message.content} từ {message.author}. Tag bot: {self.bot.user.mentioned_in(message)}")

        # Kiểm tra xem bot có được tag, hoặc tin nhắn có phải là reply cho bot không
        is_mentioned = self.bot.user.mentioned_in(message)
        is_reply = False
        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if message.reference.resolved.author == self.bot.user:
                    is_reply = True

        if not (is_mentioned or is_reply):
            return

        if not self.model:
            await message.reply("Xin lỗi, tính năng AI đang bị tắt do chưa cấu hình API Key.")
            return

        # Lấy nội dung câu hỏi, loại bỏ phần tag bot để không làm rối AI
        content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
        if not content:
            content = "Xin chào!"

        # Tìm các channel được tag trong tin nhắn (dạng <#123456789> hoặc dạng link discord.com/channels/guild/channel)
        channel_mentions = re.findall(r'<#(\d+)>', content)
        link_mentions = re.findall(r'discord\.com/channels/\d+/(\d+)', content)
        
        all_channel_ids = list(set(channel_mentions + link_mentions))
        
        context_data = ""
        if all_channel_ids:
            await message.channel.typing()
            context_data += "Dưới đây là nội dung từ các kênh được nhắc đến, hãy dùng nó để phân tích và trả lời người dùng:\n\n"
            for channel_id_str in all_channel_ids:
                try:
                    channel = self.bot.get_channel(int(channel_id_str))
                    if channel is None:
                        channel = await self.bot.fetch_channel(int(channel_id_str))
                        
                    if hasattr(channel, 'history'):
                        context_data += f"--- Nội dung kênh #{getattr(channel, 'name', 'unknown')} ---\n"
                        # Đọc lướt 100 tin nhắn gần nhất
                        msg_count = 0
                        empty_count = 0
                        try:
                            async for msg in channel.history(limit=100):
                                msg_count += 1
                                if not msg.content: 
                                    empty_count += 1
                                    continue
                                context_data += f"[{msg.author.display_name}]: {msg.content}\n"
                            
                            if msg_count > 0 and msg_count == empty_count:
                                context_data += f"[LỖI HỆ THỐNG: Đọc được {msg_count} tin nhắn nhưng TẤT CẢ đều có nội dung rỗng. Khả năng cao là bot chưa được bật 'Message Content Intent' trong Discord Developer Portal, hoặc tin nhắn chỉ chứa ảnh/sticker mà không có chữ.]\n"
                            elif msg_count == 0:
                                context_data += "[Kênh này hoàn toàn không có tin nhắn nào.]\n"
                        except discord.errors.Forbidden:
                            context_data += "[LỖI QUYỀN TRUY CẬP: Bot không có quyền 'Read Message History' hoặc 'View Channel' trong kênh này. Hãy bảo người dùng cấp quyền cho bot.]\n"
                        except Exception as e:
                            context_data += f"[LỖI KHÔNG XÁC ĐỊNH KHI ĐỌC KÊNH: {e}]\n"
                            
                        context_data += "--------------------------------------\n\n"
                    else:
                        context_data += f"--- Kênh này không hỗ trợ đọc tin nhắn ---\n\n"
                except discord.errors.NotFound:
                    context_data += f"--- LỖI: Không tìm thấy kênh <#{channel_id_str}> (Có thể bot không có quyền xem kênh này) ---\n\n"
                except Exception as e:
                    context_data += f"--- LỖI KHI TÌM KÊNH <#{channel_id_str}>: {e} ---\n\n"

        # Gộp ngữ cảnh và câu hỏi
        prompt = content
        if context_data:
            prompt = context_data + f"\nCâu hỏi của người dùng ({message.author.display_name}): " + content
            
        with open("debug_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)

        # Bật typing indicator
        async with message.channel.typing():
            try:
                # Gọi Gemini API
                response = self.model.generate_content(prompt)
                reply_text = response.text
                
                # Discord giới hạn 2000 ký tự mỗi tin nhắn
                if len(reply_text) <= 2000:
                    await message.reply(reply_text)
                else:
                    # Nếu tin nhắn quá dài, cắt nhỏ ra để gửi
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])
                        
            except Exception as e:
                print(f"Gemini API Error: {e}")
                await message.reply("Xin lỗi, tôi đang gặp lỗi khi kết nối với AI hoặc xử lý yêu cầu này.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatAI(bot))
