import shutil

import discord
from discord.ext import commands

from core.config import BOT_SESSION_ID, GUILD_ID, TOKEN
from core.storage import restore_from_github
from core.webserver import keep_alive

# ==============================================================================
# KHỞI TẠO BOT CORE
# ==============================================================================
EXTENSIONS = [
    "cogs.about",
    "cogs.siphoned",
    "cogs.massing",
    "cogs.lastseen",
    "cogs.guildcheck",
    "cogs.alo_tts",
    "cogs.corebank",
    "cogs.chat_ai",
    "cogs.onboarding",
]


class TNCBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=["!", "."], intents=intents, help_command=None)

    async def setup_hook(self):
        restore_from_github()  # Kéo data JSON từ GitHub về trước khi load cog
        for extension in EXTENSIONS:
            await self.load_extension(extension)

        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"✅ Đã sync {len(synced)} slash commands vào guild!")


bot = TNCBot()


@bot.event
async def on_ready():
    print(f"✅ Bot đã hoạt động: {bot.user} | ID: {bot.user.id}")
    print(f"🔍 [Check] ffmpeg path: {shutil.which('ffmpeg')}")
    print(f"✅ TNC Bot v40 [Siphoned + Massing + GuildCheck + ALO-TTS + CoreBank] Online! Session: {BOT_SESSION_ID}")


if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
