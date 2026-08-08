# -*- coding: utf-8 -*-
"""补充探测3：API测试新建tooltip、各页筛选下拉选项"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
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
    page.set_default_timeout(8000)
    page.on("dialog", lambda d: d.accept())

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)

    out = {}

    # API测试新建 tooltip
    print("===== API测试-新建按钮tooltip =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/api", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    btn = page.locator("button:has-text('新建')").first
    try:
        btn.hover()
        page.wait_for_timeout(900)
        poppers = page.locator(".el-popper:visible, .el-tooltip__popper:visible")
        tips = []
        for i in range(poppers.count()):
            t = clean(poppers.nth(i).inner_text())
            if t and "Android" not in t and "空闲" not in t:
                tips.append(t)
        print("  tooltip:", tips, flush=True)
        out["api_new_tooltip"] = tips
    except Exception as e:
        print("  hover异常:", str(e)[:100], flush=True)
    page.screenshot(path=f"{OUT_DIR}/explore-sub-API测试-新建hover.png", full_page=True)

    # 全部用例筛选下拉
    print("\n===== 全部用例筛选下拉 =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/testcases", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    sels = page.locator(".el-select.filter-item")
    sel_info = []
    for k in range(sels.count()):
        try:
            sels.nth(k).click()
            page.wait_for_timeout(700)
            opts = page.locator(".el-select-dropdown__item:visible")
            ot = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
            ot = [o for o in ot if o]
            sel_info.append(ot)
            print(f"  下拉[{k}]: {ot}", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception as e:
            sel_info.append(["err"])
            print(f"  下拉[{k}]异常: {str(e)[:80]}", flush=True)
    out["testcases_filters"] = sel_info

    # 执行记录筛选下拉
    print("\n===== 执行记录筛选下拉 =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/executions", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    sels = page.locator(".el-select.filter-item")
    sel_info = []
    for k in range(sels.count()):
        try:
            sels.nth(k).click()
            page.wait_for_timeout(700)
            opts = page.locator(".el-select-dropdown__item:visible")
            ot = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
            ot = [o for o in ot if o]
            sel_info.append(ot)
            print(f"  下拉[{k}]: {ot}", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception as e:
            sel_info.append(["err"])
    out["executions_filters"] = sel_info

    # 测试报告筛选
    print("\n===== 测试报告筛选下拉 =====", flush=True)
    page.goto(f"{BASE}/projects/{PID}/reports", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    sels = page.locator(".el-select")
    sel_info = []
    for k in range(sels.count()):
        try:
            sels.nth(k).click()
            page.wait_for_timeout(700)
            opts = page.locator(".el-select-dropdown__item:visible")
            ot = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
            ot = [o for o in ot if o]
            sel_info.append(ot)
            print(f"  下拉[{k}]: {ot}", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception as e:
            sel_info.append(["err"])
    out["reports_filters"] = sel_info

    browser.close()

with open(f"{OUT_DIR}/explore-final3.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n完成 -> explore-final3.json", flush=True)
