import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("bot/.env")
key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {key[:5]}... (length: {len(key)})")
genai.configure(api_key=key)
try:
    for m in genai.list_models():
        print(m.name)
except Exception as e:
    print("Error:", repr(e))
