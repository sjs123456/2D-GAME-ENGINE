# -*- coding: utf-8 -*-
"""探测登录页结构：输入框、按钮、提示元素、表单属性"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

URL = "http://123.56.21.178:8080/login"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(10000)
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception as e:
        print("load warn:", e)

    print("URL:", page.url)
    print("TITLE:", page.title())
    print("=" * 60)

    # 输入框
    inputs = page.locator("input")
    print(f"input 数量: {inputs.count()}")
    for i in range(inputs.count()):
        el = inputs.nth(i)
        print(f"  input[{i}] type={el.get_attribute('type')!r} name={el.get_attribute('name')!r} "
              f"id={el.get_attribute('id')!r} placeholder={el.get_attribute('placeholder')!r} "
              f"class={el.get_attribute('class')!r}")

    # 按钮
    btns = page.locator("button")
    print(f"button 数量: {btns.count()}")
    for i in range(btns.count()):
        el = btns.nth(i)
        print(f"  button[{i}] text={el.inner_text()!r} type={el.get_attribute('type')!r} "
              f"class={el.get_attribute('class')!r}")

    # 表单
    forms = page.locator("form")
    print(f"form 数量: {forms.count()}")

    # 常见提示容器
    for sel in [".el-message", ".el-message-box", ".error", ".alert", ".el-alert", ".toast", ".notification", ".el-notification", ".el-form-item__error", ".ant-message"]:
        loc = page.locator(sel)
        n = loc.count()
        if n:
            print(f"提示容器 {sel}: 数量={n}, 文本={loc.first.inner_text()!r}")

    # body 前 1500 字符文本
    body_text = page.inner_text("body")
    print("BODY_TEXT(截断1500):")
    print(body_text[:1500])

    page.screenshot(path=".reasonix/tmp/probe-login-page.png", full_page=True)
    print("截图已保存: .reasonix/tmp/probe-login-page.png")
    browser.close()
