# -*- coding: utf-8 -*-
"""补充探测2（健壮版）：定时任务弹窗、API测试新建、设置tab浏览器配置、CI/CD详情、概览统计卡片"""
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

def safe_field(fi):
    """安全提取单个 form-item 字段"""
    try:
        label = clean(fi.locator(".el-form-item__label").first.inner_text())
    except Exception:
        label = ""
    req = "is-required" in (fi.get_attribute("class") or "")
    ctrls = []
    try:
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
    except Exception:
        pass
    ph = None
    try:
        if fi.locator("input").count() > 0:
            ph = fi.locator("input").first.get_attribute("placeholder")
    except Exception:
        pass
    field = {"name": label, "required": req, "controls": ctrls}
    if ph:
        field["placeholder"] = ph
    return field

def dump_form(page, scope):
    fields = []
    try:
        f_items = scope.locator(".el-form-item")
        n = f_items.count()
        for k in range(n):
            fields.append(safe_field(f_items.nth(k)))
    except Exception:
        pass
    return fields

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

    # ===== 1. 定时任务弹窗 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 定时任务-新建定时任务弹窗", flush=True)
    page.goto(f"{BASE}/projects/{PID}/schedules", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建定时任务')").first.click()
    page.wait_for_timeout(1500)
    dlg = get_dialog(page)
    if dlg:
        title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else "新建定时任务"
        fields = dump_form(page, dlg)
        dlg_btns = []
        for i in range(dlg.locator("button").count()):
            t = clean(dlg.locator("button").nth(i).inner_text())
            if t and t not in dlg_btns:
                dlg_btns.append(t)
        out["schedule_dialog"] = {"name": title, "fields": fields, "buttons": dlg_btns}
        print(f"  弹窗「{title}」字段: {fields}", flush=True)
        print(f"  弹窗按钮: {dlg_btns}", flush=True)
        try:
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-新建定时任务弹窗.png", timeout=5000)
        except Exception:
            pass
        close_dialog(page)
        page.wait_for_timeout(500)
    else:
        print("  未找到弹窗", flush=True)
        out["schedule_dialog"] = "未找到弹窗"

    # ===== 2. API测试-新建 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== API测试-新建", flush=True)
    page.goto(f"{BASE}/projects/{PID}/api", wait_until="domcontentloaded", timeout=15000)
    time.sleep(1.5)
    page.locator("button:has-text('新建')").first.click()
    page.wait_for_timeout(2000)
    print(f"  点击后 URL: {page.url}", flush=True)
    out["api_new_after_click_url"] = page.url
    if page.url != f"{BASE}/projects/{PID}/api":
        page.wait_for_timeout(1200)
        body = clean(page.inner_text("body"))[:500]
        print(f"  body: {body}", flush=True)
        fields = dump_form(page, page)
        out["api_new_page"] = {"url": page.url, "h2": clean(page.locator("h2").first.inner_text()) if page.locator("h2").count() else "", "fields": fields}
        print(f"  API新建页字段: {fields}", flush=True)
        page.screenshot(path=f"{OUT_DIR}/explore-sub-API新建页面.png", full_page=True)
        page.go_back(timeout=5000)
        page.wait_for_timeout(1000)
    else:
        dlg = get_dialog(page)
        if dlg:
            fields = dump_form(page, dlg)
            out["api_new_dialog"] = fields
            print(f"  API新建弹窗字段: {fields}", flush=True)
            dlg.screenshot(path=f"{OUT_DIR}/explore-sub-API新建弹窗.png")
            close_dialog(page)
        else:
            print("  无跳转无弹窗", flush=True)
            out["api_new_note"] = "点击新建无弹窗无跳转"
            page.screenshot(path=f"{OUT_DIR}/explore-sub-API测试-新建点击后.png", full_page=True)

    # ===== 3. 设置tab - Web 浏览器配置 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 项目详情-设置tab浏览器配置", flush=True)
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    page.locator(".el-tabs__item").filter(has_text="设置").first.click()
    page.wait_for_timeout(1500)
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
        print(f"  浏览器下拉异常: {str(e)[:120]}", flush=True)
    body = clean(page.inner_text("body"))[:900]
    print(f"  设置tab body: {body}", flush=True)
    out["settings_tab_body"] = body
    page.screenshot(path=f"{OUT_DIR}/explore-sub-设置tab.png", full_page=True)

    # ===== 4. CI/CD 集成详情 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== CI/CD 集成详情", flush=True)
    page.goto(f"{BASE}/projects/{PID}/settings/ci", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    body = clean(page.inner_text("body"))[:1100]
    print(f"  CI/CD body: {body}", flush=True)
    out["cicd_body"] = body
    page.screenshot(path=f"{OUT_DIR}/explore-sub-CICD-详情.png", full_page=True)

    # ===== 5. 概览统计卡片 =====
    print(f"\n[{time.time()-t0:5.1f}s] ==== 概览统计卡片", flush=True)
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    stat_cards = page.locator(".stat-card")
    sc = []
    for i in range(stat_cards.count()):
        t = clean(stat_cards.nth(i).inner_text())
        if t:
            sc.append(t)
    out["overview_stat_cards"] = sc
    print(f"  概览统计卡片: {sc}", flush=True)
    # 概览详情表格
    detail_rows = page.locator(".detail-item, [class*='detail']")
    dr = []
    for i in range(min(detail_rows.count(), 15)):
        t = clean(detail_rows.nth(i).inner_text())
        if t:
            dr.append(t)
    out["overview_details"] = dr
    print(f"  概览详情项: {dr}", flush=True)

    browser.close()

with open(f"{OUT_DIR}/explore-final2.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n[{time.time()-t0:5.1f}s] 完成，结果已写入 explore-final2.json", flush=True)
