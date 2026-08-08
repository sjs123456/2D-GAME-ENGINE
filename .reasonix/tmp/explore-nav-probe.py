# -*- coding: utf-8 -*-
"""登录后探测主导航结构：所有链接、菜单项、按钮，供全站探索规划"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"
BASE = "http://123.56.21.178:8080"

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

    # 等待跳转
    jumped = False
    start = time.time()
    while time.time() - start < 15:
        page.wait_for_timeout(500)
        if page.url != LOGIN_URL:
            jumped = True
            break
    print("登录跳转:", jumped, "URL:", page.url)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1200)

    print("TITLE:", page.title())

    # 1. 所有 a 链接
    links = page.locator("a")
    print(f"\n=== <a> 链接数量: {links.count()} ===")
    for i in range(links.count()):
        el = links.nth(i)
        href = el.get_attribute("href") or ""
        text = (el.inner_text() or "").strip().replace("\n", " ")
        cls = el.get_attribute("class") or ""
        if text or href:
            print(f"  a[{i}] text={text!r} href={href!r} class={cls!r}")

    # 2. 侧边栏/菜单容器：常见 class
    print("\n=== 可能的导航容器 ===")
    for sel in [".sidebar", ".menu", ".nav", ".aside", ".el-menu", ".el-aside", ".layout-side", ".left-menu", "aside", "nav", ".ant-menu"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            print(f"  容器 {sel}: 数量={loc.count()}")
            try:
                txt = loc.first.inner_text()
                print("    文本:", txt.replace("\n", " | ")[:400])
            except Exception:
                pass

    # 3. 所有按钮
    btns = page.locator("button")
    print(f"\n=== button 数量: {btns.count()} ===")
    for i in range(btns.count()):
        el = btns.nth(i)
        text = (el.inner_text() or "").strip().replace("\n", " ")
        cls = el.get_attribute("class") or ""
        if text or cls:
            print(f"  button[{i}] text={text!r} class={cls!r}")

    # 4. 页面 body 文本摘要
    print("\n=== body 文本(800字) ===")
    print(page.inner_text("body").replace("\n", " | ")[:800])

    # 5. 当前 URL 的标题元素
    for sel in ["h1", "h2", "h3", ".page-title", ".title", ".breadcrumb"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            texts = [t.strip() for t in loc.all_inner_texts() if t.strip()]
            print(f"\n{sel}: {texts[:8]}")

    page.screenshot(path=f"{OUT_DIR}/explore-nav-probe.png", full_page=True)
    print("\n截图: .reasonix/tmp/explore-nav-probe.png")
    browser.close()
