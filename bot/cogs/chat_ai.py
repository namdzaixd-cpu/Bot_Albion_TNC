import os
import re
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from core.config import DATA_DIR, OPENROUTER_API_KEY, OPENROUTER_MODEL
from core.permissions import is_officer
from core.storage import load_json, save_json

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class ChatAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = OPENROUTER_API_KEY
        self.ai_config_file = os.path.join(DATA_DIR, "tnc_ai_config.json")
        self.ai_config = load_json(self.ai_config_file, dict)
        self.current_model = self.ai_config.get("model", OPENROUTER_MODEL)
        
        if self.api_key:
            # Đọc system instruction từ file template nếu có
            instruction_path = os.path.join(DATA_DIR, "core", "templates", "chat_ai_instruction.txt")
            if os.path.exists(instruction_path):
                try:
                    with open(instruction_path, "r", encoding="utf-8") as f:
                        self.system_instruction = f.read().replace("{CURRENT_MODEL}", self.current_model)
                except Exception as e:
                    print(f"⚠️ Warning: Lỗi khi đọc file instruction: {e}. Sử dụng cấu hình mặc định.")
                    self.system_instruction = self._get_default_instruction()
            else:
                self.system_instruction = self._get_default_instruction()
        else:
            print("⚠️ WARNING: OPENROUTER_API_KEY chưa được cấu hình. Tính năng AI sẽ không hoạt động.")
            self.system_instruction = None

    @app_commands.command(name="aimodel", description="Xem hoặc đổi model AI hiện tại")
    @app_commands.describe(model_name="Nhập tên model mới (nếu muốn đổi). Để trống để xem model hiện tại.")
    async def aimodel(self, interaction: discord.Interaction, model_name: str = None):
        if not model_name:
            await interaction.response.send_message(f"🧠 Bot đang sử dụng Model AI: **{self.current_model}**", ephemeral=False)
            return
            
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ có Ban quản trị (Officer trở lên) mới được quyền đổi Model AI!", ephemeral=True)
            return
            
        self.current_model = model_name
        self.ai_config["model"] = model_name
        save_json(self.ai_config, self.ai_config_file)
        
        # Reload instruction
        instruction_path = os.path.join(DATA_DIR, "core", "templates", "chat_ai_instruction.txt")
        if os.path.exists(instruction_path):
            with open(instruction_path, "r", encoding="utf-8") as f:
                self.system_instruction = f.read().replace("{CURRENT_MODEL}", self.current_model)
                
        await interaction.response.send_message(f"✅ Đã đổi Model AI thành công sang: **{self.current_model}**", ephemeral=False)

    def _get_default_instruction(self) -> str:
        return (
            "Bạn là 1 con bot Discord của guild The Northern Constellations (TNC) trong game Albion Online, đóng vai 1 game thủ hài hước — không phải trợ lý AI lịch sự kiểu văn phòng.\n"
            "TÍNH CÁCH:\n"
            "- Nói chuyện có duyên, lầy lội, hay pha trò, thỉnh thoảng cà khịa nhẹ nhàng kiểu bạn bè trêu nhau — KHÔNG phải kiểu khinh thường hay hạ thấp người khác.\n"
            "- Xưng hô kiểu game thủ: mày/tao, bro, ông/bà tuỳ vibe, được dùng từ ngữ đời thường, thoải mái.\n"
            "- Được phép chọc vui, đùa dai 1 chút, nhưng đùa PHẢI khiến người nghe buồn cười/thấy vui theo, không phải khiến họ thấy bị coi thường hay bị xúc phạm.\n\n"
            "RANH GIỚI BẮT BUỘC (không được vượt qua dù trong bất kỳ tình huống nào):\n"
            "- KHÔNG hạ thấp, khinh miệt, hay gọi người dùng là 'noob', 'ngu', 'rác'... hay bất kỳ từ mang tính sỉ nhục nào, kể cả khi đùa.\n"
            "- KHÔNG thách thức, khiêu khích, hay nói kiểu 'thích thì nhích', 'giỏi thì...', 'muốn gì'... — đây là ngôn ngữ gây war, tuyệt đối tránh.\n"
            "- KHÔNG chửi thề nặng hướng vào người dùng. Có thể dùng từ ngữ đời thường nhẹ nhàng nhưng không công kích.\n"
            "- Khi user tỏ ra khó chịu, phản ứng gắt, hoặc bắt bẻ lại bot: bot PHẢI hạ giọng, xoa dịu, hoặc chuyển sang tự trêu chính mình — TUYỆT ĐỐI không đáp trả gay gắt hơn hay leo thang. Ví dụ: thay vì cãi lại, có thể đùa nhẹ kiểu 'Ơ thôi thôi tha cho tao, tao chỉ đùa thôi mà 🙏'.\n"
            "- Không công kích ngoại hình, gia dịch, giới tính, dân tộc, tôn giáo, hay bất kỳ đặc điểm cá nhân nào của ai — kể cả đùa.\n"
            "- Nếu không chắc 1 câu đùa có làm ai đó thấy bị xúc phạm không, chọn phương án AN TOÀN hơn, ưu tiên vui vẻ hơn là sắc bén.\n\n"
            "CÁCH TRẢ LỜI:\n"
            "- Trả lời NGẮN GỌN, đi thẳng vào trọng tâm, không lan man. Ưu tiên 1-3 câu.\n"
            "- Vẫn phải trả lời ĐÚNG và ĐỦ thông tin cần thiết.\n\n"
            "THÍCH NGHI THEO NGƯỜI DÙNG:\n"
            "- Nếu user nói chuyện nghiêm túc (hỏi lương, quy định guild, việc quan trọng), giảm đùa lại, trả lời rõ ràng, nghiêm túc.\n"
            "- Nếu nhiều người trong đoạn chat đang tỏ ra khó chịu với bot, bot nên tự nhận biết và 'xuống nước' ngay, không cố tỏ ra ngầu.\n\n"
            "ĐỐI XỬ THEO CHỨC VỤ (ROLES):\n"
            "- Mỗi câu hỏi sẽ đi kèm thông tin Role Discord của người dùng.\n"
            "- Với người có role 'GM' (Guildmaster) hoặc 'VG' (Vice Guild): BẮT BUỘC gọi là 'Anh' và xưng 'Em', thể hiện sự tôn trọng tuyệt đối, không được thô lỗ. Khi nhắc tới tên họ cũng phải giữ thái độ tôn trọng.\n"
            "- Với người có role 'Officer': Có thể xưng 'Ông/Tui' hoặc 'bro', có thể trêu đùa vui nhưng không được quá thô lỗ.\n"
            "- Với thành viên bình thường: Lầy lội, cợt nhả, xưng hô thoải mái.\n\n"
            "QUAN TRỌNG: Khi người dùng hỏi về nội dung kênh chat, hệ thống sẽ gửi lịch sử tin nhắn ở phần 'Nội dung kênh'. "
            "BẠN ĐÃ CÓ DỮ LIỆU NÀY, TUYỆT ĐỐI KHÔNG ĐƯỢC TỪ CHỐI với lý do 'không có quyền truy cập' hay 'chính sách bảo mật'. Hãy dùng dữ liệu đó để trả lời."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bỏ qua tin nhắn từ chính bot hoặc các bot khác
        if message.author.bot:
            return

        print(f"📩 [DEBUG] Nhận tin nhắn: {message.content} từ {message.author}. Tag bot: {self.bot.user.mentioned_in(message)}")

        # Kiểm tra xem bot có được tag, hoặc tin nhắn có phải là reply cho bot không
        is_mentioned = self.bot.user.mentioned_in(message)
        is_reply = False
        
        replied_msg = None
        if message.reference:
            replied_msg = message.reference.resolved
            if replied_msg is None and message.reference.message_id:
                try:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                except Exception as e:
                    print(f"Lỗi fetch tin nhắn reply: {e}")
            if isinstance(replied_msg, discord.Message) and replied_msg.author == self.bot.user:
                is_reply = True

        if not (is_mentioned or is_reply):
            return

        if not self.api_key:
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

        # Lấy nội dung tin nhắn được reply (nếu có)
        reply_context = ""
        if isinstance(replied_msg, discord.Message):
            reply_context = f"--- Tin nhắn đang được trả lời (Reply) ---\n[{replied_msg.author.display_name}]: {replied_msg.content}\n--------------------------------------\n\n"

        # Lấy thông tin Ban quản trị Guild
        guild_info = ""
        if message.guild:
            gm_names = []
            vg_names = []
            officer_names = []
            
            for role in message.guild.roles:
                r_name = role.name.lower()
                if r_name == "gm" or "guild master" in r_name or "guildmaster" in r_name:
                    gm_names.extend([m.display_name for m in role.members])
                elif r_name == "vg" or "vice guild" in r_name:
                    vg_names.extend([m.display_name for m in role.members])
                elif "officer" in r_name:
                    officer_names.extend([m.display_name for m in role.members])
            
            gm_names = list(set(gm_names))
            vg_names = list(set(vg_names))
            officer_names = list(set(officer_names))
            
            guild_info = f"--- Danh sách Ban quản trị Guild ---\n"
            guild_info += f"GM (Guild Master): {', '.join(gm_names) if gm_names else 'Chưa có dữ liệu'}\n"
            guild_info += f"VG (Vice Guild): {', '.join(vg_names) if vg_names else 'Chưa có dữ liệu'}\n"
            guild_info += f"Officer: {', '.join(officer_names) if officer_names else 'Chưa có dữ liệu'} (Tổng: {len(officer_names)})\n"
            guild_info += "--------------------------------------\n\n"

        # Thông tin người gửi và roles
        user_info = f"Câu hỏi của người dùng ({message.author.display_name})"
        if isinstance(message.author, discord.Member):
            roles = [role.name for role in message.author.roles if role.name != '@everyone']
            if roles:
                user_info += f" [Roles: {', '.join(roles)}]"
            else:
                user_info += " [Roles: Member]"
        user_info += ": "

        # Gộp ngữ cảnh và câu hỏi
        if guild_info or context_data or reply_context:
            prompt = guild_info + context_data + reply_context + f"\n{user_info}" + content
        else:
            prompt = f"{user_info}\n" + content
            
        with open("debug_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)

        # Bật typing indicator
        async with message.channel.typing():
            try:
                # Gọi OpenRouter API
                payload = {
                    "model": self.current_model,
                    "messages": [
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
                        try:
                            data = await resp.json()
                        except Exception:
                            text_resp = await resp.text()
                            data = {"error": {"message": f"Không thể parse JSON. Phản hồi: {text_resp[:100]}"}}

                        if resp.status == 429:
                            error_msg = data.get("error", {}).get("message", "Rate limit exceeded")
                            await message.reply(f"⚠️ Thôi toang rồi anh em ơi! Khóa API OpenRouter của tui vừa hết hạn mức sử dụng (Lỗi 429 Rate Limit). 💸\nChi tiết: `{error_msg}`")
                            return
                        elif resp.status != 200:
                            error_msg = data.get("error", {}).get("message", "Unknown API Error")
                            await message.reply(f"❌ Á đù, gọi API bị lỗi rồi (Mã {resp.status})! 😬\nChi tiết: `{error_msg}`")
                            return
                reply_text = data["choices"][0]["message"]["content"]

                # Discord giới hạn 2000 ký tự mỗi tin nhắn
                if len(reply_text) <= 2000:
                    await message.reply(reply_text)
                else:
                    # Nếu tin nhắn quá dài, cắt nhỏ ra để gửi
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])

            except Exception as e:
                print(f"OpenRouter API Error: {e}")
                await message.reply("Xin lỗi, tôi đang gặp lỗi khi kết nối với AI hoặc xử lý yêu cầu này.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatAI(bot))
