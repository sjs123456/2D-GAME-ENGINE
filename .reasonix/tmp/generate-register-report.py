# -*- coding: utf-8 -*-
"""按 generate-test-report skill 生成注册功能测试报告"""
import base64, json, os, sys
from datetime import datetime

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash"   # 工作区根（绝对路径常量）
TMP = os.path.join(WS, ".reasonix", "tmp")
OUT = os.path.join(WS, "自动化测试平台-注册页自动化测试报告.html")  # 显式绝对路径

def img_tag(path, alt):
    if not os.path.exists(path):
        return f'<p style="color:#e6a23c">⚠ 截图缺失：{os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f'<figure><img src="data:image/png;base64,{b64}" alt="{alt}" '
            f'style="max-width:720px;width:100%;border:1px solid #d9d9d9;border-radius:6px;"/>'
            f'<figcaption style="color:#666;font-size:13px;margin-top:6px;">{alt}</figcaption></figure>')

with open(os.path.join(TMP, "register-test-results.json"), encoding="utf-8") as f:
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
        api_rows += f'<tr><td>{r["id"]}</td><td>—</td><td>未发起 API 请求（前端/HTML5 校验拦截）</td></tr>'
    else:
        for code, url in apis:
            color = "#67c23a" if 200 <= code < 300 else "#f56c6c" if code >= 400 else "#e6a23c"
            api_rows += f'<tr><td>{r["id"]}</td><td style="color:{color};font-weight:600;">{code}</td><td><code>{url}</code></td></tr>'

step_titles = {
    "TC01": "步骤 2｜TC01 正常注册成功（唯一测试账号）",
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
<head><meta charset="UTF-8"/><title>自动化测试平台-注册页自动化测试报告</title>
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
<h1>自动化测试平台 · 注册页面自动化测试报告</h1>
<p>测试地址：<code style="background:rgba(255,255,255,.2);color:#fff;">http://123.56.21.178:8080/login</code>（注册页为登录页内 tab 切换）</p>
<p>页面标题：自动化测试平台</p>
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
<p>针对注册功能进行详尽功能验证，覆盖：正常注册、注册后登录闭环、密码一致性、密码强度、用户名唯一性/长度、邮箱格式、各必填项空值校验，共 {len(results)} 条用例。每条用例使用独立浏览器上下文隔离状态，记录跳转结果、页面提示、后端 API 响应，并为每步操作保存截图。</p>
<h2>二、注册页字段分析</h2>
<p>注册页与登录页共用 <code>/login</code> URL，通过 <b>tab 切换</b>（<code>button.tab-btn</code>）进入，表单为 <code>form.login-form</code>，<b>无验证码、无协议勾选</b>。提示形式：<code>el-message</code> toast（顶部短暂弹出）。</p>
<table>
<tr><th>字段</th><th>type</th><th>placeholder（即规则提示）</th><th>前端必填校验</th></tr>
<tr><td>用户名</td><td>text</td><td>3-50 个字符，字母数字下划线</td><td>✅「请输入用户名」</td></tr>
<tr><td>邮箱</td><td>email</td><td>请输入邮箱地址</td><td>✅「请输入邮箱」+ HTML5 原生格式校验</td></tr>
<tr><td>密码</td><td>password</td><td>8-128 个字符，须含大小写字母和数字</td><td>✅「请输入密码」</td></tr>
<tr><td>确认密码</td><td>password</td><td>请再次输入密码</td><td>✅「两次输入的密码不一致」</td></tr>
</table>
{img_tag(os.path.join(TMP, "register-page.png"), "注册页截图")}
<h2>三、执行过程（步骤级记录）</h2>
{steps}
<h2>四、用例明细汇总</h2>
<table><tr><th>用例</th><th>描述</th><th>操作步骤</th><th>预期结果</th><th>实际结果</th><th>判定</th></tr>{rows}</table>
<h2>五、后端 API 响应记录</h2>
<table><tr><th>用例</th><th>HTTP 状态</th><th>接口</th></tr>{api_rows}</table>
<h2>六、缺陷与观察点</h2>
<div class="warn">
<b>OBS-001（中）｜前端缺少用户名/密码格式本地校验，后端错误消息英文透传</b><br/>
影响用例：TC03（密码过短）、TC04（弱密码）、TC06（用户名过短）。<br/>
实际：用户名长度、密码复杂度（8-128 位含大小写数字）规则仅写在 placeholder 中，前端不校验，直接提交后端；失败时 toast 显示 <b>Pydantic 英文原文</b>（如 <code>password: String should have at least 8 characters</code>），普通中文用户难以理解，且暴露字段名与实现细节。<br/>
建议：前端补充与 placeholder 规则一致的本地校验；后端错误消息本地化为中文。
</div>
<div class="note">
<b>OBS-002（低）｜邮箱格式校验为浏览器原生英文气泡</b><br/>
影响用例：TC07。实际：HTML5 原生校验拦截，提示为英文气泡（"Please include an '@'…"），与页面统一的中文 el-message 风格不一致。建议改用自定义校验统一提示风格。
</div>
<div class="note">
<b>OBS-003（低）｜确认密码为空时提示「两次输入的密码不一致」</b><br/>
影响用例：TC11。文案语义有偏差，建议区分场景提示「请再次输入密码」。
</div>
<div class="note">
<b>OBS-004（安全观察）｜注册无验证码/人机校验，未见频率限制迹象</b><br/>
存在批量注册风险，建议增加验证码或注册频率限制。
</div>
<h2>七、测试结论与建议</h2>
<div class="good">
✅ 注册核心链路可用：12/12 用例通过，注册（201）→ 自动切回登录 tab → 新账号登录成功跳转 /dashboard 的闭环验证通过；前端必填校验与密码一致性校验正确。<br/>
❌ 无功能级失败，存在 1 个中等级别体验问题（英文错误消息透传）与 3 个低级别/安全观察项。
</div>
<p style="line-height:1.8;"><b>建议：</b><br/>
1. 修复 OBS-001：前端补格式本地校验 + 后端错误消息中文化；<br/>
2. 统一邮箱校验提示风格（OBS-002）、优化确认密码空值文案（OBS-003）；<br/>
3. 评估增加验证码/频率限制（OBS-004）；<br/>
4. 测试账号 <code>testuser_202608062048216900</code> 为本次测试真实注册，如需清理请管理员处理；<br/>
5. 建议将注册用例集纳入 CI 回归。</p>
<footer>本报告由 generate-test-report skill 自动生成 · 截图已内嵌，可单文件离线分享</footer>
</div></body></html>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT, "| size:", os.path.getsize(OUT))
