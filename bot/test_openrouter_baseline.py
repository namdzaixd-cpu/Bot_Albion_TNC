"""Script test API + model OpenRouter, KHÔNG có system instruction — chạy: python bot/test_openrouter_baseline.py"""
import json
import time
import urllib.error
import urllib.request

from core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

API_KEY = OPENROUTER_API_KEY
MODEL = OPENROUTER_MODEL
URL = "https://openrouter.ai/api/v1/chat/completions"

if not API_KEY:
    raise SystemExit("Thiếu OPENROUTER_API_KEY trong .env")

print(f"Model: {MODEL}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": question}],
    }).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
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
