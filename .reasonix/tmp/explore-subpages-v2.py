# -*- coding: utf-8 -*-
"""遍历项目详情全部二级子页面（v2）：独立URL用goto，API Token/CI-CD用子菜单点击；记录结构+创建弹窗字段（只读）"""
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
        page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=2500)
        return
    except Exception:
        pass
    try:
        page.locator(".el-dialog__headerbtn").first.click(timeout=2500)
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

def record_dialog(page, mod, btn_text):
    try:
        dlg = get_dialog(page)
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
            inp_name = fi.locator("input").first.get_attribute("name") if fi.locator("input").count() else None
            field = {"name": label, "required": req or has_star, "controls": ctrls}
            if ph:
                field["placeholder"] = ph
            if inp_name:
                field["input_name"] = inp_name
            fields.append(field)
        dlg_btns = dlg.locator("button")
        btns = []
        for k in range(dlg_btns.count()):
            t = clean(dlg_btns.nth(k).inner_text())
            if t and t not in btns:
                btns.append(t)
        form = {"name": dlg_title, "trigger_button": btn_text, "fields": fields, "buttons": btns}
        shot = f"{OUT_DIR}/explore-sub-{mod['module']}-{btn_text}.png"
        try:
            dlg.screenshot(path=shot, timeout=5000)
            form["screenshot"] = shot
        except Exception:
            pass
        mod["forms"].append(form)
        print(f"      弹窗「{dlg_title}」字段: {[f['name'] + ('*' if f['required'] else '') for f in fields]}")
        close_dialog(page)
        page.wait_for_timeout(400)
    except Exception as e:
        mod["notes"].append(f"记录弹窗「{btn_text}」异常: {str(e)[:100]}")
        close_dialog(page)

def record_page(page, mod):
    page.wait_for_timeout(1500)
    mod["url"] = page.url
    mod["title"] = page.title()
    mod["h2"] = clean(page.locator("h2, .page-title").first.inner_text()) if page.locator("h2, .page-title").count() else ""
    mod["breadcrumb"] = clean(page.locator(".el-breadcrumb").first.inner_text()) if page.locator(".el-breadcrumb").count() else ""
    print(f"  [{mod['module']}] URL={mod['url']} H2={mod['h2']}")
    # inputs
    ins = []
    for i in range(page.locator("input").count()):
        el = page.locator("input").nth(i)
        info = {"type": el.get_attribute("type"), "placeholder": el.get_attribute("placeholder"), "class": el.get_attribute("class")}
        info = {k: v for k, v in info.items() if v}
        if info:
            ins.append(info)
    mod["inputs"] = ins
    # buttons
    btns = []
    for i in range(page.locator("button").count()):
        el = page.locator("button").nth(i)
        t = clean(el.inner_text())
        cls = el.get_attribute("class") or ""
        if t:
            btns.append({"text": t, "class": cls})
    mod["buttons"] = btns
    # selects
    sels = []
    for i in range(page.locator(".el-select").count()):
        sels.append(page.locator(".el-select").nth(i).get_attribute("class") or "")
    mod["selects"] = sels
    # table
    ths = page.locator(".el-table__header th")
    headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
    headers = [h for h in headers if h]
    rows = page.locator(".el-table__body tbody tr")
    mod["tables"] = {"headers": headers, "row_count": rows.count()}
    # pagination
    pg = page.locator(".el-pagination")
    mod["pagination"] = {"exists": pg.count() > 0, "text": clean(pg.first.inner_text()) if pg.count() else ""}
    # empty
    empty = page.locator(".el-table__empty-block, .el-empty")
    if empty.count() > 0:
        mod["notes"].append(f"空状态: {clean(empty.first.inner_text()) or '(无文本)'}")
    # row actions
    row_btns = page.locator(".el-table__body button, .el-table__body a")
    ra = []
    for i in range(row_btns.count()):
        t = clean(row_btns.nth(i).inner_text())
        if t and t not in ra:
            ra.append(t)
    mod["row_actions"] = ra
    # create buttons
    create = page.locator("button").filter(has_text=re.compile("新建|添加|创建|新增|导入|生成|Token|令牌"))
    cl = []
    for i in range(create.count()):
        t = clean(create.nth(i).inner_text())
        if t and t not in cl:
            cl.append(t)
    print(f"    按钮: {[b['text'] for b in btns]}")
    print(f"    创建类: {cl} | 表头: {headers} | 行数: {rows.count()}")
    # 打开创建弹窗
    for btn_text in dict.fromkeys(cl):
        try:
            btn = page.locator("button").filter(has_text=btn_text).first
            btn.scroll_into_view_if_needed(timeout=4000)
            btn.click(timeout=4000)
            page.wait_for_timeout(900)
            record_dialog(page, mod, btn_text)
        except Exception as e:
            mod["notes"].append(f"打开「{btn_text}」异常: {str(e)[:100]}")
            close_dialog(page)
    # screenshot
    try:
        page.screenshot(path=f"{OUT_DIR}/explore-sub-{mod['module']}.png", full_page=True, timeout=8000)
        mod["screenshot"] = f"{OUT_DIR}/explore-sub-{mod['module']}.png"
    except Exception:
        mod["screenshot"] = f"{OUT_DIR}/explore-sub-{mod['module']}.png"
    if mod["tables"]["headers"]:
        mod["features"].append("数据表格")
    if ins:
        mod["features"].append("输入框")
    if btns:
        mod["features"].append("按钮区")
    if mod["pagination"]["exists"]:
        mod["features"].append("分页")
    if sels:
        mod["features"].append("筛选下拉")

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
    print("登录后:", page.url)

    # 独立 URL 子页面
    routes = [
        ("全部用例", f"{BASE}/projects/{PID}/testcases"),
        ("Web测试", f"{BASE}/projects/{PID}/testcases?type=web"),
        ("API测试", f"{BASE}/projects/{PID}/api"),
        ("移动测试", f"{BASE}/projects/{PID}/testcases?type=mobile"),
        ("测试套件", f"{BASE}/projects/{PID}/suites"),
        ("执行记录", f"{BASE}/projects/{PID}/executions"),
        ("AI测试助手", f"{BASE}/projects/{PID}/ai-assistant"),
        ("测试报告", f"{BASE}/projects/{PID}/reports"),
        ("关键字库", f"{BASE}/projects/{PID}/keywords"),
        ("测试环境", f"{BASE}/projects/{PID}/environments"),
        ("定时任务", f"{BASE}/projects/{PID}/schedules"),
    ]
    sub_report = []
    for name, url in routes:
        print(f"\n===== {name} =====")
        mod = {"module": name, "features": [], "forms": [], "list_actions": [], "row_actions": [], "notes": []}
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            record_page(page, mod)
        except Exception as e:
            mod["notes"].append(f"页面访问异常: {str(e)[:120]}")
            print("  异常:", str(e)[:120])
        sub_report.append(mod)

    # API Token / CI/CD 集成（子菜单，SPA 视图）
    print("\n===== 返回详情页，展开设置子菜单 =====")
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)
    submenu = page.locator(".el-sub-menu__title").filter(has_text="设置")
    if submenu.count() > 0:
        submenu.first.click()
        page.wait_for_timeout(800)
    for name in ["API Token", "CI/CD 集成"]:
        print(f"\n===== {name} =====")
        mod = {"module": name, "features": [], "forms": [], "list_actions": [], "row_actions": [], "notes": []}
        try:
            item = page.locator(".el-menu .el-menu-item").filter(has_text=name)
            clicked = False
            for k in range(item.count()):
                if clean(item.nth(k).inner_text()) == name:
                    item.nth(k).click(timeout=4000)
                    clicked = True
                    break
            if not clicked:
                item.first.click(timeout=4000)
            page.wait_for_timeout(1500)
            record_page(page, mod)
        except Exception as e:
            mod["notes"].append(f"子菜单访问异常: {str(e)[:120]}")
            print("  异常:", str(e)[:120])
        sub_report.append(mod)

    browser.close()

with open(f"{OUT_DIR}/explore-subpages-v2.json", "w", encoding="utf-8") as f:
    json.dump(sub_report, f, ensure_ascii=False, indent=2)
print("\n=== 二级页面探索完成(v2) ===")
for m in sub_report:
    print(" -", m["module"], "|", m.get("url", ""), "| 创建弹窗:", [f["name"] for f in m["forms"]])
