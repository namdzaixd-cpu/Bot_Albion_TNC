"""Script gộp test nhanh API + model cho Gemini, Ollama và OpenRouter — chạy: python test_api_key/test_api.py"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request

# Load cấu hình từ bot để lấy key nếu chạy trong dự án
try:
    from core.config import GEMINI_API_KEY, OPENROUTER_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not OPENROUTER_API_KEY:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def choose_model():
    print("=== DANH SÁCH 13 MODEL HỖ TRỢ ===")
    print("[Google Gemini]")
    print("  1. gemini-3.5-flash-lite")
    print("  2. gemini-3.1-flash-lite")
    print("  3. gemma-4-31b-it")
    print("  4. gemini-2.5-flash")
    print("[Ollama]")
    print("  5. minimax-m3")
    print("  6. gpt-oss:120b")
    print("[OpenRouter]")
    print("  7. nvidia/nemotron-3-ultra-550b-a55b:free")
    print("  8. inclusionai/ling-3.0-flash:free")
    print("  9. poolside/laguna-s-2.1:free")
    print("  10. nvidia/nemotron-3-super-120b-a12b:free")
    print("  11. cohere/north-mini-code:free")
    print("  12. poolside/laguna-xs-2.1:free")
    print("  13. openrouter/free")
    
    choice = input("Lựa chọn của bạn (1-13, Mặc định: 1): ").strip()
    
    if choice == "2":
        return "1", "gemini-3.1-flash-lite"
    elif choice == "3":
        return "1", "gemma-4-31b-it"
    elif choice == "4":
        return "1", "gemini-2.5-flash"
    elif choice == "5":
        return "2", "minimax-m3"
    elif choice == "6":
        return "2", "gpt-oss:120b"
    elif choice == "7":
        return "3", "nvidia/nemotron-3-ultra-550b-a55b:free"
    elif choice == "8":
        return "3", "inclusionai/ling-3.0-flash:free"
    elif choice == "9":
        return "3", "poolside/laguna-s-2.1:free"
    elif choice == "10":
        return "3", "nvidia/nemotron-3-super-120b-a12b:free"
    elif choice == "11":
        return "3", "cohere/north-mini-code:free"
    elif choice == "12":
        return "3", "poolside/laguna-xs-2.1:free"
    elif choice == "13":
        return "3", "openrouter/free"
    elif choice == "1" or not choice:
        return "1", "gemini-3.5-flash-lite"
    else:
        # Nếu nhập custom model ngoài danh sách
        print("\nChọn nhà cung cấp cho model custom này:")
        print("1. Google Gemini")
        print("2. Ollama")
        print("3. OpenRouter")
        provider_choice = input("Lựa chọn (1-3, Mặc định: 1): ").strip()
        provider = provider_choice if provider_choice in ("2", "3") else "1"
        return provider, choice

def get_api_setup(provider, model):
    if provider == "1":
        if not GEMINI_API_KEY:
            print("\n❌ [LỖI 1]: Không tìm thấy GEMINI_API_KEY trong file .env.")
            print("👉 Hướng dẫn: Thêm GEMINI_API_KEY vào file .env ở thư mục gốc.\n")
            raise SystemExit(1)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        return url, headers
        
    elif provider == "2":
        ollama_url = "https://ollama.com/api"
        url_clean = ollama_url.rstrip('/')
        url = url_clean if url_clean.endswith("/api/chat") else (f"{url_clean}/chat" if url_clean.endswith("/api") else f"{url_clean}/api/chat")
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        return url, headers
        
    else:
        if not OPENROUTER_API_KEY:
            print("\n❌ [LỖI 1]: Không tìm thấy OPENROUTER_API_KEY trong file .env.")
            print("👉 Hướng dẫn: Thêm OPENROUTER_API_KEY vào file .env ở thư mục gốc.\n")
            raise SystemExit(1)
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        return url, headers

# Bắt đầu thiết lập ban đầu
provider, model = choose_model()
url, headers = get_api_setup(provider, model)

provider_names = {"1": "Gemini", "2": "Ollama", "3": "OpenRouter"}
print(f"\n[{provider_names[provider]}] Đang kết nối tới: {url}")
print(f"[{provider_names[provider]}] Đang sử dụng model: {model}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát), gõ `/model` để đổi model hoặc nhà cung cấp.\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    # Đổi model hoặc provider
    if question.lower() == "/model":
        print()
        provider, model = choose_model()
        url, headers = get_api_setup(provider, model)
        print(f"🔄 Đã chuyển sang: {provider_names[provider]} | Model: {model}\n")
        continue

    # Chuẩn bị payload theo từng bên
    if provider == "1":
        body = json.dumps({"contents": [{"parts": [{"text": question}]}]}).encode("utf-8")
    elif provider == "2":
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": question}], "stream": False}).encode("utf-8")
    else:
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": question}]}).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    start = time.perf_counter()
    
    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ssl_context) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.perf_counter() - start
        
        # Parse kết quả theo từng bên
        if provider == "1":
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
        elif provider == "2":
            reply = result["message"]["content"]
        else:
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
            key_name = "GEMINI_API_KEY" if provider == "1" else ("OLLAMA_API_KEY" if provider == "2" else "OPENROUTER_API_KEY")
            print(f"👉 Hướng dẫn: Vui lòng kiểm tra lại giá trị {key_name} trong file .env!\n")
        elif e.code == 404 and provider == "2":
            print("❌ [LỖI 2]: Model hoặc đường dẫn không tồn tại trên server Ollama (Lỗi 404).")
            print("👉 Hướng dẫn: Hãy kiểm tra xem bạn đã pull model này (`ollama pull <model>`) về máy chưa!\n")
        elif e.code in (400, 404) and provider == "1":
            print("❌ [LỖI 2]: Model không tồn tại hoặc không còn khả dụng trên Google AI Studio (Lỗi 400/404).")
            print("👉 Hướng dẫn: Vui lòng kiểm tra lại tên model Google hỗ trợ hoặc đổi model khác.\n")
        else:
            print("👉 Hướng dẫn: Kiểm tra lại cấu hình, URL hoặc model xem có chính xác không.\n")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n[{elapsed:.2f}s] Lỗi kết nối: {str(e)}\n")
