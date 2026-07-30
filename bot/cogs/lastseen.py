import asyncio
import os
from datetime import datetime

import discord
from discord.ext import commands

from core.config import DATA_DIR
from core.storage import load_json, save_json

# ==============================================================================
# HỆ THỐNG FILTER THÀNH VIÊN (LastSeen)
# ==============================================================================
LASTSEEN_FILE = os.path.join(DATA_DIR, "tnc_lastseen_v1.json")


class LastSeenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}
        self.dirty = False

    async def cog_load(self):
        self.cache.update(load_json(LASTSEEN_FILE, dict))
        self.bot.loop.create_task(self._flush_loop())

    def save(self):
        save_json(self.cache, LASTSEEN_FILE, sync_github=False)

    async def _flush_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)
            if self.dirty:
                self.save()
                self.dirty = False
                print("💾 [LastSeen] Đã lưu xuống file (định kỳ 5 phút).")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        self.cache[str(message.author.id)] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.dirty = True


async def setup(bot: commands.Bot):
    await bot.add_cog(LastSeenCog(bot))
