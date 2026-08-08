# -*- coding: utf-8 -*-
"""探索项目详情页：点击项目卡片进入，记录二级导航/标签页/用例与套件模块/创建入口"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"

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
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    # 进入项目管理
    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    page.wait_for_timeout(1200)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass

    # 检查 project-card 的 DOM 结构（是否可点击/链接）
    cards = page.locator(".project-card")
    print("project-card 数量:", cards.count())
    if cards.count() > 0:
        card = cards.first
        html = card.inner_html()
        print("卡片 HTML(600字):", html[:600].replace("\n", " "))
        # 点击卡片
        card.click()
        page.wait_for_timeout(1500)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        print("\n点击卡片后 URL:", page.url)
        print("TITLE:", page.title())
        print("body 文本(1500):")
        print(page.inner_text("body")[:1500].replace("\n", " | "))
        page.screenshot(path=f"{OUT_DIR}/explore-项目详情.png", full_page=True)

        # 详情页结构：标签页/二级导航/按钮/表格
        tabs = page.locator(".el-tabs__item, .el-tabs__nav-item")
        tab_list = []
        for i in range(tabs.count()):
            t = clean(tabs.nth(i).inner_text())
            if t:
                tab_list.append(t)
        print("\n标签页:", tab_list)

        btns = page.locator("button")
        print("\n按钮:")
        for i in range(btns.count()):
            t = clean(btns.nth(i).inner_text())
            cls = btns.nth(i).get_attribute("class") or ""
            if t:
                print("   ", repr(t), cls)

        inputs = page.locator("input")
        print("\n输入框:")
        for i in range(inputs.count()):
            el = inputs.nth(i)
            print("    ", {"type": el.get_attribute("type"), "placeholder": el.get_attribute("placeholder"),
                           "class": el.get_attribute("class")})

        # 表格
        ths = page.locator(".el-table__header th")
        if ths.count() > 0:
            headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
            print("\n表头:", [h for h in headers if h])
        rows = page.locator(".el-table__body tbody tr")
        print("表格行数:", rows.count())
        if rows.count() > 0:
            row_btns = rows.first.locator("button, a")
            rb = []
            for k in range(row_btns.count()):
                t = clean(row_btns.nth(k).inner_text())
                if t:
                    rb.append(t)
            print("行内操作按钮:", rb)

        # 创建类按钮
        create = page.locator("button").filter(has_text=re.compile("新建|添加|创建|新增|用例|套件"))
        cl = []
        for i in range(create.count()):
            t = clean(create.nth(i).inner_text())
            if t:
                cl.append(t)
        print("\n创建类按钮:", dict.fromkeys(cl))

        # 尝试打开"新建用例"类弹窗记录字段（若存在）
        for btn_text in dict.fromkeys(cl):
            try:
                btn = page.locator("button").filter(has_text=btn_text).first
                btn.scroll_into_view_if_needed()
                btn.click()
                page.wait_for_timeout(1000)
                dlg = None
                for j in range(page.locator(".el-dialog").count()):
                    d = page.locator(".el-dialog").nth(j)
                    if d.is_visible():
                        dlg = d
                        break
                if dlg is None:
                    print(f"  「{btn_text}」未弹窗（可能为页面跳转，需另探）")
                    # 若跳转了，回退
                    if page.url != "http://123.56.21.178:8080/projects":
                        page.go_back()
                        page.wait_for_timeout(1000)
                    continue
                dlg_title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else btn_text
                print(f"\n  弹窗「{dlg_title}」字段:")
                f_items = dlg.locator(".el-form-item")
                for k in range(f_items.count()):
                    fi = f_items.nth(k)
                    label = clean(fi.locator(".el-form-item__label").first.inner_text())
                    req = "is-required" in (fi.get_attribute("class") or "")
                    ctrls = []
                    if fi.locator("input").count() > 0:
                        ctrls.append("text/input")
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
                    print(f"    字段 {label}: required={req} controls={ctrls} placeholder={ph!r}")
                # 弹窗内 select 选项
                sels = dlg.locator(".el-select")
                for k in range(sels.count()):
                    s = sels.nth(k)
                    try:
                        s.click()
                        page.wait_for_timeout(600)
                        opts = page.locator(".el-select-dropdown__item:visible")
                        ot = [clean(opts.nth(m).inner_text()) for m in range(opts.count())]
                        ot = [o for o in ot if o]
                        print(f"    select[{k}] 选项: {ot}")
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                    except Exception as e:
                        print(f"    select[{k}] 展开失败: {e}")
                shot = f"{OUT_DIR}/explore-项目详情-{btn_text}.png"
                try:
                    dlg.screenshot(path=shot)
                    print("  弹窗截图:", shot)
                except Exception:
                    pass
                # 取消
                try:
                    page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=3000)
                except Exception:
                    try:
                        page.locator(".el-dialog__headerbtn").first.click(timeout=3000)
                    except Exception:
                        page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"  「{btn_text}」处理异常: {e}")
                try:
                    page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=2000)
                except Exception:
                    pass

    browser.close()
    print("\n完成")
