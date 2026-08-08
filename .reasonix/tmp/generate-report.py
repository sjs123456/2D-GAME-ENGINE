# -*- coding: utf-8 -*-
"""根据 login-test-results.json 与截图生成自包含 HTML 测试报告"""
import base64
import json
import os
import sys
from datetime import datetime

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TMP)
REPORT = os.path.join(ROOT, "自动化测试平台-登录页自动化测试报告.html")

def img_tag(path, alt, width="720px"):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:{width};width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(os.path.join(TMP, "login-test-results.json"), encoding="utf-8") as f:
    results = json.load(f)

passed = sum(1 for r in results if r["verdict"] == "PASS")
failed = sum(1 for r in results if r["verdict"] == "FAIL")

def verdict_badge(v):
    color = "#67c23a" if v == "PASS" else "#f56c6c"
    return f'<span style="background:{color};color:#fff;padding:2px 12px;border-radius:12px;font-weight:600;">{v}</span>'

rows = ""
for r in results:
    rows += f"""<tr>
<td style="text-align:center;font-weight:600;">{r['id']}</td>
<td>{r['desc']}</td>
<td><code>{r['step']}</code></td>
<td>{r['expect']}</td>
<td>{r['result']}</td>
<td style="text-align:center;">{verdict_badge(r['verdict'])}</td>
</tr>"""

api_rows = ""
for r in results:
    apis = r.get("api_responses") or []
    if not apis:
        api_rows += f"<tr><td>{r['id']}</td><td>—</td><td>未发起 API 请求（前端校验拦截）</td></tr>"
    else:
        for code, url in apis:
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>登录页面自动化测试报告</title>
<style>
  body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 0; background: #f5f7fa; color: #303133; }}
  .wrap {{ max-width: 1000px; margin: 0 auto; padding: 24px 16px 60px; }}
  header {{ background: linear-gradient(135deg,#1f3a5f,#2f6fb3); color: #fff; padding: 32px 24px; border-radius: 10px; margin-bottom: 24px; }}
  header h1 {{ margin: 0 0 8px; font-size: 26px; }}
  header p {{ margin: 4px 0; opacity: .92; font-size: 14px; }}
  h2 {{ border-left: 4px solid #2f6fb3; padding-left: 10px; margin: 32px 0 14px; font-size: 20px; }}
  .cards {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 16px 0; }}
  .card {{ flex: 1; min-width: 150px; background: #fff; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .card .num {{ font-size: 30px; font-weight: 700; }}
  .card .lbl {{ color: #909399; font-size: 13px; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  th, td {{ border: 1px solid #e4e7ed; padding: 10px 12px; font-size: 14px; vertical-align: top; text-align: left; }}
  th {{ background: #f0f4f9; font-weight: 600; }}
  code {{ background: #f4f4f5; padding: 1px 6px; border-radius: 4px; font-size: 13px; }}
  .steps {{ counter-reset: step; }}
  .step {{ background: #fff; border-radius: 8px; padding: 18px; margin: 14px 0; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .step h3 {{ margin: 0 0 10px; font-size: 16px; color: #1f3a5f; }}
  .step .meta {{ color: #909399; font-size: 13px; margin-bottom: 10px; }}
  .step figure {{ margin: 12px 0 0; }}
  .note {{ background: #fdf6ec; border: 1px solid #e6a23c; border-radius: 8px; padding: 14px 18px; font-size: 14px; line-height: 1.7; margin: 14px 0; }}
  .good {{ background: #f0f9eb; border: 1px solid #67c23a; border-radius: 8px; padding: 14px 18px; font-size: 14px; line-height: 1.7; margin: 14px 0; }}
  footer {{ color: #909399; font-size: 13px; text-align: center; margin-top: 40px; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>自动化测试平台 · 登录页面自动化测试报告</h1>
  <p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code></p>
  <p>页面标题：自动化测试平台（已校验一致）</p>
  <p>报告生成时间：{now}　·　执行引擎：Playwright 1.61.0 (Python) + Chromium 无头模式</p>
</header>

<div class="cards">
  <div class="card"><div class="num" style="color:#2f6fb3;">6</div><div class="lbl">用例总数</div></div>
  <div class="card"><div class="num" style="color:#67c23a;">{passed}</div><div class="lbl">通过 PASS</div></div>
  <div class="card"><div class="num" style="color:#f56c6c;">{failed}</div><div class="lbl">失败 FAIL</div></div>
  <div class="card"><div class="num" style="color:#909399;">0</div><div class="lbl">阻塞 BLOCKED</div></div>
  <div class="card"><div class="num" style="color:#e6a23c;">{(passed / len(results) * 100):.0f}%</div><div class="lbl">通过率</div></div>
</div>

<h2>一、测试目标与范围</h2>
<p>针对登录页面进行功能验证，覆盖正常登录、错误凭据、空值校验三类场景，共 6 条用例。每条用例使用独立浏览器上下文（隔离登录态），记录跳转结果、页面提示、后端 API 响应，并为每一步操作保存截图。</p>

<h2>二、执行过程（步骤级记录）</h2>
<div class="steps">
  <div class="step">
    <h3>步骤 1｜打开登录页并验证页面标题</h3>
    <div class="meta">操作：goto http://123.56.21.178:8080/login → 读取 &lt;title&gt; → 断言与期望一致</div>
    <p>实际标题：<b>自动化测试平台</b>，与期望完全一致，页面正常加载（无超时/拦截）。</p>
    {img_tag(os.path.join(TMP, "login-page-title-check.png"), "步骤1截图：登录页（标题验证通过）")}
  </div>
  <div class="step">
    <h3>步骤 2｜TC01 登录成功（admin123 / Admin123）</h3>
    <div class="meta">操作：输入账号 → 输入密码 → 点击「登 录」按钮 → 等待跳转</div>
    <p>结果：跳转到 <code>/dashboard</code>，出现 toast「登录成功」，右上角显示当前用户 <b>admin123</b>，登录接口与统计数据接口均返回 200。✅ PASS</p>
    {img_tag(r["screenshot"] if (r := [x for x in results if x["id"] == "TC01"][0]) else "", "步骤2截图：TC01 登录成功，已进入仪表盘")}
  </div>
  <div class="step">
    <h3>步骤 3｜TC02 密码错误（admin123 / Admin1234）</h3>
    <div class="meta">操作：输入错误密码 → 点击登录 → 等待 2s 捕获提示</div>
    <p>结果：未跳转（仍 <code>/login</code>），后端返回 401，但前端<b style="color:#f56c6c;">未显示任何错误提示</b>。❌ FAIL</p>
    {img_tag(os.path.join(TMP, "login-TC02.png"), "步骤3截图：TC02 密码错误，页面无错误提示")}
  </div>
  <div class="step">
    <h3>步骤 4｜TC03 账号不存在（nosuchuser888 / Admin123）</h3>
    <div class="meta">操作：输入不存在账号 → 点击登录 → 等待 2s 捕获提示</div>
    <p>结果：未跳转（仍 <code>/login</code>），后端返回 401，前端<b style="color:#f56c6c;">未显示任何错误提示</b>（与 TC02 文案一致，符合防枚举设计，但前端缺陷相同）。❌ FAIL</p>
    {img_tag(os.path.join(TMP, "login-TC03.png"), "步骤4截图：TC03 账号不存在，页面无错误提示")}
  </div>
  <div class="step">
    <h3>步骤 5｜TC04 账号为空（密码 Admin123）</h3>
    <div class="meta">操作：账号留空 → 点击登录</div>
    <p>结果：未跳转，前端 toast「请输入用户名」，未发起 API 请求。✅ PASS</p>
    {img_tag(os.path.join(TMP, "login-TC04.png"), "步骤5截图：TC04 账号为空，提示「请输入用户名」")}
  </div>
  <div class="step">
    <h3>步骤 6｜TC05 密码为空（账号 admin123）</h3>
    <div class="meta">操作：密码留空 → 点击登录</div>
    <p>结果：未跳转，前端 toast「请输入密码」，未发起 API 请求。✅ PASS</p>
    {img_tag(os.path.join(TMP, "login-TC05.png"), "步骤6截图：TC05 密码为空，提示「请输入密码」")}
  </div>
  <div class="step">
    <h3>步骤 7｜TC06 账号密码均为空</h3>
    <div class="meta">操作：直接点击登录</div>
    <p>结果：未跳转，前端 toast「请输入用户名」（优先校验用户名），未发起 API 请求。✅ PASS</p>
    {img_tag(os.path.join(TMP, "login-TC06.png"), "步骤7截图：TC06 均为空，提示「请输入用户名」")}
  </div>
</div>

<h2>三、用例明细汇总</h2>
<table>
  <tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>
  {rows}
</table>

<h2>四、后端 API 响应记录</h2>
<table>
  <tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>
  {api_rows}
</table>

<h2>五、缺陷报告</h2>
<div class="note">
  <b>BUG-001（中）｜登录失败时前端无任何错误提示</b><br/>
  影响用例：TC02（密码错误）、TC03（账号不存在）。<br/>
  复现步骤：输入错误密码或不存在账号，点击登录。<br/>
  实际：后端正确返回 401（未授权），但前端未渲染任何 toast / alert / 行内提示，页面无任何变化，用户无法得知登录失败及原因。<br/>
  预期：页面应提示如「账号或密码错误」的明确错误信息。<br/>
  定位建议：检查登录接口 401 响应在前端拦截器（如 axios 响应拦截 / el-message）中的处理分支。
</div>

<h2>六、测试结论与建议</h2>
<div class="good">
  ✅ 核心登录链路可用：有效凭据可正常登录并跳转仪表盘；空值校验由前端拦截，提示文案正确。<br/>
  ❌ 存在 1 个前端缺陷（登录失败无提示），导致 2 条用例 FAIL，需修复后回归。
</div>
<p style="line-height:1.8;">
  <b>建议：</b><br/>
  1. 开发修复 401 错误提示不显示的问题（BUG-001），修复后重跑 TC02/TC03 回归；<br/>
  2. 补充自动化回归：将本报告用例集纳入 CI，登录页每次变更自动回归；<br/>
  3. 建议补充用例：记住我勾选后登录态保持、注册流程、密码框字符遮盖校验、接口层 401 语义与防枚举一致性验证。
</p>

<footer>本报告由 web-automation skill（Playwright Python）自动生成 · 截图已内嵌，可单文件离线分享</footer>
</div>
</body>
</html>"""

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK: {REPORT}")
print(f"size: {os.path.getsize(REPORT)} bytes")
