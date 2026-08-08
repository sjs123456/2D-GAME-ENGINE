# -*- coding: utf-8 -*-
"""按 generate-test-report skill 生成登录功能第二轮测试报告（v2）"""
import base64, json, os, sys
from datetime import datetime

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash"   # 工作区根（绝对路径常量）
TMP = os.path.join(WS, ".reasonix", "tmp")
OUT = os.path.join(WS, "自动化测试平台-登录页自动化测试报告-v2.html")  # 显式绝对路径

def img_tag(path, alt):
    if not os.path.exists(path):
        return f'<p style="color:#e6a23c">⚠ 截图缺失：{os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:720px;width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(os.path.join(TMP, "login-test-results-v2.json"), encoding="utf-8") as f:
    results = json.load(f)

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
        api_rows += f'<tr><td>{r["id"]}</td><td>—</td><td>未发起 API 请求（前端校验拦截）</td></tr>'
    else:
        for code, url in apis:
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c" if code >= 400 else "#e6a23c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

step_titles = {
    "TC01": "步骤 2｜TC01 登录成功（admin123 / Admin123）",
    "TC02": "步骤 3｜TC02 密码错误（admin123 / Admin1234）",
    "TC03": "步骤 4｜TC03 账号不存在（nosuchuser888 / Admin123）",
    "TC04": "步骤 5｜TC04 账号为空（密码 Admin123）",
    "TC05": "步骤 6｜TC05 密码为空（账号 admin123）",
    "TC06": "步骤 7｜TC06 账号密码均为空",
}
steps = ""
for r in results:
    rid = r["id"]
    steps += (f'<div class="step"><h3>{step_titles.get(rid, f"步骤｜{rid}")}</h3>'
              f'<div class="meta">操作：{r["step"]}</div>'
              f'<p>预期：{r["expect"]}<br/>实际：{r["result"]}</p>'
              f'{img_tag(r.get("screenshot", ""), f"{rid} 截图")}</div>')

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"/><title>自动化测试平台-登录页自动化测试报告（第二轮）</title>
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
<h1>自动化测试平台 · 登录页面自动化测试报告（第二轮）</h1>
<p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code></p>
<p>页面标题：自动化测试平台</p>
<p>报告生成时间：{now}　·　执行引擎：Playwright 1.61.0 (Python) + Chromium 无头模式</p>
<p>数据来源：<code>login-test-results-v2.json</code> ｜ 执行脚本：<code>{script}</code> ｜ 执行时间：<code>{run_at}</code></p>
</header>
<div class="cards">
<div class="card"><div class="num" style="color:#2f6fb3;">{len(results)}</div><div class="lbl">用例总数</div></div>
<div class="card"><div class="num" style="color:#67c23a;">{passed}</div><div class="lbl">通过 PASS</div></div>
<div class="card"><div class="num" style="color:#f56c6c;">{failed}</div><div class="lbl">失败 FAIL</div></div>
<div class="card"><div class="num" style="color:#909399;">0</div><div class="lbl">阻塞 BLOCKED</div></div>
<div class="card"><div class="num" style="color:#e6a23c;">{passed / len(results) * 100:.0f}%</div><div class="lbl">通过率</div></div>
</div>
<h2>一、测试目标与范围</h2>
<p>对登录功能执行<b>第二轮测试（回归）</b>：复用首轮脚本 `test-login-cases.py`（仅改输出版本号），用例输入与判定逻辑完全一致，验证结果稳定性，并重点确认首轮缺陷 <b>BUG-001（登录失败前端无错误提示）</b> 是否修复。每条用例独立 browser context 隔离登录态，记录跳转、提示、API 响应，每步保存截图。</p>
<h2>二、资产复用情况</h2>
<table>
<tr><th>复用资产</th><th>处置</th></tr>
<tr><td><code>test-login-cases.py</code>（v1）</td><td>复制为 <code>test-login-cases-v2.py</code>，仅改动态部分（JSON/截图版本号、追加 script/run_at 字段），用例逻辑 0 处改动</td></tr>
<tr><td>页面选择器</td><td>复用 <code>input.form-input</code> / <code>button.submit-btn</code> / <code>.el-message</code>，未重新探索页面，全部有效</td></tr>
<tr><td><code>login-test-results.json</code>（v1）</td><td>作为对比基准保留，本轮输出 <code>login-test-results-v2.json</code></td></tr>
</table>
<h2>三、执行过程（步骤级记录）</h2>
<div class="step">
<h3>步骤 1｜打开登录页并验证页面标题</h3>
<div class="meta">操作：goto http://123.56.21.178:8080/login → 读取 &lt;title&gt; → 断言</div>
<p>实际标题：<b>自动化测试平台</b>，与期望完全一致，页面正常加载。</p>
{img_tag(os.path.join(TMP, "login-page-title-check.png"), "步骤1截图：登录页（标题验证通过）")}
</div>
{steps}
<h2>四、用例明细汇总</h2>
<table><tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>{rows}</table>
<h2>五、后端 API 响应记录</h2>
<table><tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>{api_rows}</table>
<h2>六、与首轮对比（稳定性结论）</h2>
<div class="good">
✅ <b>结果稳定：6/6 条用例 verdict 与首轮完全一致（4 PASS / 2 FAIL，无回归、无新增修复）</b>。<br/>
✅ 关键行为复现：TC01 登录 200 → /dashboard + 「登录成功」；TC04/05/06 前端空值校验 toast 正常；TC02/03 后端 401 拒绝。
</div>
<h2>七、缺陷复测确认</h2>
<div class="warn">
<b>BUG-001（中）｜登录失败时前端无任何错误提示 —— 未修复，仍复现</b><br/>
影响用例：TC02（密码错误）、TC03（账号不存在）。<br/>
本轮实测：前端收到 401 后 hints 为空、页面无任何错误文案；对比 TC04/05/06 前端校验 toast 正常弹出，确认问题仅存在于<b>服务端 401 错误的响应处理分支</b>——错误被吞掉，无 toast/弹窗/行内提示。<br/>
建议：开发修复 `/api/v1/auth/login` 401 响应的前端处理（如 axios 拦截器中对 401 显示「用户名或密码错误」），修复后复用 test-login-cases-v2.py 复测 TC02/TC03。
</div>
<h2>八、测试结论与建议</h2>
<div class="good">
✅ 登录核心链路稳定可用（成功登录、空值校验）；自动化资产复用机制在登录模块同样运转正常。<br/>
❌ BUG-001 经两轮确认未修复，是当前登录模块唯一功能缺陷。
</div>
<p style="line-height:1.8;"><b>建议：</b><br/>
1. 将 BUG-001 提交缺陷跟踪，修复后第三轮回归（复用 test-login-cases-v2.py → v3）；<br/>
2. 登录/注册用例集已全部版本化留存，可作为该平台的 CI 回归基线；<br/>
3. 可补充用例方向：记住我登录态保持、密码错误锁定/频率限制、多端登录互踢（如平台有此功能）。</p>
<footer>本报告由 generate-test-report skill 自动生成（数据版本 v2）· 截图已内嵌，可单文件离线分享</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT, "| size:", os.path.getsize(OUT))
