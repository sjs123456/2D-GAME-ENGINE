# -*- coding: utf-8 -*-
"""最终补充探测：新建用例创建页表单、套件/定时任务undefined BUG、API测试新建、设置tab浏览器配置、CI/CD详情"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
BASE = "http://123.56.21.178:8080"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def close_dialog(page):
    try:
        page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=2000)
        return
    except Exception:
        pass
    try:
        page.locator(".el-dialog__headerbtn").first.click(timeout=2000)
        return
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

def get_dialog(page):
    for j in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(j)
        if d.is_visible():
            return d
    return None

def dump_page_form(page, tag):
    """提取页面/弹窗内所有 form-item 字段"""
    f_items = page.locator(".el-form-item")
    fields = []
    for k in range(f_items.count()):
        fi = f_items.nth(k)
        label = clean(fi.locator(".el-form-item__label").first.inner_text())
        req = "is-required" in (fi.get_attribute("class") or "")
        try:
            has_star = "*" in fi.locator(".el-form-item__label").first.inner_html()
        except Exception:
            has_star = req
        ctrls = []
        if fi.locator("input").count() > 0:
            ctrls.append("input")
        if fi.locator("textarea").count() > 0:
            ctrls.append("textarea")
        if fi.locator(".el-select").count() > 0:
            ctrls.append("select")
        if fi.locator(".el-radio").count() > 0:
            ctrls.append("radio")
        if fi.locator(".el-checkbox").count() > 0:
            ctrls.append("checkbox")
        if fi.locator(".el-switch").count() > 0:
            ctrls.append("switch")
        if fi.locator(".el-date-editor").count() > 0:
            ctrls.append("date")
        ph = fi.locator("input").first.get_attribute("placeholder") if fi.locator("input").count() else None
        field = {"name": label, "required": req or has_star, "controls": ctrls}
        if ph:
            field["placeholder"] = ph
        fields.append(field)
    btns = []
    for i in range(page.locator("button").count()):
        t = clean(page.locator("button").nth(i).inner_text())
        if t and t not in btns:
            btns.append(t)
    return {"tag": tag, "url": page.url, "h2": clean(page.locator("h2, .page-title").first.inner_text()) if page.locator("h2, .page-title").count() else "",
            "fields": fields, "buttons": btns}

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

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)
    print(f"[{time.time()-t0:5.1f}s] 登录后 {page.url}", flush=True)
    out = {}

    # ===== 1. 新建用例创建页 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 全部用例-新建用例", flush=True)
    page.goto(f"{BASE}/projects/{PID}/testcases", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建用例')").first.click()
    page.wait_for_timeout(2000)
    print(f"  点击后 URL: {page.url}", flush=True)
    out["new_case_after_click_url"] = page.url
    if page.url != f"{BASE}/projects/{PID}/testcases":
        # 独立创建页
        page.wait_for_timeout(1500)
        body = clean(page.inner_text("body"))[:600]
        print(f"  body: {body}", flush=True)
        out["new_case_page"] = dump_page_form(page, "新建用例页面")
        print(f"  新建用例页表单: {out['new_case_page']['fields']}", flush=True)
        page.screenshot(path=f"{OUT_DIR}/explore-sub-新建用例页面.png", full_page=True)
        page.go_back(timeout=5000)
        page.wait_for_timeout(1200)
    else:
        # 弹窗？
        dlg = get_dialog(page)
        if dlg:
            out["new_case_dialog"] = dump_page_form(dlg, "新建用例弹窗")
            print(f"  新建用例弹窗字段: {out['new_case_dialog']['fields']}", flush=True)
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-新建用例弹窗.png")
            close_dialog(page)
        else:
            print("  既未跳转也未弹窗", flush=True)
            out["new_case_note"] = "点击新建用例后无弹窗无跳转"

    # ===== 2. 测试套件 undefined BUG =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 测试套件-新建套件", flush=True)
    page.goto(f"{BASE}/projects/{PID}/suites", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建套件')").first.click()
    page.wait_for_timeout(2500)
    print(f"  点击后 URL: {page.url}", flush=True)
    out["new_suite_after_click_url"] = page.url
    if "undefined" in page.url:
        body = clean(page.inner_text("body"))[:300]
        print(f"  body(截断): {body}", flush=True)
        out["new_suite_undefined_bug"] = True
        page.screenshot(path=f"{OUT_DIR}/explore-sub-新建套件-undefined.png", full_page=True)
        # 回退
        page.goto(f"{BASE}/projects/{PID}/suites", wait_until="domcontentloaded", timeout=15000)
        time.sleep(1.2)
    elif page.url != f"{BASE}/projects/{PID}/suites":
        page.wait_for_timeout(1500)
        out["new_suite_page"] = dump_page_form(page, "新建套件页面")
        print(f"  新建套件页字段: {out['new_suite_page']['fields']}", flush=True)
        page.screenshot(path=f"{OUT_DIR}/explore-sub-新建套件页面.png", full_page=True)
        page.go_back(timeout=5000)
        page.wait_for_timeout(1200)
    else:
        dlg = get_dialog(page)
        if dlg:
            out["new_suite_dialog"] = dump_page_form(dlg, "新建套件弹窗")
            print(f"  新建套件弹窗字段: {out['new_suite_dialog']['fields']}", flush=True)
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-新建套件弹窗.png")
            close_dialog(page)
        else:
            print("  无跳转无弹窗", flush=True)

    # ===== 3. 定时任务 undefined BUG =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 定时任务-新建定时任务", flush=True)
    page.goto(f"{BASE}/projects/{PID}/schedules", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建定时任务')").first.click()
    page.wait_for_timeout(2500)
    print(f"  点击后 URL: {page.url}", flush=True)
    out["new_schedule_after_click_url"] = page.url
    if "undefined" in page.url:
        out["new_schedule_undefined_bug"] = True
        page.screenshot(path=f"{OUT_DIR}/explore-sub-新建定时任务-undefined.png", full_page=True)
        page.goto(f"{BASE}/projects/{PID}/schedules", wait_until="domcontentloaded", timeout=15000)
        time.sleep(1.2)
    elif page.url != f"{BASE}/projects/{PID}/schedules":
        page.wait_for_timeout(1500)
        out["new_schedule_page"] = dump_page_form(page, "新建定时任务页面")
        print(f"  新建定时任务页字段: {out['new_schedule_page']['fields']}", flush=True)
        page.screenshot(path=f"{OUT_DIR}/explore-sub-新建定时任务页面.png", full_page=True)
        page.go_back(timeout=5000)
        page.wait_for_timeout(1200)
    else:
        dlg = get_dialog(page)
        if dlg:
            out["new_schedule_dialog"] = dump_page_form(dlg, "新建定时任务弹窗")
            print(f"  新建定时任务弹窗字段: {out['new_schedule_dialog']['fields']}", flush=True)
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-新建定时任务弹窗.png")
            close_dialog(page)
        else:
            print("  无跳转无弹窗", flush=True)

    # ===== 4. API测试-新建 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== API测试-新建", flush=True)
    page.goto(f"{BASE}/projects/{PID}/api", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建')").first.click()
    page.wait_for_timeout(2000)
    print(f"  点击后 URL: {page.url}", flush=True)
    out["api_new_after_click_url"] = page.url
    if page.url != f"{BASE}/projects/{PID}/api":
        page.wait_for_timeout(1500)
        out["api_new_page"] = dump_page_form(page, "API新建页面")
        print(f"  API新建页字段: {out['api_new_page']['fields']}", flush=True)
        page.screenshot(path=f"{OUT_DIR}/explore-sub-API新建页面.png", full_page=True)
        page.go_back(timeout=5000)
        page.wait_for_timeout(1200)
    else:
        dlg = get_dialog(page)
        if dlg:
            out["api_new_dialog"] = dump_page_form(dlg, "API新建弹窗")
            print(f"  API新建弹窗字段: {out['api_new_dialog']['fields']}", flush=True)
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-API新建弹窗.png")
            close_dialog(page)
        else:
            print("  无跳转无弹窗（可能是tooltip）", flush=True)
            out["api_new_note"] = "点击新建无弹窗无跳转"
            page.screenshot(path=f"{OUT_DIR}/explore-sub-API测试-新建点击后.png", full_page=True)

    # ===== 5. 设置tab - Web 浏览器配置 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 项目详情-设置tab", flush=True)
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    page.locator(".el-tabs__item").filter(has_text="设置").first.click()
    page.wait_for_timeout(1500)
    # 浏览器配置下拉
    browser_sel = page.locator(".el-select").first
    try:
        browser_sel.click()
        page.wait_for_timeout(800)
        opts = page.locator(".el-select-dropdown__item:visible")
        opt_texts = [clean(opts.nth(k).inner_text()) for k in range(opts.count())]
        opt_texts = [o for o in opt_texts if o]
        print(f"  Web浏览器配置选项: {opt_texts}", flush=True)
        out["settings_browser_options"] = opt_texts
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception as e:
        print(f"  浏览器下拉异常: {e}", flush=True)
    # 设置tab 完整内容
    body = clean(page.inner_text("body"))[:800]
    print(f"  设置tab body: {body}", flush=True)
    # CI/CD 集成区域（设置tab内）
    cicd_btns = []
    for i in range(page.locator("button").count()):
        t = clean(page.locator("button").nth(i).inner_text())
        if t:
            cicd_btns.append(t)
    out["settings_tab_buttons"] = cicd_btns
    print(f"  设置tab按钮: {cicd_btns}", flush=True)
    page.screenshot(path=f"{OUT_DIR}/explore-sub-设置tab.png", full_page=True)

    # ===== 6. CI/CD 集成详情 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== CI/CD 集成详情", flush=True)
    page.goto(f"{BASE}/projects/{PID}/settings/ci", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    body = clean(page.inner_text("body"))[:1000]
    print(f"  CI/CD body: {body}", flush=True)
    out["cicd_body"] = body
    page.screenshot(path=f"{OUT_DIR}/explore-sub-CICD-详情.png", full_page=True)

    # ===== 7. 项目概览页统计卡片点击行为 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 概览统计卡片", flush=True)
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    stat_cards = page.locator(".stat-card, [class*='stat']")
    sc = []
    for i in range(stat_cards.count()):
        t = clean(stat_cards.nth(i).inner_text())
        cls = stat_cards.nth(i).get_attribute("class") or ""
        if t and ("stat" in cls or "card" in cls):
            sc.append({"text": t, "class": cls})
    out["overview_stat_cards"] = sc[:10]
    print(f"  概览统计卡片: {sc[:10]}", flush=True)

    browser.close()

with open(f"{OUT_DIR}/explore-final.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n[{time.time()-t0:5.1f}s] 完成，结果已写入 explore-final.json", flush=True)
