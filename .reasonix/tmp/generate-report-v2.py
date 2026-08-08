# -*- coding: utf-8 -*-
"""按 generate-test-report skill 生成 HTML 测试报告（v2 验证版）"""
import base64, json, os, sys
from datetime import datetime

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash"   # 工作区根（绝对路径常量）
TMP = os.path.join(WS, ".reasonix", "tmp")
OUT = os.path.join(WS, "自动化测试平台-登录页自动化测试报告-v2.html")  # 显式绝对路径

def img_tag(path, alt):
    """base64 内嵌截图；文件缺失时返回占位提示"""
    if not os.path.exists(path):
        return f'<p style="color:#e6a23c">⚠ 截图缺失：{os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:720px;width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(os.path.join(TMP, "login-test-results.json"), encoding="utf-8") as f:
    results = json.load(f)

passed = sum(1 for r in results if r["verdict"] == "PASS")
failed = sum(1 for r in results if r["verdict"] == "FAIL")

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
        api_rows += f'<tr><td>{r["id"]}</td><td>—</td><td>未发起 API 请求（前端校验拦截）</td></tr>'
    else:
        for code, url in apis:
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

steps = ""
step_meta = {
    "TC01": ("步骤 2｜TC01 登录成功（admin123 / Admin123）", "输入账号 → 输入密码 → 点击「登 录」→ 等待跳转",
             "跳转到 <code>/dashboard</code>，toast「登录成功」，用户 admin123，接口均 200。✅ PASS"),
    "TC02": ("步骤 3｜TC02 密码错误（admin123 / Admin1234）", "输入错误密码 → 点击登录 → 等待 2s 捕获提示",
             "未跳转（仍 /login），后端 401，前端<b style='color:#f56c6c'>未显示任何错误提示</b>。❌ FAIL"),
    "TC03": ("步骤 4｜TC03 账号不存在（nosuchuser888 / Admin123）", "输入不存在账号 → 点击登录 → 等待 2s 捕获提示",
             "未跳转（仍 /login），后端 401，前端<b style='color:#f56c6c'>未显示任何错误提示</b>。❌ FAIL"),
    "TC04": ("步骤 5｜TC04 账号为空（密码 Admin123）", "账号留空 → 点击登录",
             "未跳转，前端 toast「请输入用户名」，未发起 API 请求。✅ PASS"),
    "TC05": ("步骤 6｜TC05 密码为空（账号 admin123）", "密码留空 → 点击登录",
             "未跳转，前端 toast「请输入密码」，未发起 API 请求。✅ PASS"),
    "TC06": ("步骤 7｜TC06 账号密码均为空", "直接点击登录",
             "未跳转，前端 toast「请输入用户名」（优先校验用户名）。✅ PASS"),
}
for r in results:
    rid = r["id"]
    title, meta, desc = step_meta.get(rid, (f"步骤｜{rid}", r["step"], r["result"]))
    steps += (f'<div class="step"><h3>{title}</h3><div class="meta">操作：{meta}</div>'
              f'<p>{desc}</p>{img_tag(r.get("screenshot", ""), f"{rid} 截图")}</div>')

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"/><title>登录页面自动化测试报告 v2</title>
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
.good{{background:#f0f9eb;border:1px solid #67c23a;border-radius:8px;padding:14px 18px;font-size:14px;line-height:1.7;margin:14px 0;}}
footer{{color:#909399;font-size:13px;text-align:center;margin-top:40px;}}
</style></head>
<body><div class="wrap">
<header>
<h1>自动化测试平台 · 登录页面自动化测试报告 v2</h1>
<p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code></p>
<p>页面标题：自动化测试平台（已校验一致）</p>
<p>报告生成时间：{now}　·　执行引擎：Playwright 1.61.0 (Python) + Chromium 无头模式</p>
</header>
<div class="cards">
<div class="card"><div class="num" style="color:#2f6fb3;">{len(results)}</div><div class="lbl">用例总数</div></div>
<div class="card"><div class="num" style="color:#67c23a;">{passed}</div><div class="lbl">通过 PASS</div></div>
<div class="card"><div class="num" style="color:#f56c6c;">{failed}</div><div class="lbl">失败 FAIL</div></div>
<div class="card"><div class="num" style="color:#909399;">0</div><div class="lbl">阻塞 BLOCKED</div></div>
<div class="card"><div class="num" style="color:#e6a23c;">{passed / len(results) * 100:.0f}%</div><div class="lbl">通过率</div></div>
</div>
<h2>一、测试目标与范围</h2>
<p>针对登录页面进行功能验证，覆盖正常登录、错误凭据、空值校验三类场景，共 {len(results)} 条用例。每条用例使用独立浏览器上下文隔离登录态，记录跳转结果、页面提示、后端 API 响应，并为每一步操作保存截图。</p>
<h2>二、执行过程（步骤级记录）</h2>
<div class="step">
<h3>步骤 1｜打开登录页并验证页面标题</h3>
<div class="meta">操作：goto http://123.56.21.178:8080/login → 读取 &lt;title&gt; → 断言</div>
<p>实际标题：<b>自动化测试平台</b>，与期望完全一致，页面正常加载。</p>
{img_tag(os.path.join(TMP, "login-page-title-check.png"), "步骤1截图：登录页（标题验证通过）")}
</div>
{steps}
<h2>三、用例明细汇总</h2>
<table><tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>{rows}</table>
<h2>四、后端 API 响应记录</h2>
<table><tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>{api_rows}</table>
<h2>五、缺陷报告</h2>
<div class="note"><b>BUG-001（中）｜登录失败时前端无任何错误提示</b><br/>
影响用例：TC02（密码错误）、TC03（账号不存在）。<br/>
复现步骤：输入错误密码或不存在账号，点击登录。<br/>
实际：后端正确返回 401，但前端未渲染任何 toast / alert / 行内提示，用户无法得知登录失败及原因。<br/>
预期：页面应提示如「账号或密码错误」的明确错误信息。<br/>
定位建议：检查登录接口 401 响应在前端拦截器（axios 响应拦截 / el-message）中的处理分支。</div>
<h2>六、测试结论与建议</h2>
<div class="good">✅ 核心登录链路可用：有效凭据正常登录并跳转仪表盘；空值校验前端拦截、提示正确。<br/>
❌ 存在 1 个前端缺陷（登录失败无提示），导致 2 条用例 FAIL，需修复后回归。</div>
<p style="line-height:1.8;"><b>建议：</b><br/>
1. 修复 401 错误提示不显示问题（BUG-001），修复后重跑 TC02/TC03 回归；<br/>
2. 用例集纳入 CI 自动化回归；<br/>
3. 补充用例：记住我登录态保持、注册流程、接口层 401 防枚举一致性。</p>
<footer>本报告由 generate-test-report skill 自动生成 · 截图已内嵌，可单文件离线分享</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT, "| size:", os.path.getsize(OUT))
