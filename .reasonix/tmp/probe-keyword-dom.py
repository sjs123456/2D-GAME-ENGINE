# -*- coding: utf-8 -*-
"""探测关键字库页面列表结构"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
ts = io.open(".reasonix/tmp/explore-ts.txt", encoding="utf-8").read().strip()
KW = f"kw_{ts}"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.goto(f"{BASE}/projects/{PID}/keywords", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1200)
    body = page.inner_text("body")
    print("=== body 全文 ===")
    print(clean(body)[:1200], flush=True)
    # 查找含 kw 的元素
    print("\n=== 含 kw 的元素 ===", flush=True)
    loc = page.locator(f"text={KW}")
    print("匹配数量:", loc.count(), flush=True)
    for i in range(min(loc.count(), 5)):
        el = loc.nth(i)
        print(f"  [{i}] tag={el.evaluate('e=>e.tagName')} class={el.get_attribute('class')} text={clean(el.inner_text())[:100]}", flush=True)
        try:
            parent = el.locator("xpath=..")
            print(f"      parent tag={parent.evaluate('e=>e.tagName')} class={parent.get_attribute('class')} text={clean(parent.inner_text())[:150]}", flush=True)
        except Exception:
            pass
    # 表格类组件检测
    print("\n=== 页面表格/列表类组件 ===", flush=True)
    for sel in [".el-table", ".el-card", ".keyword", ".list-item", ".el-list", "[class*='keyword']", ".el-tag"]:
        n = page.locator(sel).count()
        if n > 0:
            print(f"  {sel}: {n}", flush=True)
    page.screenshot(path=".reasonix/tmp/probe-keyword-dom.png", full_page=True)
    browser.close()
