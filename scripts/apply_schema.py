"""Apply schema_v2.sql lên Supabase thật qua Management API. Chạy từng statement."""
import json, urllib.request, os, re, sys

TOK = os.getenv("SUPABASE_ACCESS_TOKEN", "")
REF = "jbfqniokcluggcolwgut"
URL = f"https://api.supabase.com/v1/projects/{REF}/database/query"

sql = open("scripts/schema_v2.sql", encoding="utf-8").read()
# Tách statement theo ; nhưng bỏ qua ; trong string/comment đơn giản
statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

def run(stmt):
    # bỏ comment dòng
    lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
    q = "\n".join(lines).strip()
    if not q:
        return None
    body = json.dumps({"query": q}).encode()
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {TOK}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTPERR {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return f"ERR {e}"

ok, fail = 0, 0
for i, st in enumerate(statements, 1):
    # rút gọn preview
    prev = st[:60].replace("\n", " ")
    res = run(st)
    if res is None:
        continue
    if res.startswith("HTTPERR") or res.startswith("ERR"):
        print(f"[FAIL {i}] {prev}... -> {res}")
        fail += 1
    else:
        ok += 1
        if i % 5 == 0:
            print(f"[ok {i}] {prev}...")
print(f"\n=== DONE: {ok} ok, {fail} fail ===")
sys.exit(1 if fail else 0)
