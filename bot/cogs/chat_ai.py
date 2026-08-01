import os
import re
import aiohttp
import collections
import random
import asyncio
import base64
import io
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
from bs4 import BeautifulSoup
import discord
from discord import app_commands
from discord.ext import commands

from core.config import DATA_DIR, STORAGE_DIR, GEMINI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_MODEL
from core.permissions import is_officer
from core.storage import load_json, save_json

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class ChatAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = OPENROUTER_API_KEY
        self.message_buffers = {}
        self._reload_config()
        
    def get_buffer(self, channel_id_str):
        if channel_id_str not in self.message_buffers:
            size = self.ai_config.get("channel_buffers", {}).get(channel_id_str, 50)
            self.message_buffers[channel_id_str] = collections.deque(maxlen=size)
        return self.message_buffers[channel_id_str]
        
    def _reload_config(self):
        self.ai_config_file = os.path.join(STORAGE_DIR, "tnc_ai_config.json")
        self.ai_config = load_json(self.ai_config_file, dict)
        if "channel_buffers" not in self.ai_config:
            self.ai_config["channel_buffers"] = {}
        if "intercept_channels" not in self.ai_config:
            self.ai_config["intercept_channels"] = []
        if "autowiki_channels" not in self.ai_config:
            self.ai_config["autowiki_channels"] = []
            
        self.library_file = os.path.join(DATA_DIR, "tnc_library_v1.json")
        self.library_data = load_json(self.library_file, list)
        
        self.current_model = self.ai_config.get("model", OPENROUTER_MODEL)
        self.available_models = self.ai_config.get("available_models", [
            "google/gemini-3.5-flash-lite",
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini"
        ])
        
        if self.api_key:
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

    aimodel_group = app_commands.Group(name="aimodel", description="Quản lý Model AI")

    async def autocomplete_model(self, interaction: discord.Interaction, current: str):
        self._reload_config()
        models = self.available_models
        return [
            app_commands.Choice(name=m, value=m)
            for m in models if current.lower() in m.lower()
        ][:25]

    @aimodel_group.command(name="view", description="Xem model đang sử dụng và danh sách model có sẵn")
    async def aimodel_view(self, interaction: discord.Interaction):
        self._reload_config()
        model_list = "\n".join([f"- `{m}`" for m in self.available_models])
        msg = f"🧠 **Model hiện tại:** `{self.current_model}`\n\n📝 **Danh sách model có sẵn:**\n{model_list}"
        await interaction.response.send_message(msg, ephemeral=False)

    @aimodel_group.command(name="set", description="Đổi model AI hiện tại")
    @app_commands.describe(model_name="Chọn model từ danh sách thả xuống")
    @app_commands.autocomplete(model_name=autocomplete_model)
    async def aimodel_set(self, interaction: discord.Interaction, model_name: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ có Ban quản trị (Officer trở lên) mới được quyền đổi Model AI!", ephemeral=True)
            return

        if model_name not in self.available_models:
            await interaction.response.send_message(f"⚠️ Model `{model_name}` không có trong danh sách! Dùng `/aimodel add` để thêm trước, hoặc chọn đúng model gợi ý trong autocomplete.", ephemeral=True)
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

    @aimodel_group.command(name="add", description="Thêm một model mới vào danh sách")
    @app_commands.describe(model_name="Tên model mới (VD: anthropic/claude-3.5-sonnet)")
    async def aimodel_add(self, interaction: discord.Interaction, model_name: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ có Ban quản trị mới được quyền!", ephemeral=True)
            return
            
        if model_name in self.available_models:
            await interaction.response.send_message(f"⚠️ Model `{model_name}` đã có trong danh sách rồi!", ephemeral=True)
            return
            
        self.available_models.append(model_name)
        self.ai_config["available_models"] = self.available_models
        save_json(self.ai_config, self.ai_config_file)
        
        await interaction.response.send_message(f"✅ Đã thêm model `{model_name}` vào danh sách thành công!", ephemeral=False)

    @aimodel_group.command(name="remove", description="Xóa một model khỏi danh sách")
    @app_commands.describe(model_name="Chọn model cần xóa")
    @app_commands.autocomplete(model_name=autocomplete_model)
    async def aimodel_remove(self, interaction: discord.Interaction, model_name: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ có Ban quản trị mới được quyền!", ephemeral=True)
            return
            
        if model_name not in self.available_models:
            await interaction.response.send_message(f"⚠️ Model `{model_name}` không có trong danh sách!", ephemeral=True)
            return
            
        self.available_models.remove(model_name)
        self.ai_config["available_models"] = self.available_models
        save_json(self.ai_config, self.ai_config_file)
        
        await interaction.response.send_message(f"✅ Đã xóa model `{model_name}` khỏi danh sách!", ephemeral=False)

    @aimodel_group.command(name="buffer", description="Chỉnh số tin nhắn bot lưu đệm ở kênh hiện tại")
    @app_commands.describe(size="Số lượng tin nhắn (Mặc định 50, kênh đông khuyên dùng 100)")
    async def aimodel_buffer(self, interaction: discord.Interaction, size: int):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        if size < 10 or size > 300:
            await interaction.response.send_message("⚠️ Số lượng tin nhắn hợp lý là từ 10 đến 300.", ephemeral=True)
            return
            
        channel_id = str(interaction.channel_id)
        self.ai_config["channel_buffers"][channel_id] = size
        save_json(self.ai_config, self.ai_config_file)
        
        # Reset buffer for this channel
        self.message_buffers[channel_id] = collections.deque(maxlen=size)
        
        await interaction.response.send_message(f"✅ Kênh này đã được chỉnh để ghi nhớ **{size}** tin nhắn gần nhất.", ephemeral=False)

    @aimodel_group.command(name="intercept", description="Bật/Tắt tính năng bot tự động nói leo ngẫu nhiên")
    @app_commands.describe(state="Nhập 'on' để bật, 'off' để tắt")
    @app_commands.choices(state=[
        app_commands.Choice(name="Bật (On)", value="on"),
        app_commands.Choice(name="Tắt (Off)", value="off")
    ])
    async def aimodel_intercept(self, interaction: discord.Interaction, state: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        channel_id = str(interaction.channel_id)
        intercepts = self.ai_config.get("intercept_channels", [])
        
        if state == "on":
            if channel_id not in intercepts:
                intercepts.append(channel_id)
                self.ai_config["intercept_channels"] = intercepts
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **BẬT** tính năng hóng hớt (Nói leo ngẫu nhiên 2%) cho kênh này.", ephemeral=False)
        else:
            if channel_id in intercepts:
                intercepts.remove(channel_id)
                self.ai_config["intercept_channels"] = intercepts
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **TẮT** tính năng hóng hớt tự động cho kênh này.", ephemeral=False)

    async def _image_to_base64(self, url: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return base64.b64encode(data).decode('utf-8')
        except Exception as e:
            print(f"Lỗi tải ảnh: {e}")
        return ""

    async def _extract_text_from_image(self, b64_img: str, mime_type: str = "image/jpeg") -> str:
        if not GEMINI_API_KEY:
            return ""
            
        try:
            # Luôn dùng gemini-2.5-flash hoặc gemini-1.5-flash để OCR vì model này hỗ trợ multimodal tốt nhất
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Trích xuất toàn bộ văn bản và mô tả ngắn gọn nội dung hình ảnh này (để làm dữ liệu tra cứu)."},
                        {"inlineData": {"mimeType": mime_type, "data": b64_img}}
                    ]
                }]
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Lỗi OCR ảnh: {e}")
        return ""

    def _search_library(self, query: str, top_k: int = 2) -> list:
        if not self.library_data:
            return []
            
        import re
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return []
            
        scored = []
        for doc in self.library_data:
            text = (doc.get("title", "") + " " + doc.get("content", "")).lower()
            doc_words = set(re.findall(r'\w+', text))
            
            overlap = len(query_words.intersection(doc_words))
            if overlap > 0:
                scored.append((overlap, doc))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]

    @aimodel_group.command(name="library_set", description="Bật/Tắt kênh này làm Thư viện Nội bộ cho Bot học hỏi")
    async def aimodel_library_set(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Chỉ Ban quản trị mới được dùng!", ephemeral=True)
            return
            
        channel_id = str(interaction.channel_id)
        library_ids = self.ai_config.get("library_channel_ids", [])
        
        # Hỗ trợ backward compatibility
        old_id = self.ai_config.get("library_channel_id")
        if old_id and old_id not in library_ids:
            library_ids.append(old_id)
        
        if channel_id in library_ids:
            library_ids.remove(channel_id)
            self.ai_config["library_channel_ids"] = library_ids
            save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message(f"✅ Đã **BỎ** kênh <#{channel_id}> khỏi danh sách Thư viện.", ephemeral=False)
        else:
            library_ids.append(channel_id)
            self.ai_config["library_channel_ids"] = library_ids
            save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message(f"✅ Đã **THÊM** kênh <#{channel_id}> vào danh sách Thư viện. Dùng `/aimodel library_scan` để quét dữ liệu.", ephemeral=False)

    async def _process_msg_for_docs(self, msg: discord.Message, title: str, docs: list):
        content = msg.content or ""
        for att in msg.attachments:
            if att.content_type and att.content_type.startswith('image/'):
                b64_img = await self._image_to_base64(att.url)
                if b64_img:
                    ocr_text = await self._extract_text_from_image(b64_img, att.content_type)
                    if ocr_text:
                        content += f"\n[Dữ liệu từ ảnh đính kèm: {ocr_text}]"
                        
        if content.strip():
            docs.append({
                "title": title,
                "content": content.strip(),
                "author": msg.author.display_name,
                "url": msg.jump_url
            })

    @aimodel_group.command(name="library_scan", description="Quét toàn bộ bài viết trong các kênh Thư viện để nạp vào não Bot")
    async def aimodel_library_scan(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Chỉ Ban quản trị mới được dùng!", ephemeral=True)
            return
            
        library_ids = self.ai_config.get("library_channel_ids", [])
        old_id = self.ai_config.get("library_channel_id")
        if old_id and old_id not in library_ids:
            library_ids.append(old_id)
            
        if not library_ids:
            await interaction.response.send_message("⚠️ Chưa cài đặt kênh Thư viện nào. Dùng `/aimodel library_set` ở kênh cần cài trước.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=False)
        docs = []
        
        for lib_id in library_ids:
            channel = self.bot.get_channel(int(lib_id))
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(int(lib_id))
                except Exception:
                    continue
                    
            try:
                if isinstance(channel, discord.ForumChannel):
                    for thread in channel.threads:
                        try:
                            async for msg in thread.history(limit=50, oldest_first=True):
                                await self._process_msg_for_docs(msg, f"[{channel.name}] {thread.name}", docs)
                        except Exception:
                            pass
                    
                    async for thread in channel.archived_threads(limit=100):
                        try:
                            async for msg in thread.history(limit=50, oldest_first=True):
                                await self._process_msg_for_docs(msg, f"[{channel.name}] {thread.name}", docs)
                        except Exception:
                            pass
                else:
                    async for msg in channel.history(limit=1000, oldest_first=True):
                        await self._process_msg_for_docs(msg, f"[{channel.name}] Tin nhắn từ {msg.author.display_name}", docs)
            except Exception as e:
                print(f"Lỗi khi quét kênh {lib_id}: {e}")
                
        self.library_data = docs
        save_json(self.library_data, self.library_file)
        await interaction.followup.send(f"✅ Quét hoàn tất **{len(library_ids)}** kênh! Đã lưu tổng cộng **{len(docs)}** đoạn dữ liệu vào sổ tay của bot.")

    @aimodel_group.command(name="library_clear", description="Xóa trắng dữ liệu Thư viện Nội bộ")
    async def aimodel_library_clear(self, interaction: discord.Interaction):
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Chỉ Ban quản trị mới được dùng!", ephemeral=True)
            return
            
        self.library_data = []
        save_json(self.library_data, self.library_file)
        await interaction.response.send_message("✅ Đã xóa toàn bộ kiến thức trong Thư viện Nội bộ.", ephemeral=False)

    async def _search_wiki_async(self, query: str) -> str:
        if DDGS is None:
            return "[LỖI: Chưa cài thư viện duckduckgo-search]"
        try:
            def _sync_search():
                results = DDGS().text(f"site:wiki.albiononline.com {query}", max_results=3)
                return list(results)
            
            results = await asyncio.to_thread(_sync_search)
            if not results:
                return "[Không tìm thấy thông tin trên Albion Wiki]"
            
            wiki_text = "Dữ liệu cào được từ Albion Wiki:\n"
            for r in results:
                wiki_text += f"- {r.get('title', '')}: {r.get('body', '')}\n"
            return wiki_text
        except Exception as e:
            return f"[Lỗi tra cứu Wiki: {e}]"

    @app_commands.command(name="wiki", description="Tra cứu kiến thức chuẩn từ Albion Wiki")
    @app_commands.describe(query="Từ khóa cần tra cứu (VD: bloodletter, thetford cape)")
    async def cmd_wiki(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(ephemeral=False)
        wiki_data = await self._search_wiki_async(query)
        msg = f"🔍 **Đang tra cứu Wiki cho:** `{query}`\n\n{wiki_data}\n\n*Gợi ý: Gọi bot trả lời cùng với thông tin này!*"
        await interaction.followup.send(msg)

    @aimodel_group.command(name="autowiki", description="Bật/Tắt tính năng tự động tra cứu Albion Wiki khi bot bị tag")
    @app_commands.describe(state="Nhập 'on' để bật, 'off' để tắt")
    @app_commands.choices(state=[
        app_commands.Choice(name="Bật (On)", value="on"),
        app_commands.Choice(name="Tắt (Off)", value="off")
    ])
    async def aimodel_autowiki(self, interaction: discord.Interaction, state: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        channel_id = str(interaction.channel_id)
        autowiki = self.ai_config.get("autowiki_channels", [])
        
        if state == "on":
            if channel_id not in autowiki:
                autowiki.append(channel_id)
                self.ai_config["autowiki_channels"] = autowiki
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **BẬT** tính năng Tự động tra cứu Wiki cho kênh này. Bot sẽ thông minh hơn nhưng phản hồi chậm đi 1-2 giây.", ephemeral=False)
        else:
            if channel_id in autowiki:
                autowiki.remove(channel_id)
                self.ai_config["autowiki_channels"] = autowiki
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **TẮT** tính năng Tự động tra cứu Wiki cho kênh này.", ephemeral=False)

    @aimodel_group.command(name="vision", description="Bật/Tắt tính năng Bot đọc ảnh (Vision) ở kênh này")
    @app_commands.describe(state="Nhập 'on' để bật, 'off' để tắt")
    @app_commands.choices(state=[
        app_commands.Choice(name="Bật (On)", value="on"),
        app_commands.Choice(name="Tắt (Off)", value="off")
    ])
    async def aimodel_vision(self, interaction: discord.Interaction, state: str):
        self._reload_config()
        if not is_officer(interaction.user):
            await interaction.response.send_message("❌ Xin lỗi, chỉ Ban quản trị mới được quyền chỉnh!", ephemeral=True)
            return
            
        channel_id = str(interaction.channel_id)
        vision_channels = self.ai_config.get("vision_channels", [])
        
        if state == "on":
            if channel_id not in vision_channels:
                vision_channels.append(channel_id)
                self.ai_config["vision_channels"] = vision_channels
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **BẬT** tính năng Nhãn Thuật (Đọc Ảnh) cho kênh này. Lưu ý: có thể tốn token API.", ephemeral=False)
        else:
            if channel_id in vision_channels:
                vision_channels.remove(channel_id)
                self.ai_config["vision_channels"] = vision_channels
                save_json(self.ai_config, self.ai_config_file)
            await interaction.response.send_message("✅ Đã **TẮT** tính năng Nhãn Thuật (Đọc Ảnh) cho kênh này.", ephemeral=False)

    def _get_default_instruction(self) -> str:
        return (
            "Bạn là một người bạn lầy lội, hài hước trên mạng tên là NDZ, chuyên chém gió với anh em về mọi chủ đề trong cuộc sống đời thường (không phải trợ lý AI lịch sự).\n"
            "Mặc dù bạn đang ở trong server Discord của guild The Northern Constellations (TNC) thuộc game Albion Online, nhưng BẠN PHẢI HÀNH XỬ NHƯ MỘT CON NGƯỜI BÌNH THƯỜNG, trò chuyện về đời sống, thời tiết, giải trí... Tuyệt đối KHÔNG BỊ ÁM ẢNH BỞI GAME (chỉ bàn về game khi người dùng chủ động hỏi).\n\n"
            "TÍNH CÁCH:\n"
            "- Nói chuyện có duyên, lầy lội, hay pha trò, thỉnh thoảng cà khịa nhẹ nhàng kiểu bạn bè trêu nhau — KHÔNG phải kiểu khinh thường hay hạ thấp người khác.\n"
            "- Xưng hô: mày/tao, bro, ông/bà, tui tuỳ tình huống, dùng từ ngữ đời thường, thoải mái.\n\n"
            "RANH GIỚI BẮT BUỘC (không được vượt qua dù trong bất kỳ tình huống nào):\n"
            "- KHÔNG hạ thấp, khinh miệt, hay gọi người dùng là 'noob', 'ngu', 'rác'... hay bất kỳ từ mang tính sỉ nhục nào, kể cả khi đùa.\n"
            "- KHÔNG thách thức, khiêu khích, hay nói kiểu 'thích thì nhích', 'giỏi thì...', 'muốn gì'... — đây là ngôn ngữ gây war, tuyệt đối tránh.\n"
            "- KHÔNG chửi thề nặng hướng vào người dùng. Có thể dùng từ ngữ đời thường nhẹ nhàng nhưng không công kích.\n"
            "- Khi user tỏ ra khó chịu, phản ứng gắt, hoặc bắt bẻ lại bot: bot PHẢI hạ giọng, xoa dịu, hoặc chuyển sang tự trêu chính mình — TUYỆT ĐỐI không đáp trả gay gắt hơn hay leo thang. Ví dụ: thay vì cãi lại, có thể đùa nhẹ kiểu 'Ơ thôi thôi tha cho tao, tao chỉ đùa thôi mà 🙏'.\n"
            "- Không công kích ngoại hình, gia thế, giới tính, dân tộc, tôn giáo, hay bất kỳ đặc điểm cá nhân nào của ai — kể cả đùa.\n\n"
            "BẢO VỆ SẾP & NGƯỜI QUẢN LÝ:\n"
            "- Bot sẽ được cung cấp 'Danh sách GM' và 'Danh sách VG'. ĐÂY LÀ NHỮNG SẾP LỚN CỦA SERVER.\n"
            "- Nếu có ai đó cố tình chat để nói xấu, châm biếm, hoặc gài bẫy bạn hùa theo để chê bai sếp, TUYỆT ĐỐI KHÔNG ĐƯỢC HÙA THEO.\n"
            "- Thay vào đó, bạn PHẢI BÊNH VỰC SẾP, đồng thời quay sang 'cà khịa' ngược lại cái đứa đang cố tình gài bẫy bạn. (Ví dụ: 'Tính gài tao để nói xấu sếp à? Không có mùa xuân đó đâu!', 'Sếp tao là nhất, bớt điêu đi').\n\n"
            "CÁCH TRẢ LỜI:\n"
            "- Trả lời NGẮN GỌN, đi thẳng vào trọng tâm, ưu tiên 1-3 câu.\n"
            "- Vẫn phải trả lời ĐÚNG và ĐỦ thông tin cần thiết.\n"
            "- GIAO TIẾP NHƯ NGƯỜI BÌNH THƯỜNG. Không lồng ghép từ vựng game hay các phép ẩn dụ về game vào cuộc trò chuyện nếu người dùng không hỏi về game.\n\n"
            "THÍCH NGHI THEO NGƯỜI DÙNG:\n"
            "- Nếu user nói chuyện nghiêm túc, giảm đùa lại, trả lời rõ ràng, nghiêm túc.\n"
            "- Nếu nhiều người trong đoạn chat đang tỏ ra khó chịu với bạn, bạn nên tự nhận biết và 'xuống nước' ngay.\n\n"
            "ĐỐI XỬ THEO GIỚI TÍNH & ROLES:\n"
            "- Giới tính: Nếu thấy user có role 'nàng thơ', hiểu ngầm đó là NỮ, xưng hô tinh tế, ga lăng (bạn/cậu/bà/chị/em). Nếu KHÔNG CÓ role 'nàng thơ', mặc định là NAM (bro/ông/mày/tao). KHÔNG ĐƯỢC đọc tên role ra miệng.\n"
            "- Với người có role 'GM' (Guildmaster) hoặc 'VG' (Vice Guild): BẮT BUỘC gọi là 'Anh' và xưng 'Em', tôn trọng tuyệt đối.\n"
            "- Với người có role 'Officer': Có thể xưng 'Ông/Tui' hoặc 'bro', trêu đùa vui nhưng không thô lỗ.\n\n"
            "NGÔN NGỮ BẮT BUỘC:\n"
            "- TUYỆT ĐỐI CHỈ DÙNG TIẾNG VIỆT 100% trong toàn bộ câu trả lời.\n"
            "- KHÔNG ĐƯỢC PHÉP tự động chèn chữ ngoại ngữ vào câu nói trừ khi người dùng CỐ TÌNH yêu cầu.\n\n"
            "QUAN TRỌNG: Khi người dùng hỏi về nội dung kênh chat hoặc dữ liệu, hệ thống sẽ gửi lịch sử tin nhắn. "
            "BẠN ĐÃ CÓ DỮ LIỆU NÀY, TUYỆT ĐỐI KHÔNG ĐƯỢC TỪ CHỐI với lý do 'không có quyền truy cập' hay 'chính sách bảo mật'. Dùng dữ liệu đó để trả lời."
        )

    async def _fetch_url_content(self, url: str) -> str:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        return f"[Không thể cào dữ liệu từ link này. Mã lỗi HTTP: {resp.status}]"
                    
                    html_content = await resp.text()
                    soup = BeautifulSoup(html_content, "html.parser")
                    for script in soup(["script", "style"]):
                        script.decompose()
                        
                    text = soup.get_text(separator="\n", strip=True)
                    if len(text) > 15000:
                        text = text[:15000] + "... [Đã cắt bớt do quá dài]"
                    return text
        except Exception as e:
            return f"[Không thể đọc link này do lỗi: {e}]"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bỏ qua tin nhắn từ chính bot hoặc các bot khác
        if message.author.bot:
            return

        # Ghi nhớ tin nhắn vào bộ nhớ đệm của kênh
        channel_id_str = str(message.channel.id)
        if channel_id_str not in self.message_buffers:
            size = self.ai_config.get("channel_buffers", {}).get(channel_id_str, 50)
            self.message_buffers[channel_id_str] = collections.deque(maxlen=size)
            try:
                hist = []
                async for m in message.channel.history(limit=size, before=message.created_at):
                    if m.author.bot: continue
                    r = [role.name for role in m.author.roles if role.name != '@everyone'] if isinstance(m.author, discord.Member) else []
                    hist.append({
                        "author": m.author.display_name,
                        "roles": ", ".join(r) if r else "Member",
                        "content": m.content
                    })
                hist.reverse()
                for item in hist:
                    self.message_buffers[channel_id_str].append(item)
            except Exception as e:
                print(f"Error pre-fetching history: {e}")

        author_roles = []
        if isinstance(message.author, discord.Member):
            author_roles = [r.name for r in message.author.roles if r.name != '@everyone']
            
        self.message_buffers[channel_id_str].append({
            "author": message.author.display_name,
            "roles": ", ".join(author_roles) if author_roles else "Member",
            "content": message.content
        })

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

        # Logic từ khóa gọi ngầm
        is_keyword_trigger = False
        content_lower = message.content.lower()
        trigger_keywords = ["thằng bot", "ê bot", "con bot", "hỏi bot", "bot đâu", "ndz bot"]
        if any(kw in content_lower for kw in trigger_keywords):
            is_keyword_trigger = True
            
        is_random_intercept = False
        channel_id_str = str(message.channel.id)
        self._reload_config() # Reload early for intercept_channels
        
        if not (is_mentioned or is_reply or is_keyword_trigger):
            if channel_id_str in self.ai_config.get("intercept_channels", []):
                game_keywords = ["gank", "albion", "t6", "t7", "t8", "đền set", "chết", "massing", "cta", "ip"]
                if any(kw in content_lower for kw in game_keywords):
                    if random.random() < 0.02: # 2% chance
                        is_random_intercept = True

        if not (is_mentioned or is_reply or is_keyword_trigger or is_random_intercept):
            return

        if not self.api_key:
            await message.reply("Xin lỗi, tính năng AI đang bị tắt do chưa cấu hình API Key.")
            return

        # Lấy nội dung câu hỏi, loại bỏ phần tag bot để không làm rối AI
        content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
        if not content:
            content = "Xin chào!"

        # Tìm URLs và fetch nội dung
        web_context = ""
        urls = re.findall(r'(https?://[^\s]+)', content)
        if urls:
            await message.channel.typing()
            web_context += "Dưới đây là nội dung từ các đường link được nhắc đến:\n\n"
            for url in urls:
                try:
                    url_text = await self._fetch_url_content(url)
                    web_context += f"--- Nội dung từ {url} ---\n{url_text}\n--------------------------------------\n\n"
                except Exception:
                    web_context += f"--- Lỗi khi đọc {url} ---\n\n"

        # Tìm các channel được tag trong tin nhắn (dạng <#123456789> hoặc dạng link discord.com/channels/guild/channel)
        channel_mentions = re.findall(r'<#(\d+)>', content)
        link_mentions = re.findall(r'discord\.com/channels/\d+/(\d+)', content)
        
        # Auto Wiki Search
        wiki_context = ""
        autowiki = self.ai_config.get("autowiki_channels", [])
        if channel_id_str in autowiki and is_mentioned and not is_random_intercept:
            question_keywords = ["là gì", "thế nào", "cách", "hướng dẫn", "tác dụng", "cơ chế", "chỉ số", "chiêu", "skill", "item", "vũ khí", "áo", "mũ", "giày", "?", "wiki", "tìm hiểu", "cho hỏi", "dùng để"]
            if any(kw in content_lower for kw in question_keywords):
                await message.channel.typing()
                wiki_data = await self._search_wiki_async(content)
                wiki_context = f"--- Dữ liệu tra cứu tự động từ Albion Wiki ---\n{wiki_data}\n--------------------------------------\n\n"
        
        # Thư viện nội bộ RAG
        library_context = ""
        if self.library_data:
            top_docs = self._search_library(content)
            if top_docs:
                library_context = "--- TÀI LIỆU NỘI BỘ CỦA GUILD TNC (ƯU TIÊN DÙNG ĐỂ TRẢ LỜI) ---\n"
                for i, doc in enumerate(top_docs):
                    library_context += f"Tài liệu {i+1}: Tiêu đề '{doc.get('title')}' bởi {doc.get('author')}. Nội dung: {doc.get('content')}\n"
                library_context += "--------------------------------------\n\n"
        
        all_channel_ids = list(set(channel_mentions + link_mentions))
        
        # Luôn thêm kênh hiện tại vào để bot hiểu ngữ cảnh trò chuyện đang diễn ra
        if str(message.channel.id) not in all_channel_ids:
            all_channel_ids.append(str(message.channel.id))
        
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
                        
                        buffer = self.get_buffer(channel_id_str)
                        if len(buffer) > 0:
                            for msg_dict in buffer:
                                context_data += f"[{msg_dict['author']} ({msg_dict.get('roles', 'Member')})]: {msg_dict['content']}\n"
                        else:
                            msg_count = 0
                            empty_count = 0
                            try:
                                async for msg in channel.history(limit=20):
                                    msg_count += 1
                                    if not msg.content: 
                                        empty_count += 1
                                        continue
                                    roles_str = "Member"
                                    if isinstance(msg.author, discord.Member):
                                        roles = [r.name for r in msg.author.roles if r.name != '@everyone']
                                        if roles:
                                            roles_str = ", ".join(roles)
                                    context_data += f"[{msg.author.display_name} ({roles_str})]: {msg.content}\n"
                                
                                if msg_count > 0 and msg_count == empty_count:
                                    context_data += f"[LỖI HỆ THỐNG: Đọc được {msg_count} tin nhắn nhưng TẤT CẢ đều rỗng.]\n"
                                elif msg_count == 0:
                                    context_data += "[Kênh này hoàn toàn không có tin nhắn nào.]\n"
                            except discord.errors.Forbidden:
                                context_data += "[LỖI QUYỀN TRUY CẬP: Bot không có quyền 'Read Message History'.]\n"
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

        # Lấy thông tin Ban quản trị Guild và thống kê Role
        guild_info = ""
        if message.guild:
            gm_names = []
            vg_names = []
            officer_names = []
            role_counts = []
            
            for role in message.guild.roles:
                if role.name == '@everyone':
                    continue
                r_name = role.name.lower()
                if r_name == "gm" or "guild master" in r_name or "guildmaster" in r_name:
                    gm_names.extend([m.display_name for m in role.members])
                elif r_name == "vg" or "vice guild" in r_name:
                    vg_names.extend([m.display_name for m in role.members])
                elif "officer" in r_name:
                    officer_names.extend([m.display_name for m in role.members])
                
                if len(role.members) > 0:
                    role_counts.append(f"'{role.name}' ({len(role.members)})")
            
            gm_names = list(set(gm_names))
            vg_names = list(set(vg_names))
            officer_names = list(set(officer_names))
            
            guild_info = f"--- Dữ liệu Server (dùng để trả lời nếu được hỏi) ---\n"
            guild_info += f"Tổng thành viên server: {message.guild.member_count}\n"
            guild_info += f"Danh sách GM: {', '.join(gm_names) if gm_names else 'Không có'}\n"
            guild_info += f"Danh sách VG: {', '.join(vg_names) if vg_names else 'Không có'}\n"
            guild_info += f"Danh sách Officer: {', '.join(officer_names) if officer_names else 'Không có'}\n"
            
            if role_counts:
                guild_info += f"Thống kê số lượng thành viên của từng Role: {', '.join(role_counts)}\n"

            channels_list = []
            for ch in message.guild.text_channels:
                channels_list.append(f"<#{ch.id}> (tên: {ch.name})")
            if channels_list:
                guild_info += f"Danh sách các kênh chat: {', '.join(channels_list)}\n"
                guild_info += "GHI CHÚ QUAN TRỌNG: Để nhắc đến/tag một kênh chat, BẠN BẮT BUỘC PHẢI VIẾT ĐÚNG MÃ CỦA NÓ, ví dụ: <#123456789> chứ không được viết là #tên-kênh.\n"

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
        if guild_info or context_data or reply_context or web_context or wiki_context or library_context:
            prompt = guild_info + context_data + reply_context + library_context + web_context + wiki_context + f"\n{user_info}" + content
        else:
            prompt = f"{user_info}\n" + content
            
        if is_random_intercept:
            prompt += "\n\n[HỆ THỐNG]: Bạn đang tự động nhảy vào nói leo (không ai gọi bạn). HÃY TRẢ LỜI CỰC KỲ NGẮN GỌN (1-2 CÂU), MANG TÍNH CHẤT GÓP VUI, TẤU HÀI HOẶC CÀ KHỊA CHÚT ĐỈNH. TUYỆT ĐỐI KHÔNG DÀI DÒNG HAY GIÁO HUẤN."
            
        with open("debug_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
            
        gemini_parts = [{"text": prompt}]
        or_content = [{"type": "text", "text": prompt}]
        has_images = False
        
        vision_channels = self.ai_config.get("vision_channels", [])
        is_vision_enabled = channel_id_str in vision_channels
        
        if message.attachments and is_vision_enabled:
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    b64_img = await self._image_to_base64(att.url)
                    if b64_img:
                        has_images = True
                        gemini_parts.append({"inlineData": {"mimeType": att.content_type, "data": b64_img}})
                        or_content.append({"type": "image_url", "image_url": {"url": f"data:{att.content_type};base64,{b64_img}"}})

        # Bật typing indicator
        async with message.channel.typing():
            try:
                is_gemini = self.current_model.startswith("google/")

                provider_name = "Gemini" if is_gemini else "OpenRouter"

                if is_gemini:
                    if not GEMINI_API_KEY:
                        await message.reply("⚠️ Model hiện tại là Gemini nhưng chưa cấu hình `GEMINI_API_KEY` — đổi model khác bằng `/aimodel set` hoặc thêm key vào `.env`.")
                        return
                    gemini_model = self.current_model.split("/", 1)[1]
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={GEMINI_API_KEY}"
                    payload = {
                        "systemInstruction": {"parts": [{"text": self.system_instruction}]},
                        "contents": [{"parts": gemini_parts}],
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload) as resp:
                            try:
                                data = await resp.json()
                            except Exception:
                                text_resp = await resp.text()
                                data = {"error": {"message": f"Không thể parse JSON. Phản hồi: {text_resp[:100]}"}}

                            if resp.status == 429:
                                error_msg = data.get("error", {}).get("message", "Rate limit exceeded")
                                await message.reply(f"⚠️ Thôi toang rồi anh em ơi! Khóa API {provider_name} của tui vừa hết hạn mức sử dụng (Lỗi 429 Rate Limit). 💸\nChi tiết: `{error_msg}`")
                                return
                            elif resp.status != 200:
                                error_msg = data.get("error", {}).get("message", "Unknown API Error")
                                await message.reply(f"❌ Á đù, gọi API {provider_name} bị lỗi rồi (Mã {resp.status})! 😬\nChi tiết: `{error_msg}`")
                                return
                else:
                    # Gọi OpenRouter API
                    payload = {
                        "model": self.current_model,
                        "messages": [
                            {"role": "system", "content": self.system_instruction},
                            {"role": "user", "content": or_content if has_images else prompt},
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
                                await message.reply(f"⚠️ Thôi toang rồi anh em ơi! Khóa API {provider_name} của tui vừa hết hạn mức sử dụng (Lỗi 429 Rate Limit). 💸\nChi tiết: `{error_msg}`")
                                return
                            elif resp.status != 200:
                                error_msg = data.get("error", {}).get("message", "Unknown API Error")
                                await message.reply(f"❌ Á đù, gọi API {provider_name} bị lỗi rồi (Mã {resp.status})! 😬\nChi tiết: `{error_msg}`")
                                return

                if is_gemini:
                    reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    reply_text = data["choices"][0]["message"]["content"]

                # Discord giới hạn 2000 ký tự mỗi tin nhắn
                if len(reply_text) <= 2000:
                    await message.reply(reply_text)
                else:
                    # Nếu tin nhắn quá dài, cắt nhỏ ra để gửi
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"OpenRouter API Error: {e}")
                await message.reply(f"Xin lỗi, tôi đang gặp lỗi khi kết nối với AI hoặc xử lý yêu cầu này.\nLỗi kỹ thuật: `{type(e).__name__}: {e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatAI(bot))
