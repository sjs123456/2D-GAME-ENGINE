# -*- coding: utf-8 -*-
"""遍历项目详情二级导航全部子页面，记录 URL/标题/按钮/输入框/表格/弹窗字段（只读）"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def wait_net(page):
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass

def get_visible_dialog(page):
    for j in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(j)
        if d.is_visible():
            return d
    return None

def close_dialog(page):
    try:
        page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=3000)
        return "cancel"
    except Exception:
        pass
    try:
        page.locator(".el-dialog__headerbtn").first.click(timeout=3000)
        return "close-x"
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
        return "esc"
    except Exception:
        return "none"

def record_dialog(page, mod, btn_text):
    dlg = get_visible_dialog(page)
    if dlg is None:
        mod["notes"].append(f"点击「{btn_text}」未发现可见弹窗")
        return
    dlg_title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else btn_text
    f_items = dlg.locator(".el-form-item")
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
        if fi.locator(".el-upload").count() > 0:
            ctrls.append("upload")
        ph = fi.locator("input").first.get_attribute("placeholder") if fi.locator("input").count() else None
        inp = fi.locator("input").first
        inp_name = inp.get_attribute("name") if inp.count() else None
        field = {"name": label, "required": req or has_star, "controls": ctrls}
        if ph:
            field["placeholder"] = ph
        if inp_name:
            field["input_name"] = inp_name
        fields.append(field)
    # 弹窗内 select 选项
    sel_options = []
    sels = dlg.locator(".el-select")
    for k in range(sels.count()):
        try:
            sels.nth(k).click()
            page.wait_for_timeout(600)
            opts = page.locator(".el-select-dropdown__item:visible")
            ot = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
            sel_options.append({"select_index": k, "options": [o for o in ot if o]})
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass
    dlg_btns = dlg.locator(".el-dialog__footer button, .el-dialog button")
    btns = []
    for k in range(dlg_btns.count()):
        t = clean(dlg_btns.nth(k).inner_text())
        if t and t not in btns:
            btns.append(t)
    form = {"name": dlg_title, "trigger_button": btn_text, "fields": fields, "select_options": sel_options, "buttons": btns}
    shot = f"{OUT_DIR}/explore-sub-{mod['module']}-{btn_text}.png"
    try:
        dlg.screenshot(path=shot)
        form["screenshot"] = shot
    except Exception:
        pass
    mod["forms"].append(form)
    print(f"    弹窗「{dlg_title}」字段 {len(fields)} 个: {[f['name'] for f in fields]}")
    close_dialog(page)
    page.wait_for_timeout(500)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(15000)
    page.on("dialog", lambda d: d.accept())

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
    wait_net(page)
    page.wait_for_timeout(800)

    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    page.wait_for_timeout(1200)
    wait_net(page)
    page.locator(".project-card").first.click()
    page.wait_for_timeout(1500)
    wait_net(page)
    print("项目详情:", page.url)

    # 所有导航项（跳过主导航前 3 个：仪表盘/项目管理/设备管理）
    nav = page.locator(".el-menu .el-menu-item")
    all_names = []
    for i in range(nav.count()):
        t = clean(nav.nth(i).inner_text())
        if t:
            all_names.append(t)
    print("全部导航项:", all_names)
    main_nav = ["仪表盘", "项目管理", "设备管理"]
    sub_names = [n for n in all_names if n not in main_nav]
    print("二级导航项:", sub_names)

    sub_report = []
    for name in sub_names:
        print(f"\n===== 二级页面: {name} =====")
        mod = {"module": name, "url": "", "title": "", "h2": "", "features": [], "cards": [],
               "inputs": [], "buttons": [], "selects": [], "tables": {}, "pagination": {"exists": False},
               "forms": [], "list_actions": [], "row_actions": [], "screenshot": "", "notes": []}
        try:
            # 点击导航项
            item = page.locator(".el-menu .el-menu-item").filter(has_text=name)
            # 精确匹配：取文本完全相等的
            clicked = False
            for k in range(item.count()):
                if clean(item.nth(k).inner_text()) == name:
                    item.nth(k).scroll_into_view_if_needed()
                    item.nth(k).click()
                    clicked = True
                    break
            if not clicked:
                item.first.click()
            page.wait_for_timeout(1500)
            wait_net(page)
            page.wait_for_timeout(300)
        except Exception as e:
            print("  导航点击失败:", e)
            mod["notes"].append(f"导航点击失败: {e}")
            sub_report.append(mod)
            continue

        mod["url"] = page.url
        mod["title"] = page.title()
        mod["h2"] = clean(page.locator("h2, .page-title").first.inner_text()) if page.locator("h2, .page-title").count() else ""
        breadcrumb = clean(page.locator(".el-breadcrumb").first.inner_text()) if page.locator(".el-breadcrumb").count() else ""
        mod["breadcrumb"] = breadcrumb
        print(f"  URL={mod['url']} H2={mod['h2']} 面包屑={breadcrumb}")

        # 输入框
        inputs = []
        for i in range(page.locator("input").count()):
            el = page.locator("input").nth(i)
            info = {"type": el.get_attribute("type"), "placeholder": el.get_attribute("placeholder"),
                    "class": el.get_attribute("class")}
            info = {k: v for k, v in info.items() if v}
            if info:
                inputs.append(info)
        mod["inputs"] = inputs
        # 按钮
        btns = []
        for i in range(page.locator("button").count()):
            el = page.locator("button").nth(i)
            t = clean(el.inner_text())
            cls = el.get_attribute("class") or ""
            if t:
                btns.append({"text": t, "class": cls})
        mod["buttons"] = btns
        # 下拉
        selects = []
        for i in range(page.locator(".el-select").count()):
            selects.append(page.locator(".el-select").nth(i).get_attribute("class") or "")
        mod["selects"] = selects
        # 表格
        ths = page.locator(".el-table__header th")
        headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
        headers = [h for h in headers if h]
        rows = page.locator(".el-table__body tbody tr")
        mod["tables"] = {"headers": headers, "row_count": rows.count()}
        # 分页
        pg = page.locator(".el-pagination")
        if pg.count() > 0:
            mod["pagination"] = {"exists": True, "text": clean(pg.first.inner_text())}
        # 空状态
        empty = page.locator(".el-table__empty-block, .el-empty")
        if empty.count() > 0:
            t = clean(empty.first.inner_text())
            mod["notes"].append(f"空状态: {t or '(无文本)'}")
        # 行内操作
        row_btns = page.locator(".el-table__body button, .el-table__body a")
        ra = []
        for i in range(row_btns.count()):
            t = clean(row_btns.nth(i).inner_text())
            if t and t not in ra:
                ra.append(t)
        mod["row_actions"] = ra
        # 创建类按钮
        create = page.locator("button").filter(has_text=re.compile("新建|添加|创建|新增|导入|生成"))
        cl = []
        for i in range(create.count()):
            t = clean(create.nth(i).inner_text())
            if t and t not in cl:
                cl.append(t)
        print("  按钮:", [b["text"] for b in btns])
        print("  创建类按钮:", cl)
        print("  表头:", headers, "行数:", rows.count())

        # 打开创建类弹窗
        for btn_text in dict.fromkeys(cl):
            try:
                btn = page.locator("button").filter(has_text=btn_text).first
                btn.scroll_into_view_if_needed(timeout=5000)
                btn.click()
                page.wait_for_timeout(1000)
                record_dialog(page, mod, btn_text)
            except Exception as e:
                mod["notes"].append(f"打开「{btn_text}」异常: {str(e)[:120]}")
                close_dialog(page)

        # 截图
        try:
            page.screenshot(path=f"{OUT_DIR}/explore-sub-{name}.png", full_page=True)
            mod["screenshot"] = f"{OUT_DIR}/explore-sub-{name}.png"
        except Exception:
            pass

        # features
        if headers:
            mod["features"].append("数据表格")
        if inputs:
            mod["features"].append("输入框")
        if btns:
            mod["features"].append("按钮区")
        if mod["pagination"]["exists"]:
            mod["features"].append("分页")
        if selects:
            mod["features"].append("筛选下拉")
        sub_report.append(mod)

    browser.close()

with open(f"{OUT_DIR}/explore-subpages.json", "w", encoding="utf-8") as f:
    json.dump(sub_report, f, ensure_ascii=False, indent=2)
print("\n=== 二级页面探索完成 ===")
for m in sub_report:
    print(" -", m["module"], "|", m["url"], "| 按钮:", [b["text"] for b in m["buttons"][:8]], "| 表格行:", m["tables"]["row_count"])
