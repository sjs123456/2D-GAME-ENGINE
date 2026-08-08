# -*- coding: utf-8 -*-
"""探测新建用例页测试步骤区结构"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.goto(f"{BASE}/projects/{PID}/testcases/new/web", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1200)
    print("URL:", page.url)
    print("\n=== 所有按钮 ===")
    for i in range(page.locator("button").count()):
        t = clean(page.locator("button").nth(i).inner_text())
        if t:
            print(f"  btn[{i}]: {t}")
    print("\n=== 所有 textarea ===")
    for i in range(page.locator("textarea").count()):
        el = page.locator("textarea").nth(i)
        print(f"  ta[{i}]: ph={el.get_attribute('placeholder')} name={el.get_attribute('name')}")
    print("\n=== 步骤相关区域 (包含'步骤'的form-item) ===")
    fis = page.locator(".el-form-item")
    for i in range(fis.count()):
        t = clean(fis.nth(i).inner_text())
        if "步骤" in t or "step" in t.lower():
            label = clean(fis.nth(i).locator(".el-form-item__label").first.inner_text())
            print(f"  form-item[{i}] label={label} text={t[:150]}")
    # 点击 添加步骤
    try:
        page.locator("button:has-text('添加步骤')").first.click()
        page.wait_for_timeout(800)
        print("\n=== 点击添加步骤后 ===")
        print("URL:", page.url)
        print("按钮:", [clean(page.locator('button').nth(k).inner_text()) for k in range(page.locator('button').count()) if clean(page.locator('button').nth(k).inner_text())][:20])
        print("textarea:", [clean(page.locator('textarea').nth(k).get_attribute('placeholder') or '') for k in range(page.locator('textarea').count())])
        print("input:", [clean(page.locator('input').nth(k).get_attribute('placeholder') or '') for k in range(page.locator('input').count())])
        page.screenshot(path=f"{OUT_DIR}/probe-step-area.png", full_page=True)
    except Exception as e:
        print("添加步骤失败:", str(e)[:200])
    browser.close()
