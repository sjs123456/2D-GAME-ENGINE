# -*- coding: utf-8 -*-
"""给 register-test-results-v3.json 追加 script / run_at 追溯字段（不覆盖历史，直接就地更新 v3）"""
import io, json, time, os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(OUT_DIR, "register-test-results-v3.json")

with io.open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

run_at = time.strftime("%Y-%m-%d %H:%M:%S")
for rec in data:
    rec["script"] = "test-register-cases-v3.py"
    rec["run_at"] = run_at

with io.open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("已追加追溯字段, run_at =", run_at)
print("记录数:", len(data))
for r in data:
    print(f"  {r['id']}: script={r.get('script')} run_at={r.get('run_at')} verdict={r['verdict']}")
