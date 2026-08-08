# -*- coding: utf-8 -*-
"""探测项目详情：设置 tab、侧边导航完整结构（含非 el-menu-item 元素）、API Token/CI-CD 入口"""
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

LOGIN_URL = "http://123.56.21.178:8080/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
BASE = "http://123.56.21.178:8080"

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
    time.sleep(4)
    print("登录后:", page.url)

    # 直接 goto 详情页
    page.goto(f"{BASE}/projects/{PID}", wait_until="domcontentloaded", timeout=20000)
    time.sleep(2.5)
    print("详情页:", page.url)

    # 侧边导航完整结构 dump（含 class）
    print("\n=== 侧边导航元素 ===")
    nav_el = page.locator("aside, .el-aside")
    if nav_el.count() > 0:
        aside_html = nav_el.first.inner_html()
        # 打印所有带文本的 li/div/a
        for sel in ["li", ".el-menu-item", ".el-submenu", "a", ".el-menu--collapse", "[class*='menu']"]:
            els = nav_el.first.locator(sel)
            if els.count() > 0:
                found = []
                for i in range(els.count()):
                    t = clean(els.nth(i).inner_text())
                    cls = els.nth(i).get_attribute("class") or ""
                    if t:
                        found.append((t, cls))
                if found:
                    print(f"  {sel} ({els.count()}):")
                    for t, c in found[:25]:
                        print(f"     {t!r}  {c}")

    # 页签 tabs
    print("\n=== 页签 tabs ===")
    tabs = page.locator(".el-tabs__item")
    for i in range(tabs.count()):
        print(f"  tab[{i}]: {clean(tabs.nth(i).inner_text())!r}  class={tabs.nth(i).get_attribute('class')!r}")

    # 点击"设置"tab
    print("\n=== 点击设置 tab ===")
    st = page.locator(".el-tabs__item").filter(has_text="设置")
    print("设置tab数量:", st.count())
    if st.count() > 0:
        st.first.click()
        time.sleep(2)
        print("点击后 URL:", page.url)
        print("body 文本:", clean(page.inner_text("body"))[:800])
        page.screenshot(path=".reasonix/tmp/explore-sub-设置-tab.png", full_page=True)
        # 设置页内找 API Token / CI/CD
        for kw in ["API Token", "CI/CD", "Token"]:
            el = page.locator(f"text={kw}")
            print(f"  设置页包含 '{kw}': {el.count()}")
        # 设置页按钮/输入框
        btns = []
        for i in range(page.locator("button").count()):
            t = clean(page.locator("button").nth(i).inner_text())
            if t:
                btns.append(t)
        print("  设置页按钮:", btns)
        ins = []
        for i in range(page.locator("input").count()):
            el = page.locator("input").nth(i)
            ins.append({"placeholder": el.get_attribute("placeholder"), "class": el.get_attribute("class")})
        print("  设置页输入框:", ins)

    # 侧边导航点击"设置"（如果存在）
    print("\n=== 侧边导航点击设置 ===")
    set_nav = page.locator("aside .el-menu-item, aside li, aside a, aside [class*='menu-item']").filter(has_text="设置")
    print("侧边设置导航数量:", set_nav.count())
    for i in range(set_nav.count()):
        t = clean(set_nav.nth(i).inner_text())
        cls = set_nav.nth(i).get_attribute("class") or ""
        print(f"  [{i}] {t!r} {cls}")
    if set_nav.count() > 0:
        try:
            set_nav.first.click(timeout=5000)
            time.sleep(2)
            print("点击后 URL:", page.url)
            print("body:", clean(page.inner_text("body"))[:600])
        except Exception as e:
            print("点击异常:", str(e)[:100])

    # 侧边导航点击 API Token（若可点）
    print("\n=== 侧边导航点击 API Token ===")
    tok = page.locator("aside .el-menu-item, aside li, aside a, aside [class*='menu-item']").filter(has_text="API Token")
    print("API Token 导航数量:", tok.count())
    if tok.count() > 0:
        try:
            tok.first.scroll_into_view_if_needed(timeout=5000)
            tok.first.click(timeout=5000)
            time.sleep(2)
            print("点击后 URL:", page.url)
            print("body:", clean(page.inner_text("body"))[:600])
        except Exception as e:
            print("点击异常:", str(e)[:100])

    browser.close()
    print("\n完成")
