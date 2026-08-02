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

def choose_provider():
    print("=== CHỌN NHÀ CUNG CẤP AI ===")
    print("1. Google Gemini (Gọi trực tiếp AI Studio)")
    print("2. Ollama (Cấu hình cứng URL https://ollama.com/api)")
    print("3. OpenRouter")
    choice = input("Lựa chọn (1-3, Mặc định: 1): ").strip()
    if choice in ("2", "3"):
        return choice
    return "1"

def choose_model(provider):
    if provider == "1":
        print("\nChọn model Gemini:")
        print("1. gemini-3.5-flash-lite")
        print("2. gemini-3.1-flash-lite")
        print("3. gemma-4-31b-it")
        print("4. gemini-2.5-flash")
        choice = input("Lựa chọn (1-4, Mặc định: 1): ").strip()
        if choice == "2": return "gemini-3.1-flash-lite"
        elif choice == "3": return "gemma-4-31b-it"
        elif choice == "4": return "gemini-2.5-flash"
        return "gemini-3.5-flash-lite"
        
    elif provider == "2":
        print("\nChọn model Ollama:")
        print("1. minimax-m3")
        print("2. gpt-oss:120b")
        choice = input("Lựa chọn (1 hoặc 2, Mặc định: 1): ").strip()
        if choice == "2": return "gpt-oss:120b"
        return "minimax-m3"
        
    else:
        print("\nChọn model OpenRouter:")
        print("1. nvidia/nemotron-3-ultra-550b-a55b:free")
        print("2. inclusionai/ling-3.0-flash:free")
        print("3. poolside/laguna-s-2.1:free")
        print("4. nvidia/nemotron-3-super-120b-a12b:free")
        print("5. cohere/north-mini-code:free")
        print("6. poolside/laguna-xs-2.1:free")
        print("7. openrouter/free")
        choice = input("Lựa chọn (1-7, Mặc định: 1): ").strip()
        if choice == "2": return "inclusionai/ling-3.0-flash:free"
        elif choice == "3": return "poolside/laguna-s-2.1:free"
        elif choice == "4": return "nvidia/nemotron-3-super-120b-a12b:free"
        elif choice == "5": return "cohere/north-mini-code:free"
        elif choice == "6": return "poolside/laguna-xs-2.1:free"
        elif choice == "7": return "openrouter/free"
        return "nvidia/nemotron-3-ultra-550b-a55b:free"

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
provider = choose_provider()
model = choose_model(provider)
url, headers = get_api_setup(provider, model)

provider_names = {"1": "Gemini", "2": "Ollama", "3": "OpenRouter"}
print(f"\n[{provider_names[provider]}] Đang kết nối tới: {url}")
print(f"[{provider_names[provider]}] Đang sử dụng model: {model}")
print("Gõ câu hỏi rồi Enter (Ctrl+C để thoát), gõ `/model` để đổi model, gõ `/provider` để đổi nhà cung cấp.\n")

while True:
    question = input("> ").strip()
    if not question:
        continue

    # Đổi model của nhà cung cấp hiện tại
    if question.lower() == "/model":
        model = choose_model(provider)
        url, headers = get_api_setup(provider, model)
        print(f"🔄 Đã chuyển sang model: {model}\n")
        continue

    # Đổi nhà cung cấp khác
    if question.lower() == "/provider":
        print()
        provider = choose_provider()
        model = choose_model(provider)
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
