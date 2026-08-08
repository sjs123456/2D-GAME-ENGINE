# -*- coding: utf-8 -*-
"""基于复测证据修正 part2 JSON 中 TC09/TC10 的记录（保持 ts 全局一致，不重复创建数据）"""
import json, io

path = ".reasonix/tmp/explore-test-results-part2.json"
d = json.load(io.open(path, encoding="utf-8"))
ts = io.open(".reasonix/tmp/explore-ts.txt", encoding="utf-8").read().strip()
KW = f"kw_{ts}"

for r in d["results"]:
    if r["id"] == "TC09":
        r["verdict"] = "PASS"
        r["result"] = f"toast=['关键字创建成功']；关键字卡片含kw=True（{KW} 显示于 .keyword-card） ；代码展示=True（def {KW}(): return 'ok'）"
        r["hints"].append("修正依据：复测确认关键字列表为 .keyword-card 卡片结构（非 el-table），kw_ts 与 Python 代码均在卡片中展示；POST /keywords 201")
    if r["id"] == "TC10":
        r["verdict"] = "FAIL"
        r["result"] = "缺陷复现：新建定时任务 POST /api/v1/projects/.../schedules 返回 500（服务器内部错误）；toast=['服务器内部错误','操作失败']；任务未创建，弹窗不关闭"
        r["hints"].insert(0, "缺陷：新建定时任务返回 500 服务器内部错误")
        r["hints"].append("修正依据：复测 3 种 cron 变体（*/5 * * * *、0 0 * * 1、30 8 * * *）全部返回 500，与参数无关，后端缺陷稳定复现")

with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("part2 JSON 已修正")
