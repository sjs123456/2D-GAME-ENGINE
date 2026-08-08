# -*- coding: utf-8 -*-
"""定位卡点：只访问页面并做基础提取，打印每步耗时"""
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

LOGIN_URL = "http://123.56.21.178:8080/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
BASE = "http://123.56.21.178:8080"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def step(msg, t0):
    print(f"  [{time.time()-t0:6.1f}s] {msg}", flush=True)

with sync_playwright() as p:
    t0 = time.time()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(8000)
    page.on("dialog", lambda d: d.accept())

    step("goto login", t0)
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    step("fill+click", t0)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)
    step(f"登录后 {page.url}", t0)

    for name, url in [
        ("全部用例", f"{BASE}/projects/{PID}/testcases"),
        ("API测试", f"{BASE}/projects/{PID}/api"),
        ("AI测试助手", f"{BASE}/projects/{PID}/ai-assistant"),
    ]:
        t1 = time.time()
        step(f"goto {name}", t0)
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        step(f"  goto done -> {page.url}", t0)
        page.wait_for_timeout(1500)
        step("  wait 1.5s", t0)
        h2 = clean(page.locator("h2").first.inner_text()) if page.locator("h2").count() else ""
        step(f"  h2={h2}", t0)
        n_in = page.locator("input").count()
        step(f"  inputs={n_in}", t0)
        n_btn = page.locator("button").count()
        step(f"  buttons={n_btn}", t0)
        btns = []
        for i in range(n_btn):
            btns.append(clean(page.locator("button").nth(i).inner_text()))
        step(f"  btn texts done", t0)
        ths = page.locator(".el-table__header th")
        headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
        step(f"  headers={[h for h in headers if h]}", t0)
        rows = page.locator(".el-table__body tbody tr").count()
        step(f"  rows={rows}", t0)
        pg = page.locator(".el-pagination").count()
        step(f"  pagination={pg}", t0)
        step(f"  {name} 完成 总耗时 {time.time()-t1:6.1f}s", t0)

    browser.close()
    step("DONE", t0)
