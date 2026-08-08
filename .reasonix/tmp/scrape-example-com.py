import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.set_default_timeout(15000)

    page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass  # networkidle 失败不阻塞流程

    # 提取标题
    title = page.title()
    print("页面标题 (title):", title)

    # 提取 h1
    h1 = page.locator("h1").first.inner_text().strip()
    print("H1:", h1)

    # 提取段落文本
    paragraphs = page.locator("p").all_inner_texts()
    print("段落数量:", len(paragraphs))
    for i, para in enumerate(paragraphs, 1):
        print(f"段落 {i}: {para.strip()}")

    # 截图
    shot_path = ".reasonix/tmp/example_com.png"
    page.screenshot(path=shot_path, full_page=True)
    print("截图已保存:", shot_path)

    browser.close()
