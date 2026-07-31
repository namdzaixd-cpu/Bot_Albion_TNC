"""Script test độ trễ Gemini API — chạy: python bot/test_gemini_latency.py"""
import os
import time

import google.generativeai as genai

from core.config import GEMINI_API_KEY, DATA_DIR

if not GEMINI_API_KEY:
    raise SystemExit("Thiếu GEMINI_API_KEY trong .env")

genai.configure(api_key=GEMINI_API_KEY)

instruction_path = os.path.join(DATA_DIR, "core", "templates", "chat_ai_instruction.txt")
with open(instruction_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

model = genai.GenerativeModel("gemini-3.5-flash-lite", system_instruction=system_instruction)

print(f"System instruction: {len(system_instruction)} ký tự")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    start = time.perf_counter()
    response = model.generate_content(question)
    elapsed = time.perf_counter() - start

    print(f"\n[{elapsed:.2f}s] {response.text}\n")
