# -*- coding: utf-8 -*-
import json, io
d = json.load(io.open(".reasonix/tmp/explore-test-results-part2.json", encoding="utf-8"))
for r in d["results"]:
    print("=====", r["id"], r["verdict"], "=====")
    print("result:", r["result"])
    print("hints:")
    for h in r["hints"]:
        print("  -", h)
    print("url:", r["url"])
    print("POST/PUT/DELETE api:")
    for a in r["api_responses"]:
        if a["method"] in ("POST", "PUT", "DELETE"):
            print("  ", a["method"], a["status"], a["url"][-80:])
    print()
