"""Script test API + model Ollama — chạy: python bot/test_ollama.py"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

# URL Ollama cố định, không cần nhập lại
ollama_url = "https://ollama.com/api"

print("Chọn model Ollama:")
print("1. minimax-m3")
print("2. gpt-oss:120b")
model_input = input("Lựa chọn (1 hoặc 2, Mặc định: 1): ").strip()

if model_input == "2":
    model = "gpt-oss:120b"
elif model_input == "1" or not model_input:
    model = "minimax-m3"
else:
    model = model_input

# Chuẩn hóa URL để tránh trùng lặp cụm /api/chat hoặc /api
url_clean = ollama_url.rstrip('/')
if url_clean.endswith("/api/chat"):
    url = url_clean
elif url_clean.endswith("/api"):
    url = f"{url_clean}/chat"
else:
    url = f"{url_clean}/api/chat"

print(f"\n[Ollama] Đang kết nối tới: {url} | Model: {model}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

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
        reply = result["message"]["content"]
        print(f"\n[{elapsed:.2f}s] {reply}\n")
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi HTTP {e.code}: {e.read().decode('utf-8')}\n")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi kết nối: {str(e)}\n")
