import asyncio
import os
from datetime import datetime

import discord
from discord.ext import commands

from core.database import supabase

# ==============================================================================
# HỆ THỐNG FILTER THÀNH VIÊN (LastSeen)
# ==============================================================================

class LastSeenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}
        self.dirty = False

    async def cog_load(self):
        # Fetch initial data from Supabase to populate cache
        try:
            response = supabase.table("user_activity").select("user_id, last_seen").execute()
            if response.data:
                for row in response.data:
                    self.cache[row["user_id"]] = row["last_seen"]
        except Exception as e:
            print(f"Error loading user_activity from Supabase: {e}")
            
        self.bot.loop.create_task(self._flush_loop())

    def save(self):
        if not self.cache: return
        records = []
        for user_id, timestamp in self.cache.items():
            records.append({"user_id": str(user_id), "last_seen": timestamp})
        
        try:
            # Upsert in chunks
            chunk_size = 1000
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i+chunk_size]
                supabase.table("user_activity").upsert(chunk).execute()
        except Exception as e:
            print(f"Error saving user_activity to Supabase: {e}")

    async def _flush_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)
            if self.dirty:
                self.save()
                self.dirty = False
                print("💾 [LastSeen] Đã lưu xuống Supabase (định kỳ 5 phút).")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        self.cache[str(message.author.id)] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.dirty = True

async def setup(bot: commands.Bot):
    await bot.add_cog(LastSeenCog(bot))

