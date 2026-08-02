"""Script test API + model cho Gemini và Ollama — chạy: python bot/test_gemini_ollama.py"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request

# Load cấu hình từ bot
from core.config import GEMINI_API_KEY

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

print("=== HỆ THỐNG TEST DIRECT AI API ===")
print("1. Google Gemini API (Gọi trực tiếp Google AI Studio)")
print("2. Ollama API (Chạy local hoặc qua proxy)")
choice = input("Chọn API muốn test (1 hoặc 2): ").strip()

if choice == "1":
    # Cấu hình cho Gemini
    if not GEMINI_API_KEY:
        raise SystemExit("Thiếu GEMINI_API_KEY trong file .env")
        
    model_input = input("Nhập tên model Gemini (Mặc định: gemini-2.5-flash): ").strip()
    model = model_input if model_input else "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    print(f"\n[Gemini] Đang sử dụng model: {model}")

elif choice == "2":
    # Cấu hình cho Ollama
    url_input = input("Nhập URL Ollama (Mặc định: http://localhost:11434): ").strip()
    ollama_url = url_input if url_input else "http://localhost:11434"
    
    model_input = input("Nhập tên model Ollama (Mặc định: llama3): ").strip()
    model = model_input if model_input else "llama3"
    
    url = f"{ollama_url.rstrip('/')}/api/chat"
    print(f"\n[Ollama] Đang kết nối tới: {url} | Model: {model}")
else:
    raise SystemExit("Lựa chọn không hợp lệ!")

print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    # Chuẩn bị payload & headers cho từng loại API
    if choice == "1":
        # Request body cho Gemini
        body = json.dumps({
            "contents": [{"parts": [{"text": question}]}]
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
    else:
        # Request body cho Ollama
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": question}],
            "stream": False
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    start = time.perf_counter()
    
    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ssl_context) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - start
        
        # Parse kết quả phản hồi
        if choice == "1":
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply = result["message"]["content"]
            
        print(f"\n[{elapsed:.2f}s] {reply}\n")
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi HTTP {e.code}: {e.read().decode('utf-8')}\n")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi kết nối: {str(e)}\n")
