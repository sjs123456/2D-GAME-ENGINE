# -*- coding: utf-8 -*-
"""登录功能测试（第二轮）：http://123.56.21.178:8080/login
基于 v1 test-login-cases.py 复用，仅修改动态部分：
  - 输出 JSON 版本号 v2（login-test-results-v2.json）
  - 截图版本后缀 -v2（login-TC{NN}-v2.png）
  - 每条记录追加 script / run_at 追溯字段
用例输入与判定逻辑与 v1 完全一致。
"""
import sys, io, json, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))  # 稳定指向 .reasonix/tmp
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

CASES = [
    {"id": "TC01", "desc": "登录成功：admin123 / Admin123",
     "user": "admin123", "pwd": "Admin123",
     "expect": "跳转到 /dashboard，出现“登录成功”提示"},
    {"id": "TC02", "desc": "密码错误：admin123 / Admin1234",
     "user": "admin123", "pwd": "Admin1234",
     "expect": "不跳转（仍 /login），出现错误提示"},
    {"id": "TC03", "desc": "账号不存在：nosuchuser888 / Admin123",
     "user": "nosuchuser888", "pwd": "Admin123",
     "expect": "不跳转（仍 /login），出现错误提示（与TC02是否相同如实记录）"},
    {"id": "TC04", "desc": "账号为空：密码 Admin123",
     "user": "", "pwd": "Admin123",
     "expect": "不跳转，出现“请输入用户名”类提示"},
    {"id": "TC05", "desc": "密码为空：账号 admin123",
     "user": "admin123", "pwd": "",
     "expect": "不跳转，出现“请输入密码”类提示"},
    {"id": "TC06", "desc": "均为空：直接点登录",
     "user": "", "pwd": "",
     "expect": "不跳转，出现提示（记录实际提示）"},
]


def collect_hints(page):
    hints = []
    for sel in HINT_SELECTORS:
        try:
            loc = page.locator(sel)
            n = loc.count()
            for i in range(min(n, 5)):
                try:
                    txt = loc.nth(i).inner_text(timeout=500).strip()
                except Exception:
                    txt = ""
                if txt:
                    hints.append(f"[{sel}] {txt}")
        except Exception:
            pass
    return hints


def main():
    results = []
    run_at = time.strftime("%Y-%m-%d %H:%M:%S")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for case in CASES:
            rec = {"id": case["id"], "desc": case["desc"], "expect": case["expect"],
                   "result": "BLOCKED", "url": "", "title": "", "hints": [],
                   "api_responses": [], "verdict": "BLOCKED", "screenshot": "",
                   "script": "test-login-cases-v2.py", "run_at": run_at,
                   "step": f"输入账号 {case['user']!r} + 密码 {case['pwd']!r}，点击登录"}
            shot = os.path.join(OUT_DIR, f"login-{case['id']}-v2.png")
            rec["screenshot"] = shot
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
                page.wait_for_selector("button.submit-btn", timeout=10000)
                try:
                    page.evaluate(OBSERVER_JS)
                except Exception as e:
                    print(f"  [warn] observer 注入失败: {e}")

                if case["user"]:
                    page.fill("input.form-input >> nth=0", case["user"])
                if case["pwd"]:
                    page.fill("input.form-input >> nth=1", case["pwd"])

                page.click("button.submit-btn")

                page.wait_for_timeout(1200)
                try:
                    page.screenshot(path=shot)
                except Exception as e:
                    print(f"  [warn] 截图失败: {e}")

                page.wait_for_timeout(1000)  # 累计 ~2.2s
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
                url_ok = "/dashboard" in rec["url"]
                hints_joined = " || ".join(toast_texts + el_hints)
                api401 = any(s == 401 for s, _ in api_resps)
                api200 = any(s == 200 for s, _ in api_resps)

                if case["id"] == "TC01":
                    if url_ok and ("登录成功" in hints_joined or "登录成功" in body_txt):
                        rec["verdict"] = "PASS"
                        rec["result"] = f"跳转 {rec['url']}；提示：{hints_joined}"
                    else:
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"URL={rec['url']}；提示={hints_joined or '(无)'}"
                elif case["id"] in ("TC02", "TC03"):
                    if not url_ok and hints_joined:
                        rec["verdict"] = "PASS"
                        rec["result"] = f"未跳转，仍 {rec['url']}；错误提示：{hints_joined}"
                    elif not url_ok and not hints_joined:
                        # 如实判定：后端 401 拒绝（未跳转符合部分预期），但前端无错误提示 → FAIL
                        api_note = f"API 登录接口 {', '.join(f'{s}' for s, _ in api_resps) or '无请求'}"
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"未跳转但前端无任何错误提示；{api_note}"
                    else:
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"意外跳转 {rec['url']}；提示={hints_joined or '(无)'}"
                elif case["id"] == "TC04":
                    if (not url_ok) and ("用户名" in hints_joined or "用户名" in body_txt):
                        rec["verdict"] = "PASS"
                        rec["result"] = f"未跳转；提示：{hints_joined or body_txt[:200]}"
                    else:
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"URL={rec['url']}；提示={hints_joined or '(无)'}；body={body_txt[:200]!r}"
                elif case["id"] == "TC05":
                    if (not url_ok) and ("密码" in hints_joined or "密码" in body_txt):
                        rec["verdict"] = "PASS"
                        rec["result"] = f"未跳转；提示：{hints_joined or body_txt[:200]}"
                    else:
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"URL={rec['url']}；提示={hints_joined or '(无)'}；body={body_txt[:200]!r}"
                elif case["id"] == "TC06":
                    if not url_ok:
                        rec["verdict"] = "PASS"
                        rec["result"] = f"未跳转；提示：{hints_joined or '(无独立提示容器)'}"
                    else:
                        rec["verdict"] = "FAIL"
                        rec["result"] = f"意外跳转 {rec['url']}"
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
            results.append(rec)
            print(f"[{rec['id']}] verdict={rec['verdict']} | {rec['result'][:220]}")

        browser.close()

    # ---- 汇总表 ----
    print("\n" + "=" * 120)
    print("登录功能测试汇总表(v2)  http://123.56.21.178:8080/login")
    print("=" * 120)
    print(f"{'用例':<6}{'步骤摘要':<30}{'实际结果':<50}{'预期':<30}{'判定':<8}{'截图'}")
    print("-" * 120)
    for r in results:
        step = r["desc"].split("：")[1] if "：" in r["desc"] else r["desc"]
        print(f"{r['id']:<6}{step[:28]:<30}{r['result'][:48]:<50}{r['expect'][:28]:<30}{r['verdict']:<8}{os.path.basename(r['screenshot'])}")
    print("-" * 120)

    print("\n明细：")
    for r in results:
        print(f"\n[{r['id']}] {r['desc']}")
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
        if r.get("body_excerpt"):
            print(f"  body截取: {r['body_excerpt'][:250]!r}")
        print(f"  截图: {r['screenshot']}")

    out_json = os.path.join(OUT_DIR, "login-test-results-v2.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {out_json}")


if __name__ == "__main__":
    main()
