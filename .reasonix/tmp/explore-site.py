# -*- coding: utf-8 -*-
"""全站探索：登录后遍历主导航，记录页面结构、表单字段、列表操作、弹窗字段（只读，不提交）"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"
BASE = "http://123.56.21.178:8080"

report = []
visit_log = []

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def dump_inputs(page, scope=None):
    res = []
    loc = scope or page.locator("input")
    for i in range(loc.count()):
        el = loc.nth(i)
        info = {"type": el.get_attribute("type"), "name": el.get_attribute("name"),
                "id": el.get_attribute("id"), "placeholder": el.get_attribute("placeholder"),
                "class": el.get_attribute("class")}
        info = {k: v for k, v in info.items() if v}
        if info:
            res.append(info)
    return res

def dump_buttons(page, scope=None):
    res = []
    loc = scope or page.locator("button")
    for i in range(loc.count()):
        el = loc.nth(i)
        text = clean(el.inner_text())
        cls = el.get_attribute("class") or ""
        if text:
            res.append({"text": text, "class": cls})
    return res

def dump_table(page, scope=None):
    """记录表格：表头列名、行数"""
    info = {"headers": [], "row_count": 0, "source": ""}
    loc = scope or page
    # Element UI 表格
    ths = loc.locator(".el-table__header th")
    if ths.count() > 0:
        info["source"] = "el-table"
        for i in range(ths.count()):
            t = clean(ths.nth(i).inner_text())
            if t:
                info["headers"].append(t)
    else:
        # 原生 table
        ths2 = loc.locator("table thead th")
        if ths2.count() > 0:
            info["source"] = "html-table"
            for i in range(ths2.count()):
                t = clean(ths2.nth(i).inner_text())
                if t:
                    info["headers"].append(t)
    # 行数
    rows = loc.locator(".el-table__body tbody tr")
    if rows.count() > 0:
        info["row_count"] = rows.count()
    else:
        rows2 = loc.locator("table tbody tr")
        if rows2.count() > 0:
            info["row_count"] = rows2.count()
    return info

def dump_selects(page, scope=None):
    res = []
    loc = scope or page.locator(".el-select")
    for i in range(loc.count()):
        el = loc.nth(i)
        ph = el.locator(".el-input__inner").first.get_attribute("placeholder") if el.locator(".el-input__inner").count() else None
        res.append({"placeholder": ph, "class": el.get_attribute("class") or ""})
    return res

def dump_pagination(page):
    info = {}
    pg = page.locator(".el-pagination")
    if pg.count() > 0:
        info["exists"] = True
        info["text"] = clean(pg.first.inner_text())
    else:
        info["exists"] = False
    return info

def dump_form_items(page, scope=None):
    """记录 el-form-item：label + 控件类型 + 必填星号"""
    items = []
    loc = scope or page.locator(".el-form-item")
    for i in range(loc.count()):
        el = loc.nth(i)
        label_el = el.locator(".el-form-item__label")
        label = clean(label_el.inner_text()) if label_el.count() else ""
        # 必填：label 前有红色星号（is-required class 或在 .el-form-item__label 内 *）
        required = "is-required" in (el.get_attribute("class") or "")
        star = "*" in (el.locator(".el-form-item__label").inner_html() if label_el.count() else "") if False else False
        # 控件类型
        ctrl = {"input": el.locator("input").count(), "textarea": el.locator("textarea").count(),
                "select": el.locator(".el-select").count(), "radio": el.locator(".el-radio").count(),
                "checkbox": el.locator(".el-checkbox").count(), "switch": el.locator(".el-switch").count(),
                "date": el.locator(".el-date-editor").count(), "upload": el.locator(".el-upload").count()}
        ctrl_type = [k for k, v in ctrl.items() if v > 0]
        ph = el.locator("input").first.get_attribute("placeholder") if el.locator("input").count() else None
        tip = clean(el.locator(".el-form-item__error").inner_text()) if el.locator(".el-form-item__error").count() else None
        items.append({"label": label, "required": required, "controls": ctrl_type,
                      "placeholder": ph, "tip": tip})
    return items

def close_dialog(page):
    """关闭当前可见弹窗：优先点取消，其次右上角 X，最后 ESC"""
    # 取消按钮
    cancel_btns = page.locator(".el-dialog__footer button:has-text('取消')")
    if cancel_btns.count() > 0:
        try:
            cancel_btns.first.scroll_into_view_if_needed()
            cancel_btns.first.click(timeout=3000)
            page.wait_for_timeout(500)
            return "cancel"
        except Exception:
            pass
    # 右上角 X
    close = page.locator(".el-dialog__headerbtn")
    if close.count() > 0:
        try:
            close.first.click(timeout=3000)
            page.wait_for_timeout(500)
            return "close-x"
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        return "esc"
    except Exception:
        return "none"

def visible_dialog_text(page):
    for i in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(i)
        if d.is_visible():
            return clean(d.inner_text())[:600]
    return ""

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

    # ---------- 登录 ----------
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
    print("登录后 URL:", page.url, "TITLE:", page.title())

    # ---------- 获取菜单 ----------
    menu_items = page.locator(".el-menu .el-menu-item")
    menu_names = []
    for i in range(menu_items.count()):
        t = clean(menu_items.nth(i).inner_text())
        if t:
            menu_names.append(t)
    print("主导航菜单:", menu_names)

    # ---------- 遍历每个菜单 ----------
    for name in menu_names:
        print(f"\n===== 进入模块: {name} =====")
        try:
            mi = page.locator(".el-menu .el-menu-item").filter(has_text=name).first
            mi.scroll_into_view_if_needed()
            mi.click()
            page.wait_for_timeout(1200)
            try:
                page.wait_for_load_state("networkidle", timeout=6000)
            except Exception:
                pass
        except Exception as e:
            print("  点击菜单失败:", e)
            continue

        url = page.url
        title = page.title()
        h2 = clean(page.locator("h2").first.inner_text()) if page.locator("h2").count() else ""
        breadcrumb = clean(page.locator(".el-breadcrumb").first.inner_text()) if page.locator(".el-breadcrumb").count() else ""
        print(f"  URL={url} TITLE={title} H2={h2} 面包屑={breadcrumb}")

        mod = {
            "module": name,
            "url": url,
            "title": title,
            "h2": h2,
            "breadcrumb": breadcrumb,
            "features": [],
            "cards": [],
            "charts": [],
            "inputs": dump_inputs(page),
            "buttons": dump_buttons(page),
            "selects": dump_selects(page),
            "tables": dump_table(page),
            "pagination": dump_pagination(page),
            "forms": [],
            "list_actions": [],
            "row_actions": [],
            "screenshot": f"{OUT_DIR}/explore-{name}.png",
            "notes": [],
        }
        page.screenshot(path=f"{OUT_DIR}/explore-{name}.png", full_page=True)

        # 统计卡片
        cards = page.locator(".el-card")
        card_texts = []
        for i in range(cards.count()):
            t = clean(cards.nth(i).inner_text())
            if t:
                card_texts.append(t)
        mod["cards"] = card_texts

        # 图表 canvas / echarts
        charts = page.locator("canvas, .echarts, [id*='chart'], [class*='chart']")
        chart_info = []
        for i in range(min(charts.count(), 20)):
            el = charts.nth(i)
            tag = el.evaluate("e => e.tagName")
            cid = el.get_attribute("id") or ""
            cls = el.get_attribute("class") or ""
            visible = el.is_visible()
            chart_info.append({"tag": tag, "id": cid, "class": cls, "visible": visible})
        mod["charts"] = chart_info
        if chart_info:
            mod["features"].append("图表组件")

        # 空状态提示
        empty = page.locator(".el-empty, .el-table__empty-block")
        if empty.count() > 0:
            t = clean(empty.first.inner_text())
            mod["notes"].append(f"空状态提示: {t or '(无文本)'}")

        # 行内操作按钮（表格内的按钮）
        row_btns = page.locator(".el-table__body tbody button, .el-table__body tbody a, .el-table__body .el-button")
        row_actions = []
        seen = set()
        for i in range(row_btns.count()):
            t = clean(row_btns.nth(i).inner_text())
            if t and t not in seen:
                seen.add(t)
                row_actions.append(t)
        mod["row_actions"] = row_actions

        # 页面级"新建/添加/创建"按钮
        create_btns = page.locator("button").filter(has_text=re.compile("新建|添加|创建|新增|导入"))
        create_list = []
        for i in range(create_btns.count()):
            t = clean(create_btns.nth(i).inner_text())
            if t:
                create_list.append(t)
        print("  创建类按钮:", create_list)

        # 对每个创建按钮打开弹窗，记录字段
        for btn_text in dict.fromkeys(create_list):
            try:
                btn = page.locator("button").filter(has_text=btn_text).first
                btn.scroll_into_view_if_needed()
                btn.click()
                page.wait_for_timeout(900)
                # 查找可见弹窗
                dlg = None
                for j in range(page.locator(".el-dialog").count()):
                    d = page.locator(".el-dialog").nth(j)
                    if d.is_visible():
                        dlg = d
                        break
                if dlg is None:
                    dlg = page.locator(".el-drawer").filter(lambda e: e.is_visible()).first if False else None
                    for j in range(page.locator(".el-drawer").count()):
                        d = page.locator(".el-drawer").nth(j)
                        if d.is_visible():
                            dlg = d
                            break
                if dlg is None:
                    mod["notes"].append(f"点击「{btn_text}」未发现可见弹窗")
                    close_dialog(page)
                    continue
                dlg_title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else btn_text
                form_items = dump_form_items(page, dlg)
                dlg_inputs = dump_inputs(page, dlg.locator("input"))
                dlg_selects = dump_selects(page, dlg)
                frm = {
                    "name": dlg_title or btn_text,
                    "trigger_button": btn_text,
                    "fields": form_items,
                    "inputs": dlg_inputs,
                    "selects": dlg_selects,
                }
                mod["forms"].append(frm)
                shot = f"{OUT_DIR}/explore-{name}-{btn_text}.png"
                try:
                    dlg.screenshot(path=shot)
                    frm["screenshot"] = shot
                except Exception:
                    frm["screenshot"] = None
                print(f"  弹窗「{frm['name']}」字段数: {len(form_items)} 截图: {shot}")
                close_dialog(page)
            except Exception as e:
                mod["notes"].append(f"打开「{btn_text}」弹窗异常: {e}")
                close_dialog(page)

        # 列表操作（搜索/筛选等）
        search_inputs = page.locator("input[placeholder*='搜索'], input[placeholder*='筛选'], input[placeholder*='关键字'], input[placeholder*='名称'], input[placeholder*='查询']")
        if search_inputs.count() > 0:
            mod["list_actions"].append("搜索输入框")
        if mod["pagination"].get("exists"):
            mod["list_actions"].append("分页")
        if mod["buttons"]:
            mod["list_actions"].append("页面按钮: " + ", ".join(b["text"] for b in mod["buttons"][:12]))
        # features 汇总
        if mod["cards"]:
            mod["features"].append("统计卡片")
        if mod["tables"].get("headers"):
            mod["features"].append("数据表格")
        if search_inputs.count() > 0:
            mod["features"].append("搜索/筛选")

        report.append(mod)
        visit_log.append({"module": name, "url": url, "title": title})

    browser.close()

# ---------- 落盘 ----------
report_path = f"{OUT_DIR}/explore-report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("\n=== 探索完成 ===")
print("报告已写入:", report_path)
for v in visit_log:
    print(" -", v["module"], "|", v["url"], "|", v["title"])
