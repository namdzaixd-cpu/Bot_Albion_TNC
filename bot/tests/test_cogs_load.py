import asyncio

import main as bot_main


def test_all_cogs_load_without_error():
    """Load toàn bộ extension khai báo trong bot/main.py (không phải gateway thật)
    và kiểm tra các slash command chính đã đăng ký đúng — bắt lỗi import/setup
    của cog sớm, trước khi deploy."""

    async def _run():
        bot = bot_main.TNCBot()
        await bot._async_setup_hook()
        for extension in bot_main.EXTENSIONS:
            await bot.load_extension(extension)

        slash_names = {c.name for c in bot.tree.walk_commands()}
        for expected in ("aboutme", "massing", "spcheck", "guildcheck", "alojoin", "corelist"):
            assert expected in slash_names, f"Thiếu slash command /{expected}"

        await bot.close()

    asyncio.run(_run())
