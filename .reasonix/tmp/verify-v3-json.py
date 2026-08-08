# -*- coding: utf-8 -*-
import io, json
with io.open("register-test-results-v3.json", encoding="utf-8") as f:
    data = json.load(f)
print("记录数:", len(data))
for r in data:
    print(f"{r['id']}: verdict={r['verdict']} | {r['result'][:80]}")
    assert r.get("script") == "test-register-cases-v3.py", r["id"]
    assert r.get("run_at"), r["id"]
print("\n全部记录含 script/run_at 字段: OK")
