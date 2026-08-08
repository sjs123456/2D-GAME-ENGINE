import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(15000)

    url = "http://123.56.21.178:8080/login"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print("[ERROR] 打开页面失败:", e)
        page.screenshot(path=f"{OUT_DIR}/login-page-error.png", full_page=True)
        browser.close()
        sys.exit(1)

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    print("=== 页面基本信息 ===")
    print("URL:", page.url)
    print("Title:", page.title())

    # 分析页面结构：找出所有 input / button / form
    print("\n=== 页面 INPUT 元素 ===")
    inputs = page.locator("input")
    for i in range(inputs.count()):
        el = inputs.nth(i)
        info = el.evaluate("""el => ({
            tag: el.tagName,
            type: el.type,
            name: el.name,
            id: el.id,
            placeholder: el.placeholder,
            value: el.value,
            autocomplete: el.autocomplete
        })""")
        print(i, json.dumps(info, ensure_ascii=False))

    print("\n=== 页面 BUTTON 元素 ===")
    buttons = page.locator("button")
    for i in range(buttons.count()):
        el = buttons.nth(i)
        info = el.evaluate("""el => ({
            text: (el.innerText || '').trim().slice(0, 50),
            type: el.type,
            id: el.id,
            name: el.name,
            cls: el.className
        })""")
        print(i, json.dumps(info, ensure_ascii=False))

    # 也看看是否有 button 之外的提交元素（如 a 标签或 input[type=submit]）
    print("\n=== 其他可点击提交元素 (input[type=submit] / a) ===")
    subs = page.locator("input[type=submit]")
    for i in range(subs.count()):
        el = subs.nth(i)
        print("submit-input:", json.dumps(el.evaluate("""el => ({name: el.name, id: el.id, value: el.value, cls: el.className})"""), ensure_ascii=False))
    forms = page.locator("form")
    print("form 数量:", forms.count())

    # 截图页面初始状态
    page.screenshot(path=f"{OUT_DIR}/login-page-initial.png", full_page=True)
    print("\n[OK] 初始页面截图已保存:", f"{OUT_DIR}/login-page-initial.png")

    browser.close()
