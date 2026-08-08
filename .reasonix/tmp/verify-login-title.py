import sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

URL = "http://123.56.21.178:8080/login"
EXPECTED_TITLE = "自动化测试平台"
SCREENSHOT_DIR = ".reasonix/tmp"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, "login-page-title-check.png")

result = {"url": URL, "expected_title": EXPECTED_TITLE, "actual_title": None, "passed": None}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
    )
    page = context.new_page()
    page.set_default_timeout(15000)

    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass  # networkidle 超时可忽略，继续后续操作

        # 等待页面稳定后读取标题
        page.wait_for_timeout(1000)
        title = page.title()
        result["actual_title"] = title
        result["passed"] = (title == EXPECTED_TITLE)

        # 截图
        page.screenshot(path=SCREENSHOT_PATH, full_page=True)
        print(f"[截图已保存] {SCREENSHOT_PATH} ({os.path.getsize(SCREENSHOT_PATH)} bytes)")

    except Exception as e:
        print(f"[错误] {type(e).__name__}: {e}")
        # 出错时也尝试截图存证
        try:
            page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            print(f"[异常截图已保存] {SCREENSHOT_PATH}")
        except Exception:
            pass
        result["passed"] = False
    finally:
        browser.close()

# 输出验证结论
print("=" * 50)
print(f"目标 URL      : {result['url']}")
print(f"期望标题      : {result['expected_title']}")
print(f"实际标题      : {result['actual_title']!r}")
print(f"验证结论      : {'✅ 通过' if result['passed'] else '❌ 不通过'}")
print("=" * 50)
