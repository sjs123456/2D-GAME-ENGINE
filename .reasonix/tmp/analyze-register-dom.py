# -*- coding: utf-8 -*-
"""深入分析注册页 DOM 结构：登录/注册表单切换机制、字段定位、提交按钮归属"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page = context.new_page()
    page.set_default_timeout(8000)
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass

    # 点击注册 tab
    try:
        page.locator("button:has-text('注册')").first.click()
        page.wait_for_timeout(1000)
    except Exception as e:
        print("点击注册失败:", e)

    print("=== 页面 HTML 结构（body 前 6000 字符） ===")
    html = page.content()
    print(html[:6000])

    # 分析 input 的祖先链与可见性
    info = page.evaluate("""() => {
      const out = [];
      document.querySelectorAll('input').forEach((inp, idx) => {
        const r = inp.getBoundingClientRect();
        const visible = r.width > 0 && r.height > 0 && inp.offsetParent !== null;
        let ancestor = inp.parentElement;
        const chain = [];
        for (let i = 0; i < 5 && ancestor; i++) {
          chain.push({tag: ancestor.tagName, cls: (ancestor.className || '').slice(0, 80), vis: ancestor.offsetParent !== null});
          ancestor = ancestor.parentElement;
        }
        out.push({idx, type: inp.type, ph: inp.placeholder, visible, chain});
      });
      const btns = [];
      document.querySelectorAll('button').forEach((b, i) => {
        btns.push({i, type: b.type, text: (b.innerText||'').trim().slice(0,20), vis: b.offsetParent !== null, cls: (b.className||'').slice(0,60)});
      });
      return {inputs: out, buttons: btns};
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    context.close()
    browser.close()
