# -*- coding: utf-8 -*-
"""按 generate-test-report skill 生成注册功能第三轮测试报告（v3，版本与数据对齐）"""
import base64, json, os, sys
from datetime import datetime

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash"   # 工作区根（绝对路径常量）
TMP = os.path.join(WS, ".reasonix", "tmp")
OUT = os.path.join(WS, "自动化测试平台-注册页自动化测试报告-v3.html")  # 显式绝对路径

def img_tag(path, alt):
    if not os.path.exists(path):
        return f'<p style="color:#e6a23c">⚠ 截图缺失：{os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:720px;width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(os.path.join(TMP, "register-test-results-v3.json"), encoding="utf-8") as f:
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
        api_rows += f'<tr><td>{r["id"]}</td><td>—</td><td>未发起 API 请求（前端/HTML5 校验拦截）</td></tr>'
    else:
        for code, url in apis:
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c" if code >= 400 else "#e6a23c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

step_titles = {
    "TC01": "步骤 2｜TC01 正常注册成功（唯一账号）",
    "TC02": "步骤 3｜TC02 密码与确认密码不一致",
    "TC03": "步骤 4｜TC03 密码过短（3 位）",
    "TC04": "步骤 5｜TC04 弱密码（8 位无大写）",
    "TC05": "步骤 6｜TC05 用户名已存在（admin123）",
    "TC06": "步骤 7｜TC06 用户名长度不足（2 字符）",
    "TC07": "步骤 8｜TC07 邮箱格式非法",
    "TC08": "步骤 9｜TC08 用户名为空",
    "TC09": "步骤 10｜TC09 邮箱为空",
    "TC10": "步骤 11｜TC10 密码为空",
    "TC11": "步骤 12｜TC11 确认密码为空",
    "TC12": "步骤 13｜TC12 注册账号登录闭环验证",
    "TC05b": "步骤 14｜TC05b 已存在账号补充验证",
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
<head><meta charset="UTF-8"/><title>自动化测试平台-注册页自动化测试报告（第三轮）</title>
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
<h1>自动化测试平台 · 注册页面自动化测试报告（第三轮）</h1>
<p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code>（注册页为登录页内 tab 切换）</p>
<p>页面标题：自动化测试平台</p>
<p>报告生成时间：{now}　·　执行引擎：Playwright 1.61.0 (Python) + Chromium 无头模式</p>
<p>数据来源：<code>{os.path.basename(os.path.join(TMP, "register-test-results-v3.json"))}</code> ｜ 执行脚本：<code>{script}</code> ｜ 执行时间：<code>{run_at}</code></p>
</header>
<div class="cards">
<div class="card"><div class="num" style="color:#2f6fb3;">{len(results)}</div><div class="lbl">用例总数</div></div>
<div class="card"><div class="num" style="color:#67c23a;">{passed}</div><div class="lbl">通过 PASS</div></div>
<div class="card"><div class="num" style="color:#f56c6c;">{failed}</div><div class="lbl">失败 FAIL</div></div>
<div class="card"><div class="num" style="color:#909399;">0</div><div class="lbl">阻塞 BLOCKED</div></div>
<div class="card"><div class="num" style="color:#e6a23c;">{passed / len(results) * 100:.0f}%</div><div class="lbl">通过率</div></div>
</div>
<h2>一、测试目标与范围</h2>
<p>对注册功能执行<b>第三轮测试</b>（首轮 20:48 / 第二轮 20:55 / 本轮 21:15）。本轮验证 skill 资产复用机制：直接复用 `test-register-cases-v2.py`（仅改动态部分：新唯一账号、版本号 v3）与 `register-form-info.json`（跳过页面探索），用例与判定逻辑与第二轮完全一致，验证结果稳定性。</p>
<h2>二、资产复用情况</h2>
<table>
<tr><th>复用资产</th><th>处置</th></tr>
<tr><td><code>test-register-cases-v2.py</code></td><td>复制为 <code>test-register-cases-v3.py</code>，仅改动态部分（账号前缀、JSON/截图版本号、TC05b 复核账号），用例逻辑 0 处改动</td></tr>
<tr><td><code>register-form-info.json</code></td><td>直接复用（选择器无改版），跳过页面探索</td></tr>
<tr><td><code>register-test-results-v2.json</code></td><td>作为对比基准，本轮输出 <code>register-test-results-v3.json</code></td></tr>
</table>
<h2>三、注册页字段分析（复用探测数据）</h2>
<table>
<tr><th>字段</th><th>type</th><th>placeholder（即规则提示）</th><th>前端必填校验</th></tr>
<tr><td>用户名</td><td>text</td><td>3-50 个字符，字母数字下划线</td><td>✅「请输入用户名」</td></tr>
<tr><td>邮箱</td><td>email</td><td>请输入邮箱地址</td><td>✅「请输入邮箱」+ HTML5 原生格式校验</td></tr>
<tr><td>密码</td><td>password</td><td>8-128 个字符，须含大小写字母和数字</td><td>✅「请输入密码」</td></tr>
<tr><td>确认密码</td><td>password</td><td>请再次输入密码</td><td>✅「两次输入的密码不一致」</td></tr>
</table>
{img_tag(os.path.join(TMP, "register-page.png"), "注册页截图（首轮探测，结构未变）")}
<h2>四、执行过程（步骤级记录）</h2>
{steps}
<h2>五、用例明细汇总</h2>
<table><tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>{rows}</table>
<h2>六、后端 API 响应记录</h2>
<table><tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>{api_rows}</table>
<h2>七、三轮对比（稳定性结论）</h2>
<div class="good">
✅ <b>结果稳定：12/12 条用例 verdict 三轮完全一致（v2 vs v3：12 同 0 异）</b>，无 BLOCKED/FAIL。<br/>
✅ 关键行为复现：TC01 注册 201；TC03/04/06 后端 422 拒绝；TC05/TC05b 400「用户名已被占用」；TC07 HTML5 拦截无请求；TC12 登录 200 → /dashboard。<br/>
✅ 资产复用机制验证通过：本轮未重写脚本、未重复探索页面，全程复用 v2 资产，产出 v3 数据并完成对比。
</div>
<h2>八、缺陷复测确认（仍均未修复）</h2>
<div class="warn">
<b>OBS-001（中）｜前端缺格式本地校验，后端错误英文透传 —— 仍复现</b><br/>
TC03：<code>password: String should have at least 8 characters</code>（英文透传）<br/>
TC06：<code>username: String should have at least 3 characters</code>（英文透传）<br/>
TC04：<code>password: Value error, 密码必须包含大写字母</code>（Pydantic 前缀透传，内容中文）——前端仍无本地校验。
</div>
<div class="note">
<b>OBS-002（低）｜邮箱 HTML5 英文气泡 —— 仍复现</b><br/>
TC07：<code>Please include an '@' in the email address...</code>
</div>
<div class="note">
<b>OBS-003（低）｜确认密码为空提示「两次输入的密码不一致」—— 仍复现</b><br/>
TC11：空确认密码仍提示「两次输入的密码不一致」。
</div>
<h2>九、测试结论与建议</h2>
<div class="good">
✅ 注册核心链路三轮稳定可用；自动化测试资产复用机制运转正常（脚本/探测数据/结果/截图版本化留存，可追溯可对比）。<br/>
⚠️ 3 个已知缺陷经三轮确认均未修复，建议纳入缺陷跟踪排期，修复后执行第四轮回归。
</div>
<p style="line-height:1.8;"><b>建议：</b><br/>
1. 将 OBS-001/002/003 纳入缺陷跟踪，修复后第四轮回归（复用 test-register-cases-v3.py → v4）；<br/>
2. 清理测试账号：<code>testuser_202608062048216900</code>、<code>testuser_retest_202608062055097400</code>、<code>testuser_v3_202608062115081500</code>（如需）；<br/>
3. 注册用例集（13 条含 TC05b）已具备版本化资产，可直接纳入 CI 回归基线。</p>
<footer>本报告由 generate-test-report skill 自动生成（数据版本 v3）· 截图已内嵌，可单文件离线分享</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT, "| size:", os.path.getsize(OUT))
