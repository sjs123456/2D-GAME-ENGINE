# -*- coding: utf-8 -*-
"""TC05b 快速复核（v3 轮）：v2 已存在账号 testuser_retest_202608062055097400 注册应返回 400/提示已被占用
与 recheck-tc05b-v2.py 同构，仅换账号与截图版本。"""
import sys, io, json, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

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

USER = "testuser_retest_202608062055097400"
shot = os.path.join(OUT_DIR, "register-TC05b-v3.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN",
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    page = context.new_page()
    page.set_default_timeout(6000)
    api = []
    page.on("response", lambda r: api.append((r.status, r.url)) if "api/" in r.url else None)
    page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    page.locator("button.tab-btn:has-text('注册')").first.click()
    page.wait_for_timeout(600)
    page.evaluate(OBSERVER_JS)
    inputs = page.locator("input.form-input")
    inputs.nth(0).fill(USER)
    inputs.nth(1).fill("tc05b_v3@test.com")
    inputs.nth(2).fill("Test123456")
    inputs.nth(3).fill("Test123456")
    page.click("button.submit-btn")
    page.wait_for_timeout(1300)
    page.screenshot(path=shot)
    page.wait_for_timeout(1000)
    toasts = page.evaluate("() => window.__toastTexts || []")
    body = page.inner_text("body")
    print("账号:", USER)
    print("API:", api)
    print("TOASTS:", json.dumps(toasts, ensure_ascii=False))
    print("HAS_占用:", "已被占用" in body or "已存在" in body)
    print("BODY_TAIL:", body[-120:].replace("\n", " | "))
    print("截图:", shot)
    context.close()
    browser.close()
