# -*- coding: utf-8 -*-
"""修正最终 JSON：TC11（前端 Cron 必填校验缺失 + 后端 500）、TC13（OBS 候选确认）"""
import json, io

path = ".reasonix/tmp/explore-test-results.json"
d = json.load(io.open(path, encoding="utf-8"))

for r in d["results"]:
    if r["id"] == "TC11":
        r["verdict"] = "FAIL"
        r["result"] = "前端未出现 Cron 必填校验提示（校验提示=[]）、按钮未禁用，点击「确认创建」直接提交后端，返回 500（服务器内部错误）；弹窗不关闭、未创建任务（间接达成）"
        r["hints"].insert(0, "缺陷：定时任务弹窗缺少 Cron 表达式前端必填校验（未出现「请输入 Cron 表达式」提示、按钮未禁用），点击后直接提交触发后端 500（与 TC10 同一后端缺陷）")
    if r["id"] == "TC13":
        r["verdict"] = "FAIL"
        r["result"] = "精确复核：点击「新建」后 2s，无弹窗、无新建表单、无 drawer、URL 未变、无 POST/PUT/DELETE 请求，页面状态完全无变化 → 确认异常"
        r["hints"].insert(0, "OBS 候选确认：API 测试页「新建」按钮点击无响应（精确状态对比：before==after，无弹窗/无跳转/无写请求）")
        r["hints"].append("复核截图 recheck-TC13.png")

with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("最终 JSON 已修正")
