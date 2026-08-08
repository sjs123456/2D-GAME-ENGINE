import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = ".reasonix/tmp"
USERNAME = "admin123"
PASSWORD = "Admin123"
LOGIN_URL = "http://123.56.21.178:8080/login"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(15000)

    # 监听对话框
    page.on("dialog", lambda d: (print("[DIALOG]", d.message), d.accept()))

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    # 1. 填写账号密码
    page.fill("input[placeholder='请输入用户名']", USERNAME)
    page.fill("input[placeholder='请输入密码']", PASSWORD)
    print("[OK] 已填写账号:", USERNAME, "密码:", "*" * len(PASSWORD))

    # 2. 点击登录按钮
    login_btn = page.locator("button.submit-btn")
    login_btn.scroll_into_view_if_needed()
    login_btn.click()
    print("[OK] 已点击登录按钮")

    # 3. 等待跳转，最长 15 秒（轮询 URL 变化）
    jumped = False
    start = time.time()
    while time.time() - start < 15:
        page.wait_for_timeout(500)
        cur = page.url
        if cur != LOGIN_URL:
            jumped = True
            break

    print("\n=== 登录结果 ===")
    print("是否发生跳转:", "是" if jumped else "否")
    print("最终 URL:", page.url)
    print("页面标题:", page.title())

    # 判断是否跳转到首页（/ 或 /index 等）
    cur_path = page.url.split("?", 1)[0].rstrip("/")
    final_path = cur_path
    is_home = final_path in ("", "/index", "/index.html", "/home", "/dashboard") or final_path.endswith("/index")
    print("路径:", final_path or "/")
    print("是否首页:", "是" if is_home else "否")

    # 4. 若未跳转，截图并尝试提取错误信息
    if not jumped:
        print("\n[WARN] 未检测到跳转，检查页面状态...")
        # 查找可能的错误提示（常见 class: error / message / toast / alert）
        for sel in [".error", ".message", ".toast", ".alert", ".el-message", ".el-message__content", "[class*='error']", "[class*='tip']", "[class*='msg']"]:
            try:
                loc = page.locator(sel)
                if loc.count() > 0:
                    texts = [t.strip() for t in loc.all_inner_texts() if t.strip()]
                    if texts:
                        print(f"  提示元素 {sel}: {texts[:3]}")
            except Exception:
                pass
        body_txt = page.inner_text("body")[:500]
        print("  body 前500字:", body_txt.replace("\n", " | ")[:500])

    # 5. 保存登录后页面截图
    page.wait_for_timeout(1500)
    shot = f"{OUT_DIR}/after-login.png"
    page.screenshot(path=shot, full_page=True)
    print("\n[OK] 登录后截图已保存:", shot)

    # 附加：若跳转成功，打印一些首页信息
    if jumped:
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        print("\n=== 登录后页面内容摘要 ===")
        body = page.inner_text("body")
        print("body 前600字:", body.replace("\n", " | ")[:600])

    browser.close()
