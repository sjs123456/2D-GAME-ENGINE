# -*- coding: utf-8 -*-
"""确认项目卡片右上角操作菜单内容"""
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

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
    page.set_default_timeout(8000)
    page.on("dialog", lambda d: d.accept())

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)

    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    time.sleep(2)

    # 项目卡片右上角按钮/下拉
    card = page.locator(".project-card").first
    print("卡片 HTML:", card.inner_html()[:1500].replace("\n", " "), flush=True)

    # 尝试点击卡片右上角按钮（el-dropdown 或图标按钮）
    dd = card.locator(".el-dropdown, .card-actions button, .card-actions .el-button")
    print("\n卡片操作按钮数量:", dd.count(), flush=True)
    for i in range(dd.count()):
        el = dd.nth(i)
        print(f"  [{i}] text={clean(el.inner_text())!r} class={el.get_attribute('class')!r} title={el.get_attribute('title')!r}", flush=True)
    if dd.count() > 0:
        dd.first.click()
        page.wait_for_timeout(900)
        menus = page.locator(".el-dropdown-menu__item:visible, .el-dropdown__popper:visible .el-dropdown-menu__item")
        items = []
        for i in range(menus.count()):
            t = clean(menus.nth(i).inner_text())
            if t:
                items.append(t)
        print("下拉菜单项:", items, flush=True)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

    browser.close()
    print("完成", flush=True)
