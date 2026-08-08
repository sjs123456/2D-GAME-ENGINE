# -*- coding: utf-8 -*-
"""探测设置/API Token/CI-CD 的 URL 模式"""
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

LOGIN_URL = "http://123.56.21.178:8080/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
BASE = "http://123.56.21.178:8080"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(10000)
    page.on("dialog", lambda d: d.accept())

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)
    print("登录后:", page.url)

    candidates = [
        f"{BASE}/projects/{PID}/settings",
        f"{BASE}/projects/{PID}/settings/api-token",
        f"{BASE}/projects/{PID}/api-token",
        f"{BASE}/projects/{PID}/settings/cicd",
        f"{BASE}/projects/{PID}/cicd",
        f"{BASE}/projects/{PID}/token",
    ]
    for url in candidates:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.5)
            body = clean(page.inner_text("body"))[:150]
            print(f"{url}\n   -> 最终URL: {page.url}\n   -> H2: {clean(page.locator('h2').first.inner_text()) if page.locator('h2').count() else ''}\n   -> body: {body}")
            print("   -")
        except Exception as e:
            print(f"{url} 异常: {str(e)[:100]}")

    browser.close()
    print("完成")
