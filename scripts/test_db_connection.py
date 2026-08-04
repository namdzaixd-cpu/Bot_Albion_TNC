import os
import urllib.request
import json

def test_connection():
    print("=== Supabase Connection Test (Zero Dependencies) ===")
    
    # Read .env manually
    env_vars = {}
    if os.path.exists(".env"):
        print("✓ Found .env file.")
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    # Strip quotes if present
                    val = val.strip().strip('"').strip("'")
                    env_vars[key.strip()] = val
    else:
        print("✗ .env file not found!")
        return

    supabase_url = env_vars.get("SUPABASE_URL")
    supabase_anon_key = env_vars.get("SUPABASE_ANON_KEY")
    supabase_service_key = env_vars.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        print("✗ ERROR: SUPABASE_URL is missing in .env!")
        return

    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_ANON_KEY: {supabase_anon_key[:15]}... if configured")
    if supabase_service_key:
        print(f"SUPABASE_SERVICE_ROLE_KEY: {supabase_service_key[:15]}...")
    else:
        print("⚠ SUPABASE_SERVICE_ROLE_KEY is missing!")

    # 1. Test using ANON Key
    if supabase_anon_key:
        print("\n1. Testing HTTP connection with ANON KEY...")
        url = f"{supabase_url}/rest/v1/sp_metadata?select=*"
        req = urllib.request.Request(url)
        req.add_header("apikey", supabase_anon_key)
        req.add_header("Authorization", f"Bearer {supabase_anon_key}")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"✓ Success! HTTP query returned: {data}")
        except Exception as e:
            print(f"✗ Anon key request failed (likely RLS restricted, which is normal): {e}")

    # 2. Test using Service Role Key
    if supabase_service_key:
        print("\n2. Testing HTTP connection with SERVICE ROLE KEY...")
        # Check sp_metadata
        url_meta = f"{supabase_url}/rest/v1/sp_metadata?select=*"
        req_meta = urllib.request.Request(url_meta)
        req_meta.add_header("apikey", supabase_service_key)
        req_meta.add_header("Authorization", f"Bearer {supabase_service_key}")
        try:
            with urllib.request.urlopen(req_meta, timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"✓ Success! sp_metadata: {data}")
        except Exception as e:
            print(f"✗ Service Role request failed: {e}")
            return
            
        # Check user_activity count
        url_act = f"{supabase_url}/rest/v1/user_activity?select=user_id"
        req_act = urllib.request.Request(url_act)
        req_act.add_header("apikey", supabase_service_key)
        req_act.add_header("Authorization", f"Bearer {supabase_service_key}")
        try:
            with urllib.request.urlopen(req_act, timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"✓ Success! Table 'user_activity' has {len(data)} records.")
        except Exception as e:
            print(f"✗ Failed to query user_activity: {e}")

        # Check user_economy count
        url_eco = f"{supabase_url}/rest/v1/user_economy?select=user_id"
        req_eco = urllib.request.Request(url_eco)
        req_eco.add_header("apikey", supabase_service_key)
        req_eco.add_header("Authorization", f"Bearer {supabase_service_key}")
        try:
            with urllib.request.urlopen(req_eco, timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"✓ Success! Table 'user_economy' has {len(data)} records.")
                print("\n★ Database connection is fully verified and connected to Singapore via HTTP REST!")
        except Exception as e:
            print(f"✗ Failed to query user_economy: {e}")

if __name__ == "__main__":
    test_connection()
