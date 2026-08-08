# -*- coding: utf-8 -*-
"""校验 explore-report.json 与截图文件"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
rep = json.load(open(os.path.join(HERE, "explore-report.json"), encoding="utf-8"))
print("模块数:", len(rep))
print()
total_forms = 0
for m in rep:
    shots = [m.get("screenshot", "")] + [f.get("screenshot", "") for f in m.get("forms", [])]
    missing = [s for s in shots if s and not os.path.exists(s)]
    total_forms += len(m.get("forms", []))
    print(f"{m['module']:<16} | 表单{len(m.get('forms', []))} | 截图缺失: {len(missing)}")
    for f in m.get("forms", []):
        fields = "; ".join([x["name"] + ("*" if x.get("required") else "") for x in f.get("fields", [])])
        print(f"    └ {f['name']}: {fields}")
print()
print("总表单数:", total_forms)
# 截图统计
explore_png = [f for f in os.listdir(HERE) if f.startswith("explore-") and f.endswith(".png")]
print("explore-*.png 截图数量:", len(explore_png))
for f in sorted(explore_png):
    print("  ", f)
