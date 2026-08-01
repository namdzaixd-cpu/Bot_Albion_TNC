import json, asyncio, aiohttp, os, sys
sys.path.append('bot')
from core.config import OPENROUTER_MODEL, OPENROUTER_API_KEY
from core.config import DATA_DIR

async def main():
    instruction_path = os.path.join(DATA_DIR, "core", "templates", "chat_ai_instruction.txt")
    with open(instruction_path, "r", encoding="utf-8") as f:
        system_instruction = f.read()

    guild_info = "--- Danh sách Ban quản trị Guild ---\nGM (Guild Master): Chưa có dữ liệu\nVG (Vice Guild): Chưa có dữ liệu\nOfficer: Chưa có dữ liệu (Tổng: 0)\n--------------------------------------\n\n"
    user_info = "Câu hỏi của người dùng (Test): "
    content = "TNC đang có bao nhiêu officer"
    prompt = guild_info + f"\n{user_info}" + content

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:
            data = await resp.json()
            print("Status:", resp.status)
            print("Response:", json.dumps(data, indent=2, ensure_ascii=False))

asyncio.run(main())
