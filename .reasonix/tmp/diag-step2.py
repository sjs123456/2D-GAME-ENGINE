# -*- coding: utf-8 -*-
"""定位卡点2：goto + 基础提取 + full_page截图 + 创建按钮弹窗，逐步打印耗时"""
import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

LOGIN_URL = "http://123.56.21.178:8080/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
BASE = "http://123.56.21.178:8080"

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def close_dialog(page):
    try:
        page.locator(".el-dialog__footer button:has-text('取消')").first.click(timeout=2500)
        return
    except Exception:
        pass
    try:
        page.locator(".el-dialog__headerbtn").first.click(timeout=2500)
        return
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

def get_dialog(page):
    for j in range(page.locator(".el-dialog").count()):
        d = page.locator(".el-dialog").nth(j)
        if d.is_visible():
            return d
    return None

def record_dialog(page, btn_text, t0):
    dlg = get_dialog(page)
    if dlg is None:
        print(f"    [{time.time()-t0:6.1f}s] 无弹窗", flush=True)
        return
    title = clean(dlg.locator(".el-dialog__title").first.inner_text()) if dlg.locator(".el-dialog__title").count() else btn_text
    print(f"    [{time.time()-t0:6.1f}s] 弹窗「{title}」 form-items={dlg.locator('.el-form-item').count()}", flush=True)
    try:
        dlg.screenshot(path=f".reasonix/tmp/diag-dialog-{title}.png", timeout=5000)
        print(f"    [{time.time()-t0:6.1f}s] 弹窗截图OK", flush=True)
    except Exception as e:
        print(f"    [{time.time()-t0:6.1f}s] 弹窗截图异常: {str(e)[:80]}", flush=True)
    close_dialog(page)
    page.wait_for_timeout(400)
    print(f"    [{time.time()-t0:6.1f}s] 弹窗已关闭", flush=True)

with sync_playwright() as p:
    t0 = time.time()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.set_default_timeout(8000)
    page.on("dialog", lambda d: d.accept())

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", "admin123")
    page.fill("input[placeholder='请输入密码']", "Admin123")
    page.locator("button.submit-btn").click()
    time.sleep(4)
    print(f"[{time.time()-t0:6.1f}s] 登录后 {page.url}", flush=True)

    for name, url in [
        ("全部用例", f"{BASE}/projects/{PID}/testcases"),
        ("测试套件", f"{BASE}/projects/{PID}/suites"),
        ("关键字库", f"{BASE}/projects/{PID}/keywords"),
    ]:
        t1 = time.time()
        print(f"\n[{time.time()-t0:6.1f}s] ==== {name}", flush=True)
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)
        print(f"  [{time.time()-t0:6.1f}s] h2={clean(page.locator('h2').first.inner_text()) if page.locator('h2').count() else ''}", flush=True)
        btns = [clean(page.locator("button").nth(i).inner_text()) for i in range(page.locator("button").count())]
        print(f"  [{time.time()-t0:6.1f}s] 按钮={btns}", flush=True)
        # full_page 截图
        try:
            page.screenshot(path=f".reasonix/tmp/diag-{name}.png", full_page=True, timeout=8000)
            print(f"  [{time.time()-t0:6.1f}s] full截图OK", flush=True)
        except Exception as e:
            print(f"  [{time.time()-t0:6.1f}s] full截图异常: {str(e)[:100]}", flush=True)
        # 创建按钮
        create = page.locator("button").filter(has_text=re.compile("新建|添加|创建|新增|导入|生成"))
        cl = []
        for i in range(create.count()):
            t = clean(create.nth(i).inner_text())
            if t and t not in cl:
                cl.append(t)
        print(f"  [{time.time()-t0:6.1f}s] 创建类={cl}", flush=True)
        for btn_text in cl:
            try:
                btn = page.locator("button").filter(has_text=btn_text).first
                btn.scroll_into_view_if_needed(timeout=4000)
                btn.click(timeout=4000)
                page.wait_for_timeout(900)
                print(f"  [{time.time()-t0:6.1f}s] 已点击 {btn_text}", flush=True)
                record_dialog(page, btn_text, t0)
            except Exception as e:
                print(f"  [{time.time()-t0:6.1f}s] 点击/记录 {btn_text} 异常: {str(e)[:120]}", flush=True)
                close_dialog(page)
        print(f"  [{time.time()-t0:6.1f}s] {name} 完成 耗时{time.time()-t1:.1f}s", flush=True)

    browser.close()
    print(f"[{time.time()-t0:6.1f}s] DONE", flush=True)
