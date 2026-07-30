    import discord
    from discord.ext import commands
    import aiohttp
    import random

    GELBOORU_API = "https://gelbooru.com/index.php?page=dapi&q=index&json=1"
    NEKOBOT_API = "https://nekobot.xyz/api/image"

    class NsfwCog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        # 🛑 BỘ LỌC ÉP CỨNG: CHỈ CHO PHÉP CHẠY NẾU NGƯỜI DÙNG GÕ DẤU CHẤM (.)
        async def cog_before_invoke(self, ctx):
            if not ctx.prefix.startswith('.'):
                # Nếu dùng dấu khác (như !), hủy lệnh ngay lập tức để không tranh với UnbelievaBoat
                raise commands.CommandError("Wrong prefix")
            return True

        # --------------------------------------------------------------------------
        # HÀM PHỤ TRỢ GỌI API HÌNH ẢNH
        # --------------------------------------------------------------------------
        async def fetch_real_nekobot(self, ctx, endpoint_type, title_text, color):
            url = f"{NEKOBOT_API}?type={endpoint_type}"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                embed = discord.Embed(title=title_text, color=color)
                                embed.set_image(url=data.get("message"))
                                embed.set_footer(text=f"Yêu cầu bởi: {ctx.author.name}")
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send("❌ API không trả về ảnh, thử lại sau nhé bro!")
                        else:
                            await ctx.send("❌ Hệ thống API đang bận, thử lại sau nhé!")
                except Exception as e:
                    await ctx.send("⚠️ Kết nối API thất bại (Timeout). Thử lại phát nữa xem bro!")

        async def fetch_anime_gelbooru(self, ctx, tags, title_text, color):
            full_url = f"{GELBOORU_API}&tags={tags}+nsfw&limit=50"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(full_url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "post" in data and len(data["post"]) > 0:
                                image_url = random.choice(data["post"]).get("file_url")
                                embed = discord.Embed(title=title_text, color=color)
                                embed.set_image(url=image_url)
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send(f"❓ Không tìm thấy ảnh nào với từ khóa `{tags}`.")
                except: 
                    await ctx.send("⚠️ Lỗi kết nối kho ảnh Rule34!")

        # --------------------------------------------------------------------------
        # NHÓM LỆNH NSFW (CHỈ NHẬN DẤU CHẤM '.')
        # --------------------------------------------------------------------------
        @commands.command(name="boob", aliases=["boobs"])
        @commands.is_nsfw()
        async def cmd_boob(self, ctx): 
            await self.fetch_real_nekobot(ctx, "boobs", "🍒 Vòng 1 (Real)", 0xff0055)

        @commands.command(name="butt", aliases=["butts"])
        @commands.is_nsfw()
        async def cmd_butt(self, ctx): 
            await self.fetch_real_nekobot(ctx, "ass", "🍑 Vòng 3 (Real)", 0xff9900)

        @commands.command(name="tatoo", aliases=["tatoos"])
        @commands.is_nsfw()
        async def cmd_tatoo(self, ctx):
            await self.fetch_real_nekobot(ctx, "hentai", "🎨 Tatoo & Art Concept", 0x9b59b6)

        @commands.command(name="crotch")
        @commands.is_nsfw()
        async def cmd_crotch(self, ctx):
            await self.fetch_real_nekobot(ctx, "thigh", "🔥 Crotch & Thigh Area", 0xe74c3c)

        @commands.command(name="r34")
        @commands.is_nsfw()
        async def cmd_r34(self, ctx, *, keyword: str = "anime"): 
            await self.fetch_anime_gelbooru(ctx, keyword.replace(" ", "_"), f"🖼️ Rule34: {keyword}", 0x00ffcc)

        # --------------------------------------------------------------------------
        # BỘ LỌC TỰ ĐỘNG CHẶN KHI DÙNG SAI KÊNH CHAT THƯỜNG
        # --------------------------------------------------------------------------
        @commands.Cog.listener()
        async def on_command_error(self, ctx, error):
            if isinstance(error, commands.NSFWChannelRequired):
                await ctx.send("⚠️ Lệnh này 18+, bro vui lòng mang vào kênh NSFW nhé!", delete_after=5)

    async def setup(bot):
        # Đăng ký lệnh nhận diện cả dấu chấm lẫn dấu chấm than để bot xử lý nội bộ trước khi lọc
        if "." not in bot.command_prefix:
            if isinstance(bot.command_prefix, str):
                bot.command_prefix = [bot.command_prefix, "."]
            elif isinstance(bot.command_prefix, list):
                bot.command_prefix.append(".")

        await bot.add_cog(NsfwCog(bot))