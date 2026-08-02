import asyncio
import aiohttp
from core.config import OPENROUTER_API_KEY

async def test():
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://openrouter.ai/api/v1/auth/key", headers=headers) as resp:
            print(resp.status)
            print(await resp.json())

asyncio.run(test())
