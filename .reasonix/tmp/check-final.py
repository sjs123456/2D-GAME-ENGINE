# -*- coding: utf-8 -*-
import json, io, os
d = json.load(io.open(".reasonix/tmp/explore-test-results.json", encoding="utf-8"))
print("ts:", d["ts"], "run_at:", d["run_at"], "script:", d["script"])
print("用例数:", len(d["results"]))
print()
for r in d["results"]:
    print("=====", r["id"], r["verdict"], "=====")
    print("desc:", r["desc"])
    print("result:", r["result"])
    print("url:", r["url"])
    print("screenshot:", r["screenshot"])
    for h in r["hints"]:
        print("  hint:", h[:150])
    print()
    # 截图存在性
    if r["screenshot"]:
        print("  截图存在:", os.path.exists(r["screenshot"]))
print()
print("=== 截图文件清单 ===")
for f in sorted(os.listdir(".reasonix/tmp")):
    if f.startswith("explore-TC") or f == "explore-test-results.json":
        print(" ", f, os.path.getsize(os.path.join(".reasonix/tmp", f)))
