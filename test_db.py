import os
import sys
sys.path.append(os.path.abspath('bot'))
from core.config import SUPABASE_URL, SUPABASE_KEY, GUILD_ID
from supabase import create_client

print(f'URL: {SUPABASE_URL}')
print(f'KEY: {SUPABASE_KEY[:10]}...')
client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = client.table('guild_config').upsert({'guild_id': str(GUILD_ID)}).execute()
    print('Upsert guild:', res)
except Exception as e:
    print('Error upsert guild:', e)
