"""Script test API + model Google Gemini trực tiếp — chạy: python bot/test_gemini.py"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request

# Load cấu hình từ bot
from core.config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise SystemExit("Thiếu GEMINI_API_KEY trong file .env")

def choose_model():
    print("Chọn model Gemini:")
    print("1. gemini-3.5-flash-lite")
    print("2. gemini-3.1-flash-lite")
    print("3. gemma-4-31b-it")
    print("4. gemini-2.5-flash")
    model_choice = input("Lựa chọn (1-4, Mặc định: 1): ").strip()
    
    if model_choice == "2":
        return "gemini-3.1-flash-lite"
    elif model_choice == "3":
        return "gemma-4-31b-it"
    elif model_choice == "4":
        return "gemini-2.5-flash"
    elif model_choice == "1" or not model_choice:
        return "gemini-3.5-flash-lite"
    else:
        return model_choice

# Khởi tạo model và URL lần đầu
model = choose_model()
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

print(f"\n[Gemini] Đang sử dụng model: {model}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    # Nhận diện lệnh đổi model
    if question.lower() == "/model":
        print()
        model = choose_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        print(f"🔄 Đã chuyển sang model: {model}\n")
        continue

    body = json.dumps({
        "contents": [{"parts": [{"text": question}]}]
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    start = time.perf_counter()
    
    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ssl_context) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - start
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        print(f"\n[{elapsed:.2f}s] {reply}\n")
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi HTTP {e.code}: {e.read().decode('utf-8')}\n")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi kết nối: {str(e)}\n")
