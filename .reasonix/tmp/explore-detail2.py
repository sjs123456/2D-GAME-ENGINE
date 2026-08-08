# -*- coding: utf-8 -*-
"""聚焦探测：项目管理页列表结构/表头/行操作；设备管理页所有可交互元素"""
import sys, io, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
LOGIN_URL = "http://123.56.21.178:8080/login"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def goto_menu(page, name):
    page.locator(".el-menu .el-menu-item").filter(has_text=name).first.click()
    page.wait_for_timeout(1200)
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
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    out = {}

    # ===== 项目管理 =====
    print("\n===== 项目管理 =====")
    goto_menu(page, "项目管理")
    print("URL:", page.url)
    print("body 文本:")
    print(page.inner_text("body")[:1200].replace("\n", " | "))
    # 找表格/列表容器
    for sel in [".el-table", "table", ".project-item", ".project-card", ".project-list", "[class*='project']", ".el-timeline", ".el-collapse"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            print(f"\n容器 {sel}: 数量={loc.count()}")
            if loc.count() <= 5:
                try:
                    print("  首个:", clean(loc.first.inner_text())[:300])
                except Exception:
                    pass
    # 行内操作
    for sel in ["button", "a", "[class*='action']", "[class*='btn']", "[class*='operate']"]:
        loc = page.locator(sel)
        texts = []
        for i in range(min(loc.count(), 30)):
            t = clean(loc.nth(i).inner_text())
            cls = loc.nth(i).get_attribute("class") or ""
            if t:
                texts.append((t, cls))
        if texts:
            print(f"\n可点击元素 {sel} ({loc.count()}):")
            for t, c in texts[:20]:
                print("   ", repr(t), c)
    page.screenshot(path=f"{OUT_DIR}/explore-项目管理-detail.png", full_page=True)

    # ===== 设备管理 =====
    print("\n===== 设备管理 =====")
    goto_menu(page, "设备管理")
    print("URL:", page.url)
    print("body 文本:")
    print(page.inner_text("body")[:800].replace("\n", " | "))
    for sel in ["button", "a", "[role='button']", ".el-button", "[class*='btn']", "[class*='add']", "[class*='create']", "[class*='action']", ".el-dropdown", ".el-tooltip"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            texts = []
            for i in range(min(loc.count(), 20)):
                el = loc.nth(i)
                t = clean(el.inner_text())
                cls = el.get_attribute("class") or ""
                title = el.get_attribute("title") or ""
                icon = el.locator("i").first.get_attribute("class") if el.locator("i").count() else ""
                texts.append({"text": t, "class": cls, "title": title, "icon": icon})
            print(f"\n元素 {sel} ({loc.count()}):")
            for x in texts[:20]:
                print("   ", x)
    page.screenshot(path=f"{OUT_DIR}/explore-设备管理-detail2.png", full_page=True)

    # ===== 首页（面包屑里的首页 /） =====
    print("\n===== 首页 / =====")
    try:
        page.goto("http://123.56.21.178:8080/", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1000)
        print("URL:", page.url, "TITLE:", page.title())
        print("body:", page.inner_text("body")[:400].replace("\n", " | "))
        page.screenshot(path=f"{OUT_DIR}/explore-首页.png", full_page=True)
    except Exception as e:
        print("访问 / 异常:", e)

    browser.close()
    print("\n完成")
