# -*- coding: utf-8 -*-
"""探测：不同 cron/参数组合下定时任务创建是否仍 500"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
ts = io.open(".reasonix/tmp/explore-ts.txt", encoding="utf-8").read().strip()
SUITE = f"suite_{ts}"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def choose_suite(page, dlg, want):
    try:
        fi = dlg.locator(".el-form-item").filter(has_text="关联套件").first
        sel2 = fi.locator(".el-select")
        sel2.first.click()
        page.wait_for_timeout(500)
        items = page.locator(".el-select-dropdown__item:visible")
        for k in range(items.count()):
            t = clean(items.nth(k).inner_text())
            if t and (want in t or t in want):
                items.nth(k).click()
                page.wait_for_timeout(200)
                return f"el:{t}"
        for k in range(items.count()):
            t = clean(items.nth(k).inner_text())
            if t:
                items.nth(k).click()
                page.wait_for_timeout(200)
                return f"el-first:{t}"
    except Exception as e:
        return f"err:{str(e)[:80]}"

def fill_lbl(page, dlg, lbl, val):
    try:
        dlg.locator(".el-form-item").filter(has_text=lbl).first.locator("input, textarea").first.fill(val)
        return "ok"
    except Exception as e:
        return f"err:{str(e)[:60]}"

variants = [
    ("sched_v1", "*/5 * * * *"),
    ("sched_v2", "0 0 * * 1"),
    ("sched_v3", "30 8 * * *"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    for name, cron in variants:
        print(f"\n===== 变体 {name} cron={cron} =====", flush=True)
        page.goto(f"{BASE}/projects/{PID}/schedules", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(900)
        page.locator("button:has-text('新建定时任务')").first.click()
        page.wait_for_timeout(700)
        dlg = page.locator(".el-dialog:visible").last
        fill_lbl(page, dlg, "任务名称", name)
        fill_lbl(page, dlg, "Cron 表达式", cron)
        print("套件:", choose_suite(page, dlg, SUITE), flush=True)
        fill_lbl(page, dlg, "描述", "variant")
        try:
            with page.expect_response(lambda r: "/schedules" in r.url and r.request.method == "POST", timeout=15000) as ri:
                dlg.locator("button:has-text('确认创建')").first.click()
            resp = ri.value
            print("状态码:", resp.status, flush=True)
            try:
                print("响应体:", resp.body().decode("utf-8", errors="replace")[:300], flush=True)
            except Exception as e:
                print("读体失败:", str(e)[:80], flush=True)
        except Exception as e:
            print("超时/失败:", str(e)[:120], flush=True)
        page.wait_for_timeout(1000)
        try:
            dlg.locator("button:has-text('取消')").first.click(timeout=2000)
        except Exception:
            page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    browser.close()
