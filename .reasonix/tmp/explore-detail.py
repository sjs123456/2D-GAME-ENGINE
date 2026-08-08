# -*- coding: utf-8 -*-
"""补充探索：新建项目弹窗字段、设备管理按钮/下拉选项、仪表盘图表结构、顶部导航、列表空状态"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"
BASE = "http://123.56.21.178:8080"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def visible_dialog(page):
    for j in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(j)
        if d.is_visible():
            return d
    return None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(15000)
    page.on("dialog", lambda d: (print("[DIALOG]", d.message), d.accept()))

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    start = time.time()
    while time.time() - start < 15:
        page.wait_for_timeout(400)
        if page.url != LOGIN_URL:
            break
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1000)
    print("登录后:", page.url)

    detail = {}

    # ========== 1. 顶部导航 / 用户区 ==========
    print("\n=== 顶部导航/用户区 ===")
    header = page.locator(".el-header, header, .layout-header")
    for i in range(header.count()):
        h = header.nth(i)
        print(f"  header[{i}] 文本: {clean(h.inner_text())[:200]}")
        # header 内的链接/按钮
        for tag in ["a", "button", ".el-dropdown", ".el-avatar"]:
            els = h.locator(tag)
            for k in range(els.count()):
                e = els.nth(k)
                t = clean(e.inner_text())
                href = e.get_attribute("href") or ""
                cls = e.get_attribute("class") or ""
                print(f"    {tag}: text={t!r} href={href!r} class={cls!r}")
    # 用户下拉菜单（admin123）
    user_el = page.locator(".el-dropdown, .user-info, [class*='user']").first
    try:
        if user_el.count() > 0:
            user_el.click()
            page.wait_for_timeout(700)
            dd_items = page.locator(".el-dropdown-menu__item")
            dd = []
            for k in range(dd_items.count()):
                dd.append(clean(dd_items.nth(k).inner_text()))
            detail["user_dropdown"] = dd
            print("  用户下拉菜单项:", dd)
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
    except Exception as e:
        print("  用户下拉异常:", e)

    # ========== 2. 仪表盘详情 ==========
    print("\n=== 仪表盘 ===")
    page.locator(".el-menu .el-menu-item").filter(has_text="仪表盘").first.click()
    page.wait_for_timeout(1200)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    # 统计卡片结构
    stats = page.locator(".chart-row, [class*='stat'], [class*='card'], .el-card")
    stat_list = []
    for i in range(min(stats.count(), 20)):
        el = stats.nth(i)
        t = clean(el.inner_text())[:100]
        cls = el.get_attribute("class") or ""
        if t or cls:
            stat_list.append({"class": cls, "text": t})
    detail["dashboard_stats"] = stat_list
    print("  统计卡片区元素:")
    for s in stat_list:
        print("   ", s)
    # canvas / echarts
    canvas = page.locator("canvas")
    print(f"  canvas 数量: {canvas.count()}")
    for i in range(canvas.count()):
        c = canvas.nth(i)
        print(f"    canvas[{i}] id={c.get_attribute('id')!r} class={c.get_attribute('class')!r} visible={c.is_visible()}")
    # chart-row 内部
    cr = page.locator(".chart-row")
    for i in range(cr.count()):
        inner = cr.nth(i).inner_html()
        print(f"  chart-row[{i}] 长度={len(inner)}")
        print("    ", inner[:300].replace("\n", " "))
    page.screenshot(path=f"{OUT_DIR}/explore-仪表盘-detail.png", full_page=True)

    # ========== 3. 项目管理 - 新建项目弹窗 ==========
    print("\n=== 项目管理 - 新建项目弹窗 ===")
    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    page.wait_for_timeout(1200)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    # 列表空状态
    empty = page.locator(".el-table__empty-block, .el-empty")
    if empty.count() > 0:
        print("  列表空状态:", clean(empty.first.inner_text()))
    # 表格结构
    tbl = page.locator(".el-table")
    if tbl.count() > 0:
        ths = tbl.first.locator(".el-table__header th")
        headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
        headers = [h for h in headers if h]
        print("  表头:", headers)
        detail["project_table_headers"] = headers
        trs = tbl.first.locator(".el-table__body tbody tr")
        print("  数据行数:", trs.count())
        if trs.count() > 0:
            detail["project_row_count"] = trs.count()
            cells = [clean(trs.first.locator("td").nth(k).inner_text()) for k in range(trs.first.locator("td").count())]
            print("  首行单元格:", cells)

    # 打开新建项目
    page.locator("button:has-text('新建项目')").first.click()
    page.wait_for_timeout(1000)
    dlg = visible_dialog(page)
    if dlg:
        dlg_title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else "新建项目"
        print("  弹窗标题:", dlg_title)
        detail["project_dialog_title"] = dlg_title
        # 逐个 form-item
        form_items = dlg.locator(".el-form-item")
        fields = []
        for k in range(form_items.count()):
            fi = form_items.nth(k)
            label = clean(fi.locator(".el-form-item__label").first.inner_text())
            req = "is-required" in (fi.get_attribute("class") or "")
            # 星号检查
            try:
                html = fi.locator(".el-form-item__label").first.inner_html()
                has_star = "*" in html
            except Exception:
                has_star = req
            # 控件
            ctrls = []
            if fi.locator("input[type='text'], input:not([type])").count() > 0:
                ctrls.append("text")
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
            if fi.locator(".el-upload").count() > 0:
                ctrls.append("upload")
            ph = fi.locator("input").first.get_attribute("placeholder") if fi.locator("input").count() else None
            field = {"name": label, "required": req or has_star, "controls": ctrls}
            if ph:
                field["placeholder"] = ph
            # 输入框 name/id
            inp = fi.locator("input").first
            if inp.count() > 0:
                nm = inp.get_attribute("name") or ""
                fid = inp.get_attribute("id") or ""
                if nm:
                    field["input_name"] = nm
                if fid:
                    field["input_id"] = fid
            fields.append(field)
            print(f"    字段: {field}")
        detail["project_dialog_fields"] = fields
        # 弹窗按钮
        dlg_btns = dlg.locator(".el-dialog__footer button")
        dlg_buttons = []
        for k in range(dlg_btns.count()):
            t = clean(dlg_btns.nth(k).inner_text())
            cls = dlg_btns.nth(k).get_attribute("class") or ""
            if t:
                dlg_buttons.append({"text": t, "class": cls})
        detail["project_dialog_buttons"] = dlg_buttons
        print("  弹窗按钮:", dlg_buttons)
        try:
            dlg.screenshot(path=f"{OUT_DIR}/explore-项目管理-新建项目.png")
            detail["project_dialog_screenshot"] = f"{OUT_DIR}/explore-项目管理-新建项目.png"
        except Exception as e:
            print("  弹窗截图异常:", e)
        # 取消关闭
        try:
            page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            try:
                page.locator(".el-dialog__headerbtn").first.click(timeout=3000)
                page.wait_for_timeout(500)
            except Exception:
                page.keyboard.press("Escape")
    else:
        print("  未找到可见弹窗!")
        page.screenshot(path=f"{OUT_DIR}/explore-project-dialog-missing.png")

    # ========== 4. 设备管理 ==========
    print("\n=== 设备管理 ===")
    page.locator(".el-menu .el-menu-item").filter(has_text="设备管理").first.click()
    page.wait_for_timeout(1200)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    # 所有按钮（含无文本图标按钮）
    btns = page.locator("button")
    print(f"  button 数量: {btns.count()}")
    btn_info = []
    for k in range(btns.count()):
        el = btns.nth(k)
        t = clean(el.inner_text())
        cls = el.get_attribute("class") or ""
        title = el.get_attribute("title") or ""
        aria = el.get_attribute("aria-label") or ""
        icon = el.locator("i").first.get_attribute("class") if el.locator("i").count() else ""
        btn_info.append({"text": t, "class": cls, "title": title, "aria": aria, "icon": icon})
        print(f"    button[{k}] text={t!r} class={cls!r} title={title!r} aria={aria!r} icon={icon!r}")
    detail["device_buttons"] = btn_info
    # 筛选下拉框选项
    selects = page.locator(".el-select.filter-item")
    filter_info = []
    for k in range(selects.count()):
        sel = selects.nth(k)
        # 尝试读取 label（.el-form-item__label 或前置文本）
        try:
            sel.click()
            page.wait_for_timeout(700)
            opts = page.locator(".el-select-dropdown__item:visible")
            opt_texts = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
            opt_texts = [o for o in opt_texts if o]
            filter_info.append({"index": k, "options": opt_texts})
            print(f"    下拉[{k}] 选项: {opt_texts}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        except Exception as e:
            print(f"    下拉[{k}] 展开异常: {e}")
            filter_info.append({"index": k, "error": str(e)})
    detail["device_filters"] = filter_info
    # 设备表格/卡片
    dev_cards = page.locator(".device-card, [class*='device'], .el-card")
    dev_list = []
    for k in range(min(dev_cards.count(), 15)):
        c = dev_cards.nth(k)
        t = clean(c.inner_text())[:150]
        cls = c.get_attribute("class") or ""
        if t:
            dev_list.append({"class": cls, "text": t})
    detail["device_cards"] = dev_list
    print("  设备卡片:", dev_list)
    page.screenshot(path=f"{OUT_DIR}/explore-设备管理-detail.png", full_page=True)

    # ========== 5. 退出登录入口（只观察） ==========
    print("\n=== 退出登录入口 ===")
    logout = page.locator("button:has-text('退出'), a:has-text('退出'), span:has-text('退出登录')")
    if logout.count() > 0:
        print("  发现退出入口:", clean(logout.first.inner_text()))
        detail["logout_found"] = True
    else:
        print("  页面未见明显退出按钮（可能在用户下拉中）")
        detail["logout_found"] = False

    browser.close()

# 落盘
path = f"{OUT_DIR}/explore-detail.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(detail, f, ensure_ascii=False, indent=2)
print("\n补充探索结果已写入:", path)
