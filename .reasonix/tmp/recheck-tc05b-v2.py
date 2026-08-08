# -*- coding: utf-8 -*-
"""快速复核 TC05b：上轮已存在账号 testuser_202608062048216900 注册应提示用户名已被占用"""
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
    inputs.nth(0).fill("testuser_202608062048216900")
    inputs.nth(1).fill("tc05b_recheck@test.com")
    inputs.nth(2).fill("Test123456")
    inputs.nth(3).fill("Test123456")
    page.click("button.submit-btn")
    page.wait_for_timeout(1300)
    page.screenshot(path=os.path.join(OUT_DIR, "register-TC05b-recheck-v2.png"))
    page.wait_for_timeout(1000)
    toasts = page.evaluate("() => window.__toastTexts || []")
    body = page.inner_text("body")
    print("API:", api)
    print("TOASTS:", json.dumps(toasts, ensure_ascii=False))
    print("HAS_占用:", "已被占用" in body or "已存在" in body)
    print("BODY_TAIL:", body[-120:].replace("\n", " | "))
    context.close()
    browser.close()
