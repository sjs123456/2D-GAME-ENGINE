# -*- coding: utf-8 -*-
"""诊断：逐个点击二级导航，只打印 URL 与耗时，定位卡点"""
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
    page.set_default_timeout(10000)
    page.on("dialog", lambda d: d.accept())

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(3)
    print("登录后:", page.url)

    page.locator(".el-menu .el-menu-item").filter(has_text="项目管理").first.click()
    time.sleep(2)
    page.locator(".project-card").first.click()
    time.sleep(3)
    print("详情:", page.url)

    nav = page.locator(".el-menu .el-menu-item")
    all_names = []
    for i in range(nav.count()):
        t = clean(nav.nth(i).inner_text())
        if t:
            all_names.append(t)
    sub_names = [n for n in all_names if n not in ["仪表盘", "项目管理", "设备管理"]]
    print("二级导航:", sub_names)

    for name in sub_names:
        t0 = time.time()
        try:
            item = page.locator(".el-menu .el-menu-item").filter(has_text=name)
            clicked = False
            for k in range(item.count()):
                if clean(item.nth(k).inner_text()) == name:
                    item.nth(k).scroll_into_view_if_needed(timeout=4000)
                    item.nth(k).click(timeout=5000)
                    clicked = True
                    break
            if not clicked:
                item.first.click(timeout=5000)
            page.wait_for_timeout(2000)
            print(f"[{time.time()-t0:6.1f}s] {name} -> {page.url}  H2={clean(page.locator('h2').first.inner_text()) if page.locator('h2').count() else ''}")
        except Exception as e:
            print(f"[{time.time()-t0:6.1f}s] {name} 异常: {str(e)[:150]}")
            try:
                page.goto("http://123.56.21.178:8080/projects/ab2fb177-e302-43bf-a146-6c1b6b9a771c", wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
            except Exception:
                pass

    browser.close()
    print("诊断完成")
