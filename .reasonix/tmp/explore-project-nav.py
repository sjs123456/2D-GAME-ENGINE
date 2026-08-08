# -*- coding: utf-8 -*-
"""探索项目详情二级导航：全部用例/测试套件/执行记录/AI测试助手/测试报告/关键字库/测试环境/设置/定时任务 + 编辑弹窗 + CI/CD弹窗"""
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

    # 进入项目管理 → 点击项目卡片
    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    page.wait_for_timeout(1200)
    wait_net(page)
    page.locator(".project-card").first.click()
    page.wait_for_timeout(1500)
    wait_net(page)
    print("项目详情 URL:", page.url)

    out = {"project_detail_url": page.url}

    # ===== 二级导航结构 =====
    print("\n=== 二级导航结构 ===")
    # 侧边项目导航
    for sel in [".project-nav", ".sub-nav", ".el-menu", "aside", "nav", "[class*='nav']", "[class*='side']"]:
        loc = page.locator(sel)
        for i in range(loc.count()):
            t = clean(loc.nth(i).inner_text())[:400]
            if "全部用例" in t or "测试套件" in t or "AI" in t:
                print(f"  容器 {sel}[{i}]: {t}")
    # 二级导航里的链接
    links = page.locator("a")
    sub_links = []
    for i in range(links.count()):
        el = links.nth(i)
        href = el.get_attribute("href") or ""
        t = clean(el.inner_text())
        if t and href:
            sub_links.append({"text": t, "href": href})
    print("  详情页 a 链接:")
    for s in sub_links:
        print("   ", s)
    out["detail_links"] = sub_links

    # 二级导航项（div/li 可点击）
    nav_items = page.locator(".el-menu-item, .project-nav-item, [class*='nav-item'], [class*='menu-item'], .el-menu li")
    nav_list = []
    for i in range(nav_items.count()):
        t = clean(nav_items.nth(i).inner_text())
        if t:
            nav_list.append(t)
    print("  导航项文本:", nav_list)

    # ===== 概览页 - 编辑弹窗 =====
    print("\n=== 编辑项目弹窗 ===")
    edit_btn = page.locator("button:has-text('编辑')").first
    try:
        edit_btn.scroll_into_view_if_needed()
        edit_btn.click()
        page.wait_for_timeout(1000)
        dlg = None
        for j in range(page.locator(".el-dialog").count()):
            d = page.locator(".el-dialog").nth(j)
            if d.is_visible():
                dlg = d
                break
        if dlg:
            print("  弹窗标题:", clean(dlg.locator(".el-dialog__title").first.inner_text()))
            f_items = dlg.locator(".el-form-item")
            fields = []
            for k in range(f_items.count()):
                fi = f_items.nth(k)
                label = clean(fi.locator(".el-form-item__label").first.inner_text())
                req = "is-required" in (fi.get_attribute("class") or "")
                ph = fi.locator("input").first.get_attribute("placeholder") if fi.locator("input").count() else None
                val = fi.locator("input").first.input_value() if fi.locator("input").count() else None
                ta = clean(fi.locator("textarea").first.input_value()) if fi.locator("textarea").count() else None
                fields.append({"name": label, "required": req, "placeholder": ph, "prefill_value": val or ta})
                print(f"    字段 {label}: required={req} placeholder={ph!r} 预填值={val or ta!r}")
            out["edit_project_dialog_fields"] = fields
            dlg.screenshot(path=f"{OUT_DIR}/explore-项目详情-编辑.png")
            try:
                page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=3000)
            except Exception:
                try:
                    page.locator(".el-dialog__headerbtn").first.click(timeout=3000)
                except Exception:
                    page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        else:
            print("  未找到编辑弹窗")
    except Exception as e:
        print("  编辑弹窗异常:", e)

    # ===== 管理 CI/CD 配置弹窗 =====
    print("\n=== CI/CD 配置弹窗 ===")
    try:
        cicd = page.locator("button:has-text('管理 CI/CD 配置')").first
        cicd.scroll_into_view_if_needed()
        cicd.click()
        page.wait_for_timeout(1000)
        dlg = None
        for j in range(page.locator(".el-dialog").count()):
            d = page.locator(".el-dialog").nth(j)
            if d.is_visible():
                dlg = d
                break
        if dlg:
            print("  弹窗标题:", clean(dlg.locator(".el-dialog__title").first.inner_text()))
            print("  弹窗内容:", clean(dlg.inner_text())[:500])
            dlg.screenshot(path=f"{OUT_DIR}/explore-项目详情-CICD.png")
            try:
                page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=3000)
            except Exception:
                try:
                    page.locator(".el-dialog__headerbtn").first.click(timeout=3000)
                except Exception:
                    page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        else:
            print("  未找到 CI/CD 弹窗（可能是抽屉或跳转）")
    except Exception as e:
        print("  CI/CD 弹窗异常:", e)

    # ===== 遍历二级导航子页面 =====
    print("\n=== 二级导航子页面 ===")
    sub_report = []
    # 通过点击侧边导航项进入（先找导航项的定位方式）
    nav_sel_candidates = [".project-nav .el-menu-item", ".el-menu-item", "[class*='nav-item']"]
    nav_loc = None
    for sel in nav_sel_candidates:
        loc = page.locator(sel)
        if loc.count() >= 4:
            nav_loc = loc
            print("  使用导航选择器:", sel, "数量:", loc.count())
            break
    # 如果找不到，dump body 看看二级导航元素
    if nav_loc is None:
        print("  未定位二级导航，dump 侧边区域:")
        for sel in ["aside", ".el-aside", "[class*='side']", "[class*='nav']"]:
            loc = page.locator(sel)
            for i in range(loc.count()):
                print(f"    {sel}[{i}]: {clean(loc.nth(i).inner_text())[:300]}")

    browser.close()
    print("\n完成")
