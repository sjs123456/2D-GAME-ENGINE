# -*- coding: utf-8 -*-
"""调查 TC02/TC03：错误登录时页面到底发生了什么（dialog / toast / 接口响应）"""
import sys, io, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

LOGIN_URL = "http://123.56.21.178:8080/login"
OUT_DIR = ".reasonix/tmp"

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

def run_probe(p, label, user, pwd):
    print(f"\n===== {label} user={user!r} pwd={pwd!r} =====")
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page = context.new_page()
    page.set_default_timeout(5000)

    dialogs = []
    page.on("dialog", lambda d: (dialogs.append({"type": d.type, "message": d.message}), d.accept()))
    responses = []
    page.on("response", lambda r: responses.append((r.status, r.url)) if "api" in r.url or "login" in r.url.lower() else None)

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    page.wait_for_selector("button.submit-btn", timeout=10000)
    page.evaluate(OBSERVER_JS)

    if user:
        page.fill("input.form-input >> nth=0", user)
    if pwd:
        page.fill("input.form-input >> nth=1", pwd)

    page.click("button.submit-btn")
    t0 = time.time()
    snapshots = []
    while time.time() - t0 < 3.5:
        try:
            toasts = page.evaluate("() => window.__toastTexts || []")
            body = page.inner_text("body", timeout=800)
            snapshots.append({"t": round(time.time() - t0, 2), "toasts": list(toasts), "body_tail": body[-300:]})
        except Exception:
            snapshots.append({"t": round(time.time() - t0, 2), "toasts": [], "body_tail": "(read fail)"})
        time.sleep(0.2)

    print("URL:", page.url)
    print("DIALOGS:", json.dumps(dialogs, ensure_ascii=False))
    print("RESPONSES:")
    for s, u in responses:
        print(f"  {s} {u}")
    print("SNAPSHOT 采样（每0.4s取一个）:")
    for s in snapshots[::2]:
        print(f"  t={s['t']}s toasts={s['toasts'][:5]} body_tail={s['body_tail'][-120:]!r}")
    page.screenshot(path=f"{OUT_DIR}/probe-{label}.png", full_page=True)
    context.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    run_probe(p, "tc02-wrongpwd", "admin123", "Admin1234")
    run_probe(p, "tc03-nouser", "nosuchuser888", "Admin123")
    browser.close()
print("\n调查完成")
