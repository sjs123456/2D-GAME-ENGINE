# -*- coding: utf-8 -*-
"""校验最终 JSON 字段完整性与 verdict 汇总"""
import json, io

d = json.load(io.open(".reasonix/tmp/explore-test-results.json", encoding="utf-8"))
req = ["id", "desc", "step", "expect", "result", "url", "title", "verdict",
       "screenshot", "api_responses", "hints", "dialogs", "body_excerpt", "script", "run_at"]
print("顶层字段:", sorted(d.keys()))
print("用例数:", len(d["results"]))
all_ok = True
from collections import Counter
cnt = Counter()
for r in d["results"]:
    missing = [k for k in req if k not in r]
    if missing:
        all_ok = False
        print("字段缺失:", r["id"], missing)
    cnt[r["verdict"]] += 1
print("字段完整性:", "OK" if all_ok else "缺失")
print("verdict 分布:", dict(cnt))
print("script 唯一:", set(r["script"] for r in d["results"]))
print("run_at 唯一:", set(r["run_at"] for r in d["results"]))
print()
print("=== verdict 汇总 ===")
for r in d["results"]:
    print(f"{r['id']} | {r['verdict']:7s} | {r['desc']}")
