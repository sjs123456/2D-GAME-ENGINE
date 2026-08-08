# -*- coding: utf-8 -*-
"""探测：1) 定时任务创建 500 响应体  2) 关键字列表搜索 kw_"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
ts = io.open(".reasonix/tmp/explore-ts.txt", encoding="utf-8").read().strip()
SUITE = f"suite_{ts}"
KW = f"kw_{ts}"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def choose_select(page, scope, label_text, want):
    try:
        fi = scope.locator(".el-form-item").filter(has_text=label_text).first
        if fi.count() == 0:
            fi = page.locator(".el-form-item").filter(has_text=label_text).first
        sel2 = fi.locator(".el-select")
        if sel2.count() > 0:
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
            page.keyboard.press("Escape")
            return f"no-opt:{want}"
    except Exception as e:
        return f"err:{str(e)[:80]}"

def fill_by_label(page, scope, label_text, value):
    try:
        fi = scope.locator(".el-form-item").filter(has_text=label_text).first
        inp = fi.locator("input, textarea")
        inp.first.fill(value)
        return "ok"
    except Exception as e:
        return f"err:{str(e)[:80]}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=".reasonix/tmp/explore-auth.json", viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(10000)

    # ---- 1. 定时任务 500 响应体 ----
    print("===== 定时任务创建 500 探测 =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/schedules", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1000)
    page.locator("button:has-text('新建定时任务')").first.click()
    page.wait_for_timeout(700)
    dlg = page.locator(".el-dialog:visible").last
    print("弹窗标题:", clean(dlg.locator(".el-dialog__title").first.inner_text()), flush=True)
    fill_by_label(page, dlg, "任务名称", f"sched_probe_{ts}")
    fill_by_label(page, dlg, "Cron 表达式", "0 8 * * *")
    print("关联套件选择:", choose_select(page, dlg, "关联套件", SUITE), flush=True)
    fill_by_label(page, dlg, "描述", "probe")
    # 捕获 POST schedules 响应
    try:
        with page.expect_response(lambda r: "/schedules" in r.url and r.request.method == "POST", timeout=15000) as ri:
            dlg.locator("button:has-text('确认创建')").first.click()
        resp = ri.value
        print("状态码:", resp.status, flush=True)
        try:
            body = resp.body().decode("utf-8", errors="replace")
            print("响应体:", body[:800], flush=True)
        except Exception as e:
            print("读响应体失败:", str(e)[:100], flush=True)
    except Exception as e:
        print("expect_response 超时/失败:", str(e)[:150], flush=True)
    page.wait_for_timeout(1500)
    print("弹窗仍在:", page.locator(".el-dialog:visible").count() > 0, flush=True)
    page.screenshot(path=".reasonix/tmp/probe-schedule-500.png", full_page=True)

    # ---- 2. 关键字列表搜索 ----
    print("\n===== 关键字列表搜索探测 =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/keywords", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(1000)
    sb = page.locator("input[placeholder='搜索关键字名称...']")
    sb.fill(KW)
    sb.press("Enter")
    page.wait_for_timeout(1500)
    print("URL:", page.url, flush=True)
    print("表头:", [clean(page.locator('.el-table__header th').nth(k).inner_text()) for k in range(page.locator('.el-table__header th').count())], flush=True)
    rows = page.locator(".el-table__body tbody tr")
    print("行数:", rows.count(), flush=True)
    for i in range(rows.count()):
        print("row:", [clean(rows.nth(i).locator("td").nth(k).inner_text()) for k in range(rows.nth(i).locator("td").count())], flush=True)
    body_txt = page.inner_text("body")
    print("body 含 kw_ts:", KW in body_txt, flush=True)
    # 不搜索，直接看全部列表
    sb.fill("")
    sb.press("Enter")
    page.wait_for_timeout(1500)
    rows2 = page.locator(".el-table__body tbody tr")
    print("清空搜索后行数:", rows2.count(), flush=True)
    for i in range(rows2.count()):
        print("row:", [clean(rows2.nth(i).locator("td").nth(k).inner_text()) for k in range(rows2.nth(i).locator("td").count())], flush=True)
    page.screenshot(path=".reasonix/tmp/probe-keyword-list.png", full_page=True)
    browser.close()
