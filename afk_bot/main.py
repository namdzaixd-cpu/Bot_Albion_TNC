"""
AFK Sitter Bot — con bot cực nhỏ, chỉ có nhiệm vụ ngồi AFK vô hạn trong 1 voice channel.
Deploy lên Render service RIÊNG, không bao giờ restart cùng bot chính.

Env vars cần thiết:
  AFK_BOT_TOKEN   — token của bot thứ 2 (tạo tại Discord Developer Portal)
  AFK_CHANNEL_ID  — ID của voice channel muốn bot ngồi AFK
"""

import asyncio
import os

import discord

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

TOKEN = os.environ["AFK_BOT_TOKEN"]
CHANNEL_ID = int(os.environ["AFK_CHANNEL_ID"])

# Khoảng thời gian giữa mỗi lần ping silence (giây).
# Discord tự kick bot sau ~60s idle khi một mình → dùng 30s để an toàn.
KEEPALIVE_INTERVAL = 30

# ──────────────────────────────────────────────────────────────────────────────
# Bot setup
# ──────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.voice_states = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"[AFK Bot] ✅ Online: {client.user} (ID: {client.user.id})")
    asyncio.create_task(afk_loop())


async def afk_loop():
    """Loop vô hạn: giữ bot trong voice channel bất kể chuyện gì xảy ra."""
    print(f"[AFK Bot] 🔁 Bắt đầu keepalive loop cho channel {CHANNEL_ID}")

    while True:
        try:
            channel = client.get_channel(CHANNEL_ID)
            if not channel:
                print(f"[AFK Bot] ⚠️  Không tìm thấy channel {CHANNEL_ID}, thử lại sau 10s...")
                await asyncio.sleep(10)
                continue

            guild = channel.guild
            vc = guild.voice_client

            # ── Chưa kết nối hoặc mất kết nối → reconnect ──
            if not vc or not vc.is_connected():
                try:
                    if vc:
                        await vc.disconnect(force=True)
                    vc = await channel.connect()
                    print(f"[AFK Bot] 🔗 Đã kết nối: {channel.name}")
                except Exception as e:
                    print(f"[AFK Bot] ❌ Kết nối thất bại: {e}, thử lại sau 5s...")
                    await asyncio.sleep(5)
                    continue

            # ── Bị kéo sang channel khác → quay về ──
            elif vc.channel.id != CHANNEL_ID:
                try:
                    await vc.move_to(channel)
                    print(f"[AFK Bot] ↩️  Quay lại: {channel.name}")
                except Exception as e:
                    print(f"[AFK Bot] ❌ Move thất bại: {e}")

            # ── Phát 20ms silence để tránh Discord idle-disconnect ──
            if vc and vc.is_connected() and not vc.is_playing():
                try:
                    vc.play(
                        discord.PCMAudio(b"\x00" * 3840),  # 20ms stereo 48kHz
                        after=lambda e: None,
                    )
                except Exception:
                    pass  # Không quan trọng, vòng lặp tiếp theo sẽ thử lại

        except Exception as e:
            print(f"[AFK Bot] 💥 Lỗi không mong đợi: {e}")

        await asyncio.sleep(KEEPALIVE_INTERVAL)


client.run(TOKEN)
