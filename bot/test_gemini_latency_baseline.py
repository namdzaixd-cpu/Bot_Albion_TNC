"""Script test độ trễ Gemini API gốc, KHÔNG có system instruction — chạy: python bot/test_gemini_latency_baseline.py"""
import time

import google.generativeai as genai

from core.config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise SystemExit("Thiếu GEMINI_API_KEY trong .env")

genai.configure(api_key=GEMINI_API_KEY, transport="rest")

model = genai.GenerativeModel("gemini-3.5-flash-lite")

print("Không có system instruction — test độ trễ gốc của API.")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    start = time.perf_counter()
    response = model.generate_content(question)
    elapsed = time.perf_counter() - start

    print(f"\n[{elapsed:.2f}s] {response.text}\n")
