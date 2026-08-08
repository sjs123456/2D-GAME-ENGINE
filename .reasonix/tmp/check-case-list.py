# -*- coding: utf-8 -*-
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
ts = io.open(".reasonix/tmp/explore-ts.txt", encoding="utf-8").read().strip()
CASE = f"case_{ts}"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.goto(f"{BASE}/projects/{PID}/testcases?type=web", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1200)
    sb = page.locator("input[placeholder='搜索用例名称...']")
    sb.fill(CASE)
    sb.press("Enter")
    page.wait_for_timeout(1200)
    print("=== 表头 ===")
    ths = page.locator(".el-table__header th")
    print([clean(ths.nth(k).inner_text()) for k in range(ths.count())])
    print("=== 行 ===")
    rows = page.locator(".el-table__body tbody tr")
    print("行数:", rows.count())
    for i in range(rows.count()):
        cells = [clean(rows.nth(i).locator("td").nth(k).inner_text()) for k in range(rows.nth(i).locator("td").count())]
        print(f"row{i}:", cells)
    print("=== body 含 Web 片段 ===")
    body = page.inner_text("body")
    for m in re.finditer(r".{0,20}Web.{0,20}", body):
        print("  ...", m.group(0).replace("\n", " "))
        if m.start() > 4000:
            break
    page.screenshot(path=".reasonix/tmp/check-case-list.png", full_page=True)
    browser.close()
