"""Script test API + model OpenRouter, KHÔNG có system instruction — chạy: python bot/test_openrouter.py"""
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

# Thêm đường dẫn để import được core.config khi chạy từ thư mục khác
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot"))

# Load cấu hình từ bot
from core.config import OPENROUTER_API_KEY

API_KEY = OPENROUTER_API_KEY
URL = "https://openrouter.ai/api/v1/chat/completions"

if not API_KEY:
    print("\n❌ [LỖI 1]: Không tìm thấy OPENROUTER_API_KEY trong file .env.")
    print("👉 Hướng dẫn: Sao chép file .env.example thành .env ở thư mục gốc và điền giá trị cho OPENROUTER_API_KEY.\n")
    raise SystemExit(1)

def choose_model():
    print("Chọn model OpenRouter:")
    print("1. nvidia/nemotron-3-ultra-550b-a55b:free")
    print("2. inclusionai/ling-3.0-flash:free")
    print("3. poolside/laguna-s-2.1:free")
    print("4. nvidia/nemotron-3-super-120b-a12b:free")
    print("5. cohere/north-mini-code:free")
    print("6. poolside/laguna-xs-2.1:free")
    print("7. openrouter/free")
    model_choice = input("Lựa chọn (1-7, Mặc định: 1): ").strip()
    
    if model_choice == "2":
        return "inclusionai/ling-3.0-flash:free"
    elif model_choice == "3":
        return "poolside/laguna-s-2.1:free"
    elif model_choice == "4":
        return "nvidia/nemotron-3-super-120b-a12b:free"
    elif model_choice == "5":
        return "cohere/north-mini-code:free"
    elif model_choice == "6":
        return "poolside/laguna-xs-2.1:free"
    elif model_choice == "7":
        return "openrouter/free"
    elif model_choice == "1" or not model_choice:
        return "nvidia/nemotron-3-ultra-550b-a55b:free"
    else:
        return model_choice

# Khởi tạo model lần đầu
model = choose_model()

print(f"\n[OpenRouter] Đang sử dụng model: {model}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát):\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    # Nhận diện lệnh đổi model
    if question.lower() == "/model":
        print()
        model = choose_model()
        print(f"🔄 Đã chuyển sang model: {model}\n")
        continue

    body = json.dumps({
        "model": model,
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
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ssl_context) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - start
        reply = result["choices"][0]["message"]["content"]
        print(f"\n[{elapsed:.2f}s] {reply}\n")
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        error_content = e.read().decode('utf-8')
        print(f"\n[{elapsed:.2f}s] Lỗi HTTP {e.code}: {error_content}")
        if e.code == 429:
            print("❌ [LỖI 2]: Đã chạm giới hạn request/ngày hoặc tần suất của API (Rate Limit / Quota Exceeded).")
            print("👉 Hướng dẫn: API Key này đã hết lượt dùng hôm nay. Vui lòng đổi sang API Key khác trong file .env!\n")
        elif e.code in (401, 403):
            print("❌ [LỖI 1/2]: API Key không hợp lệ hoặc không có quyền truy cập.")
            print("👉 Hướng dẫn: Vui lòng kiểm tra lại giá trị OPENROUTER_API_KEY trong file .env!\n")
        else:
            print("👉 Hướng dẫn: Kiểm tra lại cấu hình hoặc tên model xem có chính xác không.\n")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi kết nối: {str(e)}\n")
