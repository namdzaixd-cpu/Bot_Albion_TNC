import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging to see everything
logging.basicConfig(level=logging.INFO)

from bot.core.db import safe_select, get_client

client = get_client()
if client is None:
    print("Client is None")
else:
    print("Client successfully initialized")
    
    # Try safe_select on a nonexistent file
    data, err = safe_select("json_storage", columns="data", filters={"file_name": "nonexistent_file.json"}, single=True)
    print("Result of safe_select:", data, err)
