"""Script test độ trễ OpenRouter API (kèm system instruction thật) — chạy: python bot/test_openrouter_full.py"""
import json
import os
import time
import urllib.error
import urllib.request

from core.config import DATA_DIR, OPENROUTER_API_KEY, OPENROUTER_MODEL

URL = "https://openrouter.ai/api/v1/chat/completions"

if not OPENROUTER_API_KEY:
    raise SystemExit("Thiếu OPENROUTER_API_KEY trong .env")

instruction_path = os.path.join(DATA_DIR, "core", "templates", "chat_ai_instruction.txt")
with open(instruction_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

print(f"Model: {OPENROUTER_MODEL}")
print(f"System instruction: {len(system_instruction)} ký tự")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    body = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": question},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - start
        reply = result["choices"][0]["message"]["content"]
        print(f"\n[{elapsed:.2f}s] {reply}\n")
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi HTTP {e.code}: {e.read().decode('utf-8')}\n")
