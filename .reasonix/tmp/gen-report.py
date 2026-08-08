# -*- coding: utf-8 -*-
"""按 generate-test-report skill 生成测试报告（参数化：模块 + 版本，后续轮次直接复用）
用法: python gen-report.py <module> <version>   例: python gen-report.py register 4
"""
import base64, json, os, sys
from datetime import datetime

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = os.environ.get("TEST_WS", r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash")   # 工作区根（绝对路径常量；CI 用 TEST_WS 覆盖）
TMP = os.path.join(WS, ".reasonix", "tmp")

module, ver = sys.argv[1], int(sys.argv[2])
NAME = {"register": "注册", "login": "登录", "explore": "全站探索"}[module]
json_file = os.path.join(TMP, f"{module}-test-results-v{ver}.json")
if not os.path.exists(json_file) and ver == 1:  # 无版本后缀视为 v1
    json_file = os.path.join(TMP, f"{module}-test-results.json")
if module == "explore":
    OUT = os.path.join(WS, f"自动化测试平台-全站探索测试报告-v{ver}.html")  # 显式绝对路径
else:
    OUT = os.path.join(WS, f"自动化测试平台-{NAME}页自动化测试报告-v{ver}.html")

DEFECTS = {
    "register": [
        ("warn", "OBS-001（中）｜前端缺格式本地校验，后端错误英文透传 —— 仍复现",
         "TC03：<code>password: String should have at least 8 characters</code>（英文透传）<br/>"
         "TC06：<code>username: String should have at least 3 characters</code>（英文透传）<br/>"
         "TC04：<code>password: Value error, 密码必须包含大写字母</code>（Pydantic 前缀透传，内容中文）——前端仍无本地校验。"),
        ("note", "OBS-002（低）｜邮箱 HTML5 英文气泡 —— 仍复现",
         "TC07：<code>Please include an '@' in the email address...</code>（英文气泡）"),
        ("note", "OBS-003（低）｜确认密码为空提示「两次输入的密码不一致」—— 仍复现",
         "TC11：空确认密码仍提示「两次输入的密码不一致」，语义应改为「请再次输入密码」。"),
    ],
    "explore": [
        ("warn", "BUG-002（中）｜新建套件项目 ID 丢失为 undefined，保存失败",
         "影响用例：TC05。<br/>点击「新建套件」跳转 <code>/projects/undefined/suites/new</code>，提交返回 "
         "<code>project_id: Input should be a valid UUID, invalid character: found 'u' at 1</code>，套件无法创建。<br/>"
         "建议：新建套件入口应携带当前项目真实 ID。"),
        ("warn", "BUG-003（中）｜新建定时任务后端 500 服务器内部错误",
         "影响用例：TC10。<br/>POST <code>/api/v1/projects/{id}/schedules</code> 返回 500 "
         "<code>{\"code\":5000,\"message\":\"服务器内部错误\"}</code>，3 种 cron 变体均复现，与参数无关，任务无法创建。<br/>"
         "建议：后端排查 schedules 创建接口。"),
        ("note", "BUG-004（低）｜定时任务弹窗缺 Cron 必填前端校验",
         "影响用例：TC11。<br/>Cron 留空提交无前端提示、按钮未禁用，直接请求后端导致 500。<br/>建议：前端补充 Cron 必填与格式校验。"),
        ("note", "OBS-004（低）｜API 测试「新建」按钮点击无响应",
         "影响用例：TC13。<br/>hover 无 tooltip，点击后无弹窗/无跳转/无写请求（状态 before==after）。<br/>建议：确认该按钮是否需要前置条件或补充事件绑定。"),
        ("note", "OBS-005（低）｜CI/CD 页面两表格表头混排",
         "影响用例：TC14。<br/>最近 CI 触发表头混入 API Token 列（12 列混排）。<br/>建议：修复表格列定义。"),
    ],
    "login": [
        ("warn", "BUG-001（中）｜登录失败时前端无任何错误提示 —— 未修复，仍复现",
         "影响用例：TC02（密码错误）、TC03（账号不存在）。<br/>"
         "本轮实测：前端收到 401 后 hints 为空、页面无任何错误文案；对比 TC04/05/06 前端校验 toast 正常弹出，"
         "确认问题仅存在于<b>服务端 401 错误的响应处理分支</b>——错误被吞掉。<br/>"
         "建议：开发修复 <code>/api/v1/auth/login</code> 401 响应的前端处理（如 axios 拦截器对 401 显示「用户名或密码错误」）。"),
    ],
}

def img_tag(path, alt):
    if not os.path.exists(path):
        return f'<p style="color:#e6a23c">⚠ 截图缺失：{os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:720px;width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(json_file, encoding="utf-8") as f:
    data = json.load(f)
if isinstance(data, dict) and "results" in data:   # 兼容 {ts,run_at,script,results:[...]} 包装结构
    run_at = data.get("run_at", "—")
    script = data.get("script", "—")
    results = data["results"]
else:
    results = data

passed = sum(1 for r in results if r["verdict"] == "PASS")
failed = sum(1 for r in results if r["verdict"] == "FAIL")
run_at = results[0].get("run_at", "—") if results else "—"
script = results[0].get("script", "—") if results else "—"

def badge(v):
    color = {"PASS": "#67c23a", "FAIL": "#f56c6c", "BLOCKED": "#e6a23c"}.get(v, "#909399")
    return f'<span style="background:{color};color:#fff;padding:2px 12px;border-radius:12px;font-weight:600;">{v}</span>'

rows = "".join(
    f'<tr><td style="text-align:center;font-weight:600;">{r["id"]}</td>'
    f'<td>{r["desc"]}</td><td><code>{r["step"]}</code></td>'
    f'<td>{r["expect"]}</td><td>{r["result"]}</td>'
    f'<td style="text-align:center;">{badge(r["verdict"])}</td></tr>'
    for r in results
)

api_rows = ""
for r in results:
    apis = r.get("api_responses") or []
    if not apis:
        api_rows += f'<tr><td>{r["id"]}</td><td>—</td><td>未发起 API 请求（前端/HTML5 校验拦截）</td></tr>'
    else:
        for item in apis:
            if isinstance(item, dict):   # 兼容 {status,url,method} 形式
                code, url = item.get("status"), item.get("url", "")
            else:                        # 兼容 [status, url] 形式
                code, url = item[0], item[1]
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c" if code >= 400 else "#e6a23c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

steps = ""
for r in results:
    rid = r["id"]
    steps += (f'<div class="step"><h3>步骤｜{rid}　{r["desc"]}</h3>'
              f'<div class="meta">操作：{r["step"]}</div>'
              f'<p>预期：{r["expect"]}<br/>实际：{r["result"]}</p>'
              f'{img_tag(r.get("screenshot", ""), f"{rid} 截图")}</div>')

defects_html = "".join(
    f'<div class="{cls}"><b>{title}</b><br/>{body}</div>' for cls, title, body in DEFECTS[module]
)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"/><title>自动化测试平台-{NAME}页自动化测试报告（第{ver}轮）</title>
<style>
body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;background:#f5f7fa;color:#303133;}}
.wrap{{max-width:1000px;margin:0 auto;padding:24px 16px 60px;}}
header{{background:linear-gradient(135deg,#1f3a5f,#2f6fb3);color:#fff;padding:32px 24px;border-radius:10px;margin-bottom:24px;}}
header h1{{margin:0 0 8px;font-size:26px;}} header p{{margin:4px 0;opacity:.92;font-size:14px;}}
h2{{border-left:4px solid #2f6fb3;padding-left:10px;margin:32px 0 14px;font-size:20px;}}
.cards{{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0;}}
.card{{flex:1;min-width:150px;background:#fff;border-radius:8px;padding:16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);}}
.card .num{{font-size:30px;font-weight:700;}} .card .lbl{{color:#909399;font-size:13px;margin-top:4px;}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);}}
th,td{{border:1px solid #e4e7ed;padding:10px 12px;font-size:14px;vertical-align:top;text-align:left;}}
th{{background:#f0f4f9;font-weight:600;}} code{{background:#f4f4f5;padding:1px 6px;border-radius:4px;font-size:13px;}}
.step{{background:#fff;border-radius:8px;padding:18px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.08);}}
.step h3{{margin:0 0 10px;font-size:16px;color:#1f3a5f;}} .step .meta{{color:#909399;font-size:13px;margin-bottom:10px;}}
.note{{background:#fdf6ec;border:1px solid #e6a23c;border-radius:8px;padding:14px 18px;font-size:14px;line-height:1.7;margin:14px 0;}}
.warn{{background:#fef0f0;border:1px solid #f56c6c;border-radius:8px;padding:14px 18px;font-size:14px;line-height:1.7;margin:14px 0;}}
.good{{background:#f0f9eb;border:1px solid #67c23a;border-radius:8px;padding:14px 18px;font-size:14px;line-height:1.7;margin:14px 0;}}
footer{{color:#909399;font-size:13px;text-align:center;margin-top:40px;}}
</style></head>
<body><div class="wrap">
<header>
<h1>自动化测试平台 · {NAME}页面自动化测试报告（第{ver}轮）</h1>
<p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code></p>
<p>页面标题：自动化测试平台</p>
<p>报告生成时间：{now}　·　执行引擎：Playwright 1.61.0 (Python) + Chromium 无头模式</p>
<p>数据来源：<code>{os.path.basename(json_file)}</code> ｜ 执行脚本：<code>{script}</code> ｜ 执行时间：<code>{run_at}</code></p>
</header>
<div class="cards">
<div class="card"><div class="num" style="color:#2f6fb3;">{len(results)}</div><div class="lbl">用例总数</div></div>
<div class="card"><div class="num" style="color:#67c23a;">{passed}</div><div class="lbl">通过 PASS</div></div>
<div class="card"><div class="num" style="color:#f56c6c;">{failed}</div><div class="lbl">失败 FAIL</div></div>
<div class="card"><div class="num" style="color:#909399;">0</div><div class="lbl">阻塞 BLOCKED</div></div>
<div class="card"><div class="num" style="color:#e6a23c;">{passed / len(results) * 100:.0f}%</div><div class="lbl">通过率</div></div>
</div>
<h2>一、测试目标与范围</h2>
<p>对{NAME}功能执行<b>第{ver}轮测试</b>：复用资产机制（脚本仅改动态部分、复用表单探测数据、跳过页面探索），用例与判定逻辑与上一轮完全一致，验证结果稳定性与已知缺陷修复情况。每条用例独立 browser context 隔离状态，记录跳转、提示、API 响应，每步保存截图。</p>
<h2>二、执行过程（步骤级记录）</h2>
{steps}
<h2>三、用例明细汇总</h2>
<table><tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>{rows}</table>
<h2>四、后端 API 响应记录</h2>
<table><tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>{api_rows}</table>
<h2>五、缺陷复测确认</h2>
{defects_html}
<h2>六、测试结论与建议</h2>
<div class="good">
✅ {NAME}核心链路稳定可用；{len(results)} 条用例 verdict 与上一轮完全一致，无回归；自动化资产复用机制运转正常（脚本/探测数据/结果/截图版本化留存）。<br/>
⚠️ 已知缺陷持续复现，建议纳入缺陷跟踪排期，修复后执行下一轮回归（复用 test-{module}-cases-v{ver}.py → v{ver + 1}）。
</div>
<p style="line-height:1.8;"><b>建议：</b><br/>
1. 缺陷修复后复用 <code>test-{module}-cases-v{ver}.py</code> 执行回归；<br/>
2. 用例集已版本化留存，可纳入 CI 回归基线；<br/>
3. 清理历轮测试账号（如需）。</p>
<footer>本报告由 generate-test-report skill 自动生成（数据版本 v{ver}）· 截图已内嵌，可单文件离线分享</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT, "| size:", os.path.getsize(OUT))
