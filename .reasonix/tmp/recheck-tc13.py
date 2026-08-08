# -*- coding: utf-8 -*-
"""精确复核 TC13：API 测试页「新建」按钮点击前后状态对比"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def state(page):
    """采集页面关键状态"""
    dialogs = []
    for i in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(i)
        if d.is_visible():
            dialogs.append(clean(d.locator(".el-dialog__title").first.inner_text()) if d.locator(".el-dialog__title").count() else "dialog")
    return {
        "url": page.url,
        "dialogs": dialogs,
        "new_form": page.locator("input[placeholder='请输入用例名称']").count() > 0,
        "drawer": page.locator(".el-drawer:visible").count() > 0,
        "route_path": page.evaluate("window.location.pathname"),
    }

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    api_reqs = []
    page.on("request", lambda req: api_reqs.append(req.url) if ("/api/" in req.url and req.method in ("POST", "PUT", "DELETE")) else None)

    page.goto(f"{BASE}/projects/{PID}/api", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1500)
    print("=== 点击前状态 ===")
    before = state(page)
    print(before, flush=True)
    btn = page.locator("button:has-text('新建')").first
    btn.click()
    page.wait_for_timeout(2000)
    print("=== 点击后 2s 状态 ===")
    after = state(page)
    print(after, flush=True)
    print("点击期间写请求:", api_reqs, flush=True)
    print("=== 结论 ===")
    changed = before != after
    print("状态变化:", changed, flush=True)
    print("点击后有弹窗:", len(after["dialogs"]) > 0, flush=True)
    print("点击后有新建表单:", after["new_form"], flush=True)
    print("URL 变化:", before["url"] != after["url"], flush=True)
    print("写请求:", api_reqs, flush=True)
    page.screenshot(path=".reasonix/tmp/recheck-TC13.png", full_page=True)
    browser.close()
