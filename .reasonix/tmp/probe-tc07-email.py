# -*- coding: utf-8 -*-
"""TC07 专项探测：无效邮箱提交后为何无提示无请求（检查 HTML5 原生校验）"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page = context.new_page()
    page.set_default_timeout(8000)
    api_resps = []
    page.on("response", lambda r: api_resps.append((r.status, r.url)) if "api/" in r.url else None)
    page.on("requestfailed", lambda r: print("请求失败:", r.url, r.failure))
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    page.locator("button.tab-btn:has-text('注册')").first.click()
    page.wait_for_timeout(600)

    inputs = page.locator("input.form-input")
    inputs.nth(0).fill("tc07probe_xyz")
    inputs.nth(1).fill("not-an-email")
    inputs.nth(2).fill("Test123456")
    inputs.nth(3).fill("Test123456")

    # 检查 HTML5 校验属性
    info = page.evaluate("""() => {
      const em = document.querySelector('input[type=email]');
      const form = document.querySelector('form.login-form');
      return {
        emailValid: em ? em.checkValidity() : null,
        emailValidityState: em ? Object.fromEntries(Object.entries(em.validity).map(([k,v]) => [k, v])) : null,
        formNoValidate: form ? form.noValidate : null,
        formNovalidateAttr: form ? form.hasAttribute('novalidate') : null,
        onsubmit: form ? (form.onsubmit ? form.onsubmit.toString().slice(0,200) : null) : null,
      };
    }""")
    print("校验属性:", json.dumps(info, ensure_ascii=False, indent=2))

    # 点击提交
    page.click("button.submit-btn")
    page.wait_for_timeout(2500)

    # 检查 validationMessage
    vm = page.evaluate("""() => {
      const em = document.querySelector('input[type=email]');
      return em ? {message: em.validationMessage, value: em.value} : null;
    }""")
    print("validationMessage:", json.dumps(vm, ensure_ascii=False))
    print("URL:", page.url)
    print("API:", api_resps)
    print("body 截取:", repr(page.inner_text("body", timeout=3000)[:400]))
    page.screenshot(path=os.path.join(OUT_DIR, "register-TC07-probe.png"))
    print("截图: register-TC07-probe.png")
    context.close()
    browser.close()
