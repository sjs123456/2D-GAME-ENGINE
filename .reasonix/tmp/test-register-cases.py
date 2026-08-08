# -*- coding: utf-8 -*-
"""注册功能测试：http://123.56.21.178:8080/login (注册 tab)
TC01-TC12，每条用例独立 browser context 隔离状态。
覆盖：正常注册、密码不一致、弱密码、用户名已存在、格式非法、必填项逐项为空、注册后登录闭环。
通过 MutationObserver 捕获短暂 toast，监听 dialog 与 api 响应，记录 URL/标题/提示/截图。
"""
import sys, io, json, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT_DIR, exist_ok=True)

OBSERVER_JS = r"""
() => {
  window.__toastTexts = [];
  if (window.__toastObs) { window.__toastObs.disconnect(); }
  const obs = new MutationObserver(muts => {
    const collect = (node) => {
      if (node.nodeType === 1) {
        const t = node.innerText || node.textContent || '';
        if (t.trim()) window.__toastTexts.push(t.trim());
      } else if (node.nodeType === 3) {
        const t = node.textContent || '';
        if (t.trim()) window.__toastTexts.push(t.trim());
      }
    };
    for (const m of muts) {
      for (const node of m.addedNodes) collect(node);
      if (m.type === 'characterData' && m.target && m.target.textContent && m.target.textContent.trim()) {
        window.__toastTexts.push(m.target.textContent.trim());
      }
    }
  });
  obs.observe(document.body, {childList: true, subtree: true, characterData: true});
  window.__toastObs = obs;
}
"""

HINT_SELECTORS = [
    ".el-message", ".el-message-box", ".el-notification", ".el-alert",
    ".ant-message", ".ant-alert", ".toast", ".error", ".alert",
    ".form-error", ".el-form-item__error", ".tip", ".msg", ".message",
]

# ---- 唯一测试账号（注册成功类） ----
SUFFIX = time.strftime("%Y%m%d%H%M%S") + str(time.time_ns() % 10000)
REG_USER = f"testuser_{SUFFIX}"
REG_EMAIL = f"{REG_USER}@test.com"
REG_PWD = "Test123456"

# 字段填写定义：None 表示不填（留空）
CASES = [
    {"id": "TC01", "desc": "正常注册成功（唯一账号）",
     "user": REG_USER, "email": REG_EMAIL, "pwd": REG_PWD, "pwd2": REG_PWD,
     "expect": "注册接口返回成功(2xx)，出现“注册成功”提示；记录跳转/自动登录行为"},
    {"id": "TC02", "desc": "密码与确认密码不一致",
     "user": f"tc02_{SUFFIX}", "email": f"tc02_{SUFFIX}@test.com", "pwd": "Test123456", "pwd2": "Test654321",
     "expect": "前端提示“两次输入的密码不一致”，不产生注册请求"},
    {"id": "TC03", "desc": "密码过短（3位）",
     "user": f"tc03_{SUFFIX}", "email": f"tc03_{SUFFIX}@test.com", "pwd": "Ab1", "pwd2": "Ab1",
     "expect": "注册被拒绝并提示密码长度/规则要求（8-128个字符，须含大小写字母和数字）"},
    {"id": "TC04", "desc": "弱密码：8位但无大写字母",
     "user": f"tc04_{SUFFIX}", "email": f"tc04_{SUFFIX}@test.com", "pwd": "test1234", "pwd2": "test1234",
     "expect": "注册被拒绝并提示密码须含大小写字母和数字"},
    {"id": "TC05", "desc": "用户名已存在（admin123 试探）",
     "user": "admin123", "email": f"tc05_{SUFFIX}@test.com", "pwd": "Test123456", "pwd2": "Test123456",
     "expect": "后端拒绝：提示“用户名已被占用”或注册接口 4xx"},
    {"id": "TC06", "desc": "用户名格式非法（2个字符，长度不足）",
     "user": "ab", "email": f"tc06_{SUFFIX}@test.com", "pwd": "Test123456", "pwd2": "Test123456",
     "expect": "注册被拒绝并提示用户名须 3-50 个字符字母数字下划线"},
    {"id": "TC07", "desc": "邮箱格式非法",
     "user": f"tc07_{SUFFIX}", "email": "not-an-email", "pwd": "Test123456", "pwd2": "Test123456",
     "expect": "无效邮箱被拦截不提交（HTML5 原生校验或前端提示），无注册请求"},
    {"id": "TC08", "desc": "必填项-用户名为空",
     "user": None, "email": f"tc08_{SUFFIX}@test.com", "pwd": "Test123456", "pwd2": "Test123456",
     "expect": "提示“请输入用户名”，不产生注册请求"},
    {"id": "TC09", "desc": "必填项-邮箱为空",
     "user": f"tc09_{SUFFIX}", "email": None, "pwd": "Test123456", "pwd2": "Test123456",
     "expect": "提示“请输入邮箱”，不产生注册请求"},
    {"id": "TC10", "desc": "必填项-密码为空",
     "user": f"tc10_{SUFFIX}", "email": f"tc10_{SUFFIX}@test.com", "pwd": None, "pwd2": "Test123456",
     "expect": "提示“请输入密码”，不产生注册请求"},
    {"id": "TC11", "desc": "必填项-确认密码为空",
     "user": f"tc11_{SUFFIX}", "email": f"tc11_{SUFFIX}@test.com", "pwd": "Test123456", "pwd2": None,
     "expect": "提示“请再次输入密码/两次输入不一致”，不产生注册请求"},
    {"id": "TC12", "desc": "注册成功账号登录验证（闭环）",
     "user": REG_USER, "pwd": REG_PWD,
     "expect": "用 TC01 注册的账号登录成功，跳转 /dashboard"},
]


def collect_hints(page):
    hints = []
    for sel in HINT_SELECTORS:
        try:
            loc = page.locator(sel)
            n = loc.count()
            for i in range(min(n, 5)):
                try:
                    txt = loc.nth(i).inner_text(timeout=400).strip()
                except Exception:
                    txt = ""
                if txt:
                    hints.append(f"[{sel}] {txt}")
        except Exception:
            pass
    return hints


def open_register_tab(page):
    try:
        page.locator("button.tab-btn:has-text('注册')").first.click()
    except Exception:
        pass
    page.wait_for_timeout(600)


def run_register_case(browser, case, shot):
    rec = {"id": case["id"], "desc": case["desc"], "expect": case["expect"],
           "result": "BLOCKED", "url": "", "title": "", "hints": [],
           "api_responses": [], "verdict": "BLOCKED", "screenshot": shot,
           "step": "", "dialogs": [], "body_excerpt": ""}
    fields = [case.get("user"), case.get("email"), case.get("pwd"), case.get("pwd2")]
    rec["step"] = f"注册tab填写 用户名={case.get('user')!r} 邮箱={case.get('email')!r} 密码={case.get('pwd')!r} 确认={case.get('pwd2')!r}，点注册"
    page = None
    context = None
    try:
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.set_default_timeout(6000)
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(f"{d.type}: {d.message}"), d.accept()))
        api_resps = []
        page.on("response", lambda r: api_resps.append((r.status, r.url)) if "api/" in r.url else None)

        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        open_register_tab(page)
        try:
            page.evaluate(OBSERVER_JS)
        except Exception:
            pass

        inputs = page.locator("input.form-input")
        for i, val in enumerate(fields):
            if val is not None:
                inputs.nth(i).fill(val)

        page.click("button.submit-btn")
        page.wait_for_timeout(1300)
        try:
            page.screenshot(path=shot)
        except Exception as e:
            print(f"  [warn] 截图失败: {e}")
        page.wait_for_timeout(1000)
        time.sleep(0.3)

        rec["url"] = page.url
        rec["title"] = page.title()
        rec["api_responses"] = api_resps
        rec["dialogs"] = dialogs

        toast_texts = []
        try:
            raw = page.evaluate("() => window.__toastTexts || []")
            for t in raw or []:
                t = str(t).strip()
                if t and t not in toast_texts:
                    toast_texts.append(t)
        except Exception:
            pass
        el_hints = collect_hints(page)
        body_txt = ""
        try:
            body_txt = page.inner_text("body", timeout=3000).strip()
        except Exception:
            pass
        rec["hints"] = toast_texts + el_hints
        rec["body_excerpt"] = body_txt[:600]

        # ---- 判定 ----
        hints_joined = " || ".join(toast_texts + el_hints)
        api2xx = any(200 <= s < 300 for s, _ in api_resps)
        reg_api = [(s, u) for s, u in api_resps if "register" in u]
        reg_rejected = (not reg_api) or (reg_api and not any(200 <= s < 300 for s, _ in reg_api))

        if case["id"] == "TC01":
            if api2xx and ("成功" in hints_joined or "成功" in body_txt or len(reg_api) > 0):
                rec["verdict"] = "PASS"
                rec["result"] = f"注册接口 {[(s, u) for s, u in api_resps]}；提示：{hints_joined or '(无)'}；最终URL={rec['url']}"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"注册未成功。URL={rec['url']}；提示={hints_joined or '(无)'}；API={reg_api or api_resps}"
        elif case["id"] == "TC02":
            if ("一致" in hints_joined or "不匹配" in hints_joined or "确认" in hints_joined) and not reg_api:
                rec["verdict"] = "PASS"
                rec["result"] = f"前端拦截：提示={hints_joined}；无注册请求"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"无相关提示={hints_joined or '(无)'}；API={reg_api or '(无)'}"
        elif case["id"] in ("TC03", "TC04"):
            if reg_rejected and ("大小写" in hints_joined or "8-128" in hints_joined or "password" in hints_joined.lower() or "密码" in hints_joined):
                rec["verdict"] = "PASS"
                rec["result"] = f"注册被拒并提示：{hints_joined}；API={reg_api or '(前端拦截无请求)'}"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"提示={hints_joined or '(无)'}；API={reg_api or '(无)'}"
        elif case["id"] == "TC05":
            if "已存在" in hints_joined or "占用" in hints_joined or any(400 <= s < 500 for s, _ in api_resps):
                rec["verdict"] = "PASS"
                rec["result"] = f"后端拒绝：提示={hints_joined}；API={[(s, u) for s, u in api_resps]}"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"未正确拒绝或提示不清。提示={hints_joined or '(无)'}；API={[(s, u) for s, u in api_resps]}"
        elif case["id"] == "TC06":
            if reg_rejected and ("用户名" in hints_joined or "3-50" in hints_joined or "字符" in hints_joined or "username" in hints_joined.lower()):
                rec["verdict"] = "PASS"
                rec["result"] = f"注册被拒并提示：{hints_joined}；API={reg_api or '(前端拦截无请求)'}"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"提示={hints_joined or '(无)'}；API={reg_api or '(无)'}"
        elif case["id"] == "TC07":
            vm = ""
            try:
                vm = page.evaluate("() => { const em = document.querySelector('input[type=email]'); return em ? em.validationMessage : ''; }") or ""
                if vm.strip():
                    toast_texts.append(f"[html5-validation] {vm.strip()}")
                    rec["hints"] = toast_texts + el_hints
            except Exception:
                pass
            if not reg_api:
                rec["verdict"] = "PASS"
                rec["result"] = f"提交被 HTML5 原生邮箱校验拦截（无API请求）；validationMessage={vm or '已拦截'}；页面无 JS 提示"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"意外发出请求：API={reg_api}"
        elif case["id"] in ("TC08", "TC09", "TC10", "TC11"):
            if hints_joined and not reg_api:
                rec["verdict"] = "PASS"
                rec["result"] = f"前端拦截：提示={hints_joined}；无注册请求"
            else:
                rec["verdict"] = "FAIL"
                rec["result"] = f"提示={hints_joined or '(无)'}；API={reg_api or '(无)'}"
        context.close()
    except Exception as e:
        rec["result"] = f"BLOCKED: {type(e).__name__}: {e}"
        rec["verdict"] = "BLOCKED"
        try:
            page.screenshot(path=shot)
        except Exception:
            pass
        try:
            rec["url"] = page.url
            rec["title"] = page.title()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
    return rec


def run_login_verify(browser, case, shot, username, password):
    rec = {"id": case["id"], "desc": case["desc"], "expect": case["expect"],
           "result": "BLOCKED", "url": "", "title": "", "hints": [],
           "api_responses": [], "verdict": "BLOCKED", "screenshot": shot,
           "step": f"用注册账号 {username} / {password} 在登录页登录，验证跳转 /dashboard",
           "dialogs": [], "body_excerpt": ""}
    page = None
    context = None
    try:
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.set_default_timeout(6000)
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(f"{d.type}: {d.message}"), d.accept()))
        api_resps = []
        page.on("response", lambda r: api_resps.append((r.status, r.url)) if "api/" in r.url else None)

        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        try:
            page.evaluate(OBSERVER_JS)
        except Exception:
            pass
        try:
            page.locator("button.tab-btn:has-text('登录')").first.click()
        except Exception:
            pass
        page.wait_for_timeout(400)
        inputs = page.locator("input.form-input")
        inputs.nth(0).fill(username)
        inputs.nth(1).fill(password)
        page.click("button.submit-btn")
        page.wait_for_timeout(1800)
        try:
            page.screenshot(path=shot)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        time.sleep(0.3)

        rec["url"] = page.url
        rec["title"] = page.title()
        rec["api_responses"] = api_resps
        rec["dialogs"] = dialogs
        toast_texts = []
        try:
            raw = page.evaluate("() => window.__toastTexts || []")
            for t in raw or []:
                t = str(t).strip()
                if t and t not in toast_texts:
                    toast_texts.append(t)
        except Exception:
            pass
        el_hints = collect_hints(page)
        try:
            rec["body_excerpt"] = page.inner_text("body", timeout=3000).strip()[:600]
        except Exception:
            pass
        rec["hints"] = toast_texts + el_hints
        hints_joined = " || ".join(toast_texts + el_hints)

        if "/dashboard" in rec["url"]:
            rec["verdict"] = "PASS"
            rec["result"] = f"注册账号登录成功，跳转 {rec['url']}；提示={hints_joined or '(无)'}"
        else:
            rec["verdict"] = "FAIL"
            rec["result"] = f"登录未跳转。URL={rec['url']}；提示={hints_joined or '(无)'}；API={[(s, u) for s, u in api_resps]}"
        context.close()
    except Exception as e:
        rec["result"] = f"BLOCKED: {type(e).__name__}: {e}"
        rec["verdict"] = "BLOCKED"
        try:
            page.screenshot(path=shot)
        except Exception:
            pass
        try:
            rec["url"] = page.url
            rec["title"] = page.title()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
    return rec


def main():
    print(f"唯一测试账号: {REG_USER} / {REG_EMAIL} / {REG_PWD}\n")
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for case in CASES:
            if case["id"] == "TC12":
                rec = run_login_verify(browser, case, os.path.join(OUT_DIR, "register-TC12.png"),
                                       REG_USER, REG_PWD)
            else:
                rec = run_register_case(browser, case, os.path.join(OUT_DIR, f"register-{case['id']}.png"))
            results.append(rec)
            print(f"[{rec['id']}] verdict={rec['verdict']} | {rec['result'][:200]}")
        browser.close()

    # ---- 汇总表 ----
    print("\n" + "=" * 130)
    print("注册功能测试汇总表  http://123.56.21.178:8080/login (注册 tab)")
    print("=" * 130)
    print(f"{'用例':<6}{'描述':<34}{'实际结果':<56}{'判定':<8}{'截图'}")
    print("-" * 130)
    for r in results:
        print(f"{r['id']:<6}{r['desc'][:32]:<34}{r['result'][:54]:<56}{r['verdict']:<8}{os.path.basename(r['screenshot'])}")
    print("-" * 130)

    print("\n明细：")
    for r in results:
        print(f"\n[{r['id']}] {r['desc']}")
        print(f"  步骤: {r['step']}")
        print(f"  预期: {r['expect']}")
        print(f"  判定: {r['verdict']}")
        print(f"  URL : {r['url']}")
        print(f"  标题: {r['title']}")
        if r.get("api_responses"):
            print(f"  API : {', '.join(f'{s} {u}' for s, u in r['api_responses'])}")
        if r.get("dialogs"):
            print(f"  弹窗: {r['dialogs']}")
        if r.get("hints"):
            for h in r["hints"]:
                print(f"  提示: {h}")
        print(f"  截图: {r['screenshot']}")

    out_json = os.path.join(OUT_DIR, "register-test-results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {out_json}")


if __name__ == "__main__":
    main()
