# -*- coding: utf-8 -*-
"""全站探索用例集执行 v1（TC01~TC14），支持分段运行
用法: python explore-cases-v1.py --part 1|2|3
  part1: 登录 + TC01-TC05
  part2: TC06-TC10（复用登录态）
  part3: TC11-TC14（复用登录态，合并结果落盘）
"""
import sys, io, json, time, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

OUT_DIR = os.path.abspath(".reasonix/tmp")
BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
PID = "ab2fb177-e302-43bf-a146-6c1b6b9a771c"
USERNAME = "admin123"
PASSWORD = "Admin123"
AUTH_PATH = os.path.join(OUT_DIR, "explore-auth.json").replace("\\", "/")

ts = time.strftime("%Y%m%d%H%M%S")
RUN_AT = time.strftime("%Y-%m-%d %H:%M:%S")
SCRIPT = "explore-cases-v1.py"

PROJ = f"proj_{ts}"
CASE = f"case_{ts}"
SUITE = f"suite_{ts}"
ENV = f"env_{ts}"
KW = f"kw_{ts}"
TOKEN = f"token_{ts}"
SCHED = f"sched_{ts}"

api_log = []
capture_api = True

def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def on_response(resp):
    if not capture_api:
        return
    try:
        if "/api/" in resp.url and resp.request.resource_type in ("xhr", "fetch"):
            api_log.append({"url": resp.url, "status": resp.status, "method": resp.request.method})
    except Exception:
        pass

def wait_net(page, sec=4):
    try:
        page.wait_for_load_state("networkidle", timeout=int(sec * 1000))
    except Exception:
        pass

def body_excerpt(page, n=400):
    try:
        return clean(page.inner_text("body"))[:n]
    except Exception:
        return ""

def grab_toasts(page):
    msgs = []
    try:
        els = page.locator(".el-message")
        for i in range(els.count()):
            t = clean(els.nth(i).inner_text())
            if t and t not in msgs:
                msgs.append(t)
    except Exception:
        pass
    return msgs

def visible_dialog(page):
    try:
        for i in range(page.locator(".el-dialog").count()):
            d = page.locator(".el-dialog").nth(i)
            if d.is_visible():
                return d
    except Exception:
        pass
    return None

def form_errors(page, scope=None):
    errs = []
    try:
        loc = scope.locator(".el-form-item__error") if scope is not None else page.locator(".el-form-item__error")
        for i in range(loc.count()):
            t = clean(loc.nth(i).inner_text())
            if t and t not in errs:
                errs.append(t)
    except Exception:
        pass
    return errs

def close_dialog(page):
    try:
        d = visible_dialog(page)
        if d is not None:
            b = d.locator(".el-dialog__footer button:has-text('取消')")
            if b.count() > 0:
                b.first.click(timeout=3000)
                return "cancel"
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
        return "esc"
    except Exception:
        return "none"

def fill_by_label(page, scope, label_text, value):
    try:
        fi = None
        if scope is not None:
            c = scope.locator(".el-form-item").filter(has_text=label_text)
            if c.count() > 0:
                fi = c.first
        if fi is None:
            c = page.locator(".el-form-item").filter(has_text=label_text)
            if c.count() > 0:
                fi = c.first
        if fi is None:
            return f"no-fi:{label_text}"
        inp = fi.locator("input, textarea")
        if inp.count() > 0:
            inp.first.fill(value)
            return f"ok:{label_text}"
        return f"no-inp:{label_text}"
    except Exception as e:
        return f"err:{label_text}:{str(e)[:60]}"

def choose_select(page, scope, label_text, want):
    try:
        fi = None
        if scope is not None:
            c = scope.locator(".el-form-item").filter(has_text=label_text)
            if c.count() > 0:
                fi = c.first
        if fi is None:
            c = page.locator(".el-form-item").filter(has_text=label_text)
            if c.count() > 0:
                fi = c.first
        if fi is None:
            return f"no-fi:{label_text}"
        sel = fi.locator("select")
        if sel.count() > 0:
            sel.first.select_option(label=want)
            return f"native:{want}"
        sel2 = fi.locator(".el-select")
        if sel2.count() > 0:
            sel2.first.click()
            page.wait_for_timeout(500)
            items = page.locator(".el-select-dropdown__item:visible")
            for k in range(items.count()):
                t = clean(items.nth(k).inner_text())
                if t and (want in t or t in want):
                    items.nth(k).click()
                    page.wait_for_timeout(200)
                    return f"el:{t}"
            for k in range(items.count()):
                t = clean(items.nth(k).inner_text())
                if t:
                    items.nth(k).click()
                    page.wait_for_timeout(200)
                    return f"el-first:{t}"
            page.keyboard.press("Escape")
            return f"no-opt:{want}"
        return f"no-ctrl:{label_text}"
    except Exception as e:
        return f"err:{label_text}:{str(e)[:60]}"

def click_scope_button(page, scope, text):
    try:
        b = scope.locator("button").filter(has_text=text).first
        b.scroll_into_view_if_needed(timeout=5000)
        b.click()
        return True
    except Exception as e:
        try:
            b2 = page.locator("button").filter(has_text=text).first
            b2.scroll_into_view_if_needed(timeout=5000)
            b2.click()
            return True
        except Exception:
            return False

def shot(page, name):
    p = os.path.join(OUT_DIR, name).replace("\\", "/")
    try:
        page.screenshot(path=p, full_page=True)
        return p
    except Exception as e:
        return p

def goto(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(400)

def login(page):
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.fill("input[placeholder='请输入用户名']", USERNAME)
    page.fill("input[placeholder='请输入密码']", PASSWORD)
    page.locator("button.submit-btn").click()
    start = time.time()
    while time.time() - start < 15:
        page.wait_for_timeout(400)
        if page.url != LOGIN_URL:
            break
    wait_net(page)
    page.wait_for_timeout(500)
    print("[OK] 登录后 URL:", page.url, flush=True)

def make_result(tc_id, desc, step, expect):
    return {
        "id": tc_id, "desc": desc, "step": step, "expect": expect,
        "result": "", "url": "", "title": "", "verdict": "BLOCKED",
        "screenshot": "", "api_responses": [], "hints": [], "dialogs": [],
        "body_excerpt": "", "script": SCRIPT, "run_at": RUN_AT,
    }

def finalize(r, page, seg):
    r["url"] = page.url
    r["title"] = page.title()
    r["api_responses"] = seg[-30:]
    r["body_excerpt"] = body_excerpt(page)
    return r

def new_context(browser, use_auth=False):
    if use_auth and os.path.exists(AUTH_PATH):
        ctx = browser.new_context(
            storage_state=AUTH_PATH,
            viewport={"width": 1440, "height": 900}, locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        print("[OK] 使用存储登录态", flush=True)
    else:
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900}, locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
    return ctx

# ================= TC 用例 =================

def tc01(page):
    r = make_result("TC01", "项目管理：新建项目成功（唯一测试项目名）",
                    "进入 /projects → 点击「新建项目」→ 填写项目名称/描述/Git 地址 → 点击「确认创建」",
                    "toast「项目创建成功」；项目卡片列表出现 proj_<ts>；可搜索；详情名称=proj_<ts>、拥有者=admin123")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects")
        click_scope_button(page, page.locator("body"), "新建项目")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "点击「新建项目」未出现弹窗"; r["verdict"] = "FAIL"
        else:
            page.fill("input[placeholder='请输入项目名称']", PROJ)
            try:
                page.fill("textarea", "自动化回归测试项目-" + ts)
            except Exception:
                r["hints"].append("描述 textarea 未找到")
            try:
                page.fill("input[placeholder='https://github.com/team/test-cases.git（可选）']", f"https://github.com/team/{PROJ}.git")
            except Exception:
                r["hints"].append("Git 仓库地址输入框未找到（可选字段）")
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1500)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            try:
                sb = page.locator("input[placeholder='搜索项目名称或描述...']")
                sb.fill(PROJ)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                cards = page.locator(".project-card")
                found = any(PROJ in clean(cards.nth(i).inner_text()) for i in range(cards.count()))
                r["hints"].append(f"搜索后项目卡片出现={found}")
                if found:
                    cards.filter(has_text=PROJ).first.click()
                    page.wait_for_timeout(1200)
                    wait_net(page)
                    dtxt = clean(page.inner_text("body"))
                    r["result"] = f"创建成功；toast={toasts}；详情含项目名={PROJ in dtxt}、admin123={'admin123' in dtxt}"
                    r["verdict"] = "PASS" if (PROJ in dtxt and "admin123" in dtxt) else "PARTIAL"
                else:
                    r["result"] = f"toast={toasts}；但搜索未找到项目卡片"; r["verdict"] = "FAIL"
            except Exception as e:
                r["result"] = f"创建后验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC01.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC01.png")
    return finalize(r, page, api_log[s0:])

def tc02(page):
    r = make_result("TC02", "项目管理：新建项目必填校验（项目名称为空）",
                    "进入 /projects → 新建项目 → 名称留空 → 确认创建",
                    "出现「请输入项目名称」提示或按钮禁用；弹窗不关闭；无创建成功请求")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects")
        before_count = page.locator(".project-card").count()
        click_scope_button(page, page.locator("body"), "新建项目")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1200)
            errs = form_errors(page, dlg)
            toasts = grab_toasts(page)
            still_open = visible_dialog(page) is not None
            after_count = page.locator(".project-card").count()
            r["result"] = f"校验提示={errs}；toast={toasts}；弹窗仍打开={still_open}；卡片数 {before_count}->{after_count}"
            r["hints"] = [f"before={before_count}", f"after={after_count}"]
            r["verdict"] = "PASS" if (errs or toasts) and still_open and after_count == before_count else "FAIL"
            close_dialog(page)
        r["screenshot"] = shot(page, "explore-TC02.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC02.png")
    return finalize(r, page, api_log[s0:])

def tc03(page):
    r = make_result("TC03", "用例管理：新建 Web 用例成功（保存并关闭）",
                    "项目详情 → 用例 tab → 新建用例 → 填字段 → 保存并关闭",
                    "toast 保存成功；跳回用例列表；出现 case_<ts>，类型=Web 测试、状态=活跃、优先级=P1")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/testcases?type=web")
        click_scope_button(page, page.locator("body"), "新建用例")
        page.wait_for_timeout(1200)
        r["hints"].append("new_url=" + page.url)
        if "/testcases/new/web" not in page.url:
            r["result"] = f"未跳转新建用例页: {page.url}"; r["verdict"] = "FAIL"
        else:
            page.fill("input[placeholder='请输入用例名称']", CASE)
            r["hints"].append("类型=" + choose_select(page, None, "测试类型", "Web 测试"))
            r["hints"].append("优先级=" + choose_select(page, None, "优先级", "P1 (高)"))
            r["hints"].append("状态=" + choose_select(page, None, "状态", "活跃"))
            r["hints"].append("超时=" + fill_by_label(page, None, "超时", "60"))
            r["hints"].append("重试=" + fill_by_label(page, None, "重试", "0"))
            r["hints"].append("前置=" + fill_by_label(page, None, "前置条件", f"前置条件-{ts}"))
            # 系统要求至少一个测试步骤（用例设计未含步骤字段，动态补充）
            try:
                page.locator("button:has-text('+ 添加步骤')").first.click()
                page.wait_for_timeout(600)
                page.fill("input[placeholder='步骤说明']", "打开首页并验证标题")
                r["hints"].append("已添加测试步骤（步骤说明）")
            except Exception as e:
                r["hints"].append(f"添加测试步骤失败: {str(e)[:80]}")
            page.wait_for_timeout(300)
            click_scope_button(page, page.locator("body"), "保存并关闭")
            page.wait_for_timeout(1800)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            try:
                sb = page.locator("input[placeholder='搜索用例名称...']")
                sb.fill(CASE)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                web_col = ("Web 测试" in tbody) or ("Web" in tbody)
                r["hints"].append("表格类型列显示 Web（等价 Web 测试）")
                r["result"] = f"toast={toasts}；URL={page.url}；表含case={CASE in tbody}、Web={web_col}、活跃={'活跃' in tbody}、P1={'P1' in tbody}"
                r["verdict"] = "PASS" if (CASE in tbody and web_col and "活跃" in tbody and "P1" in tbody) else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC03.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC03.png")
    return finalize(r, page, api_log[s0:])

def tc04(page):
    r = make_result("TC04", "用例管理：新建用例必填校验（用例名称为空）",
                    "项目详情 → 用例 tab → 新建用例 → 名称留空 → 保存并关闭",
                    "出现「请输入用例名称」提示或保存按钮禁用；不跳转、无成功 toast；URL 仍在 /testcases/new/web")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/testcases?type=web")
        click_scope_button(page, page.locator("body"), "新建用例")
        page.wait_for_timeout(1200)
        if "/testcases/new/web" not in page.url:
            r["result"] = f"未跳转新建用例页: {page.url}"; r["verdict"] = "FAIL"
        else:
            click_scope_button(page, page.locator("body"), "保存并关闭")
            page.wait_for_timeout(1500)
            errs = form_errors(page)
            toasts = grab_toasts(page)
            url_still = "/testcases/new/web" in page.url
            r["result"] = f"校验提示={errs}；toast={toasts}；URL仍在新建页={url_still}"
            r["verdict"] = "PASS" if (errs or toasts) and url_still else "FAIL"
        r["screenshot"] = shot(page, "explore-TC04.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC04.png")
    return finalize(r, page, api_log[s0:])

def tc05(page):
    r = make_result("TC05", "测试套件：新建套件 + 已知缺陷回归（undefined 项目 ID）",
                    "项目详情 → 套件 tab → 新建套件 → 记录 URL → 填名称/描述 → 保存套件",
                    "URL 应含有效项目 ID；若为 /projects/undefined/suites/new 则缺陷复现；表单可填写；保存后列表出现 suite_<ts>")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/suites")
        click_scope_button(page, page.locator("body"), "新建套件")
        page.wait_for_timeout(1500)
        new_url = page.url
        r["hints"].append("点击后URL=" + new_url)
        is_undefined = "/projects/undefined/suites/new" in new_url
        r["hints"].append(f"URL含undefined={is_undefined}")
        try:
            page.locator("text=当前项目 undefined").first.wait_for(timeout=2500)
            r["hints"].append("侧边栏出现「当前项目 undefined」")
        except Exception:
            pass
        page.fill("input", SUITE)
        try:
            page.fill("textarea", f"套件-{ts}")
        except Exception:
            r["hints"].append("描述 textarea 未找到（可选）")
        click_scope_button(page, page.locator("body"), "保存套件")
        page.wait_for_timeout(1800)
        toasts = grab_toasts(page)
        r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
        r["hints"].append("保存后URL=" + page.url)
        found = False
        try:
            page.fill("input[placeholder='搜索套件名称...']", SUITE)
            page.press("input[placeholder='搜索套件名称...']", "Enter")
            page.wait_for_timeout(1000)
            tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
            found = SUITE in tbody
            r["hints"].append(f"列表出现suite={found}")
        except Exception:
            r["hints"].append("列表搜索异常")
        if is_undefined:
            r["result"] = f"缺陷复现：/projects/undefined/suites/new；表单可填写；保存后toast={toasts}；列表出现={found}"
            r["verdict"] = "FAIL"
            r["hints"].insert(0, "缺陷复现：/projects/undefined/suites/new")
        else:
            r["result"] = f"URL正常={new_url}；toast={toasts}；列表出现={found}"
            r["verdict"] = "PASS" if found else "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC05.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC05.png")
    return finalize(r, page, api_log[s0:])

def tc06(page):
    r = make_result("TC06", "测试套件：新建套件必填校验（套件名称为空）",
                    "项目详情 → 套件 tab → 新建套件 → 名称留空 → 保存套件",
                    "出现「请输入套件名称」提示或按钮禁用；不跳转、无成功 toast；未创建空名套件")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/suites")
        click_scope_button(page, page.locator("body"), "新建套件")
        page.wait_for_timeout(1500)
        r["hints"].append("URL=" + page.url)
        click_scope_button(page, page.locator("body"), "保存套件")
        page.wait_for_timeout(1500)
        errs = form_errors(page)
        toasts = grab_toasts(page)
        r["result"] = f"校验提示={errs}；toast={toasts}；URL={page.url}"
        r["verdict"] = "PASS" if (errs or toasts) else "FAIL"
        r["screenshot"] = shot(page, "explore-TC06.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC06.png")
    return finalize(r, page, api_log[s0:])

def tc07(page):
    r = make_result("TC07", "测试环境：新建环境成功",
                    "项目详情 → 环境页 → 新建环境 → 填名称/类型/URL/超时 → 确认创建",
                    "toast「环境创建成功」；环境列表出现 env_<ts>；类型=Staging、URL 正确")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/environments")
        click_scope_button(page, page.locator("body"), "新建环境")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            page.fill("input[placeholder='例如: 测试环境']", ENV)
            r["hints"].append("类型=" + choose_select(page, dlg, "环境类型", "Staging"))
            try:
                page.fill("input[placeholder='https://staging.api.example.com']", f"https://staging-{ts}.example.com")
            except Exception:
                r["hints"].append("基础 URL 输入框未找到")
            r["hints"].append("超时=" + fill_by_label(page, dlg, "全局超时", "30000"))
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1500)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            try:
                sb = page.locator("input[placeholder='搜索环境名称...']")
                sb.fill(ENV)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                r["result"] = f"toast={toasts}；表含env={ENV in tbody}、Staging={'Staging' in tbody}、URL={f'staging-{ts}.example.com' in tbody}"
                r["verdict"] = "PASS" if (ENV in tbody and "Staging" in tbody and f"staging-{ts}.example.com" in tbody) else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC07.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC07.png")
    return finalize(r, page, api_log[s0:])

def tc08(page):
    r = make_result("TC08", "测试环境：新建环境必填校验（基础 URL 为空）",
                    "项目详情 → 环境页 → 新建环境 → 名称填、URL 留空 → 确认创建",
                    "出现「请输入基础 URL」提示或按钮禁用；弹窗不关闭；未创建环境")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/environments")
        click_scope_button(page, page.locator("body"), "新建环境")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            page.fill("input[placeholder='例如: 测试环境']", f"env_empty_url_{ts}")
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1200)
            errs = form_errors(page, dlg)
            toasts = grab_toasts(page)
            still_open = visible_dialog(page) is not None
            r["result"] = f"校验提示={errs}；toast={toasts}；弹窗仍打开={still_open}"
            r["verdict"] = "PASS" if (errs or toasts) and still_open else "FAIL"
            close_dialog(page)
        r["screenshot"] = shot(page, "explore-TC08.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC08.png")
    return finalize(r, page, api_log[s0:])

def tc09(page):
    r = make_result("TC09", "关键字库：添加关键字成功",
                    "项目详情 → 关键字库 → 添加关键字 → 填名称/类型/描述/Python 代码 → 确认创建",
                    "toast 添加成功；关键字列表出现 kw_<ts>；Python 代码展示正确")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/keywords")
        click_scope_button(page, page.locator("body"), "添加关键字")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            r["hints"].append("名称=" + fill_by_label(page, dlg, "关键字名称", KW))
            r["hints"].append("类型=" + choose_select(page, dlg, "类型", "自定义"))
            r["hints"].append("描述=" + fill_by_label(page, dlg, "描述", f"关键字-{ts}"))
            r["hints"].append("Python=" + fill_by_label(page, dlg, "Python 代码", f"def {KW}():\n    return 'ok'"))
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1500)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            try:
                sb = page.locator("input[placeholder='搜索关键字名称...']")
                sb.fill(KW)
                sb.press("Enter")
                page.wait_for_timeout(1000)
                card_txt = ""
                cards = page.locator(".keyword-card")
                for i in range(cards.count()):
                    ct = clean(cards.nth(i).inner_text())
                    if KW in ct:
                        card_txt = ct
                        break
                r["hints"].append("关键字列表为 .keyword-card 卡片结构")
                r["result"] = f"toast={toasts}；关键字卡片含kw={KW in card_txt}；代码展示={'def' in card_txt}"
                r["verdict"] = "PASS" if (KW in card_txt and "def" in card_txt) else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC09.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC09.png")
    return finalize(r, page, api_log[s0:])

def ensure_suite(page):
    """确保套件存在，返回 (ready, hints)"""
    hints = []
    ready = False
    goto(page, f"{BASE}/projects/{PID}/suites")
    try:
        sb = page.locator("input[placeholder='搜索套件名称...']")
        sb.fill(SUITE)
        sb.press("Enter")
        page.wait_for_timeout(1000)
        tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
        ready = SUITE in tbody
    except Exception:
        pass
    if not ready:
        hints.append("TC05 套件未保存成功，降级：用有效项目 ID 进入 /projects/{id}/suites/new 建套件")
        goto(page, f"{BASE}/projects/{PID}/suites/new")
        page.wait_for_timeout(800)
        try:
            page.fill("input", SUITE)
            try:
                page.fill("textarea", f"套件-{ts}")
            except Exception:
                pass
            click_scope_button(page, page.locator("body"), "保存套件")
            page.wait_for_timeout(1800)
            toasts_s = grab_toasts(page)
            hints.append("降级创建套件toast=" + json.dumps(toasts_s, ensure_ascii=False))
            hints.append("降级创建后URL=" + page.url)
        except Exception as e:
            hints.append(f"降级创建套件异常: {str(e)[:120]}")
    else:
        hints.append("套件已存在（TC05 保存成功）")
    return ready, hints

def tc10(page):
    r = make_result("TC10", "定时任务：新建定时任务成功",
                    "项目详情 → 定时任务 → 新建定时任务 → 填名称/Cron/描述/选套件 → 确认创建",
                    "toast 创建成功；定时任务列表出现 sched_<ts>；Cron=0 8 * * *、套件=suite_<ts>、状态=启用")
    s0 = len(api_log)
    try:
        r["hints"].extend(ensure_suite(page)[1])
        goto(page, f"{BASE}/projects/{PID}/schedules")
        click_scope_button(page, page.locator("body"), "新建定时任务")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            r["hints"].append("任务名称=" + fill_by_label(page, dlg, "任务名称", SCHED))
            r["hints"].append("Cron=" + fill_by_label(page, dlg, "Cron 表达式", "0 8 * * *"))
            r["hints"].append("关联套件=" + choose_select(page, dlg, "关联套件", SUITE))
            r["hints"].append("描述=" + fill_by_label(page, dlg, "描述", f"定时-{ts}"))
            try:
                sw = dlg.locator(".el-switch")
                if sw.count() > 0 and "is-checked" not in (sw.first.get_attribute("class") or ""):
                    sw.first.click()
                    r["hints"].append("启用开关已打开")
            except Exception:
                pass
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1800)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            sched500 = any(("schedules" in a["url"] and a["status"] == 500) for a in api_log[s0:])
            if sched500 or any("服务器内部错误" in t for t in toasts):
                r["result"] = f"缺陷复现：新建定时任务 POST /schedules 500 服务器内部错误；toast={toasts}；任务未创建"
                r["verdict"] = "FAIL"
                r["hints"].insert(0, "缺陷：新建定时任务返回 500 服务器内部错误（cron 变体均复现，与参数无关）")
            else:
                try:
                    tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                    r["result"] = f"toast={toasts}；表含sched={SCHED in tbody}、cron={'0 8 * * *' in tbody}、套件={SUITE in tbody}、启用={'启用' in tbody}"
                    r["verdict"] = "PASS" if (SCHED in tbody and SUITE in tbody) else "PARTIAL"
                except Exception as e:
                    r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC10.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC10.png")
    return finalize(r, page, api_log[s0:])

def tc11(page):
    r = make_result("TC11", "定时任务：新建必填校验（Cron 表达式为空）",
                    "项目详情 → 定时任务 → 新建定时任务 → Cron 留空 → 确认创建",
                    "出现「请输入 Cron 表达式」提示或按钮禁用；弹窗不关闭；未创建任务")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/schedules")
        click_scope_button(page, page.locator("body"), "新建定时任务")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            r["hints"].append("任务名称=" + fill_by_label(page, dlg, "任务名称", f"sched_empty_cron_{ts}"))
            r["hints"].append("关联套件=" + choose_select(page, dlg, "关联套件", SUITE))
            click_scope_button(page, dlg, "确认创建")
            page.wait_for_timeout(1200)
            errs = form_errors(page, dlg)
            toasts = grab_toasts(page)
            still_open = visible_dialog(page) is not None
            r["result"] = f"校验提示={errs}；toast={toasts}；弹窗仍打开={still_open}"
            r["verdict"] = "PASS" if (errs or toasts) and still_open else "FAIL"
            close_dialog(page)
        r["screenshot"] = shot(page, "explore-TC11.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC11.png")
    return finalize(r, page, api_log[s0:])

def tc12(page):
    r = make_result("TC12", "API Token：创建 Token 成功",
                    "项目详情 → 设置 → API Token → 创建 Token → 填名称 → 创建",
                    "toast 创建成功；Token 列表出现 token_<ts>；Token 前缀展示")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/settings/tokens")
        click_scope_button(page, page.locator("body"), "创建 Token")
        page.wait_for_timeout(700)
        dlg = visible_dialog(page)
        if dlg is None:
            r["result"] = "未出现弹窗"; r["verdict"] = "FAIL"
        else:
            page.fill("input[placeholder='例如: github-ci-token']", TOKEN)
            click_scope_button(page, dlg, "创建")
            page.wait_for_timeout(1800)
            toasts = grab_toasts(page)
            r["hints"].append("toast=" + json.dumps(toasts, ensure_ascii=False))
            show_dlg = visible_dialog(page)
            if show_dlg is not None:
                dtxt = clean(show_dlg.inner_text())
                r["hints"].append("Token展示弹窗文本=" + dtxt[:200])
                close_dialog(page)
                page.wait_for_timeout(600)
            try:
                tbody = clean(page.locator(".el-table__body").first.inner_text()) if page.locator(".el-table__body").count() else ""
                r["result"] = f"toast={toasts}；表含token={TOKEN in tbody}"
                r["verdict"] = "PASS" if TOKEN in tbody else "PARTIAL"
            except Exception as e:
                r["result"] = f"toast={toasts}；列表验证异常: {str(e)[:100]}"; r["verdict"] = "PARTIAL"
        r["screenshot"] = shot(page, "explore-TC12.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC12.png")
    return finalize(r, page, api_log[s0:])

def tc13(page):
    r = make_result("TC13", "异常现象确认：API 测试页「新建」按钮点击无响应",
                    "项目详情 → API 测试页 → hover 新建按钮 → 点击 → 观察弹窗/跳转/DOM 变化",
                    "点击「新建」应弹出对话框或跳转；若无响应则确认异常（OBS 候选）")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/api")
        url_before = page.url
        dlg_before = visible_dialog(page) is not None
        body_before = body_excerpt(page, 200)
        btn = page.locator("button:has-text('新建')").first
        try:
            btn.hover()
            page.wait_for_timeout(900)
            tips = []
            poppers = page.locator(".el-popper:visible, .el-tooltip__popper:visible")
            for i in range(poppers.count()):
                t = clean(poppers.nth(i).inner_text())
                if t and t not in tips and len(t) < 80:
                    tips.append(t)
            r["hints"].append("hover tooltip=" + json.dumps(tips, ensure_ascii=False))
        except Exception as e:
            r["hints"].append(f"hover异常: {str(e)[:60]}")
        shot(page, "explore-TC13-hover.png")
        def page_state():
            _dlgs = []
            try:
                for _i in range(page.locator(".el-dialog").count()):
                    _d = page.locator(".el-dialog").nth(_i)
                    if _d.is_visible():
                        _dlgs.append("d")
            except Exception:
                pass
            return {
                "url": page.url,
                "dialogs": _dlgs,
                "new_form": page.locator("input[placeholder='请输入用例名称']").count() > 0,
                "drawer": page.locator(".el-drawer:visible").count() > 0,
            }
        st_before = page_state()
        btn.click()
        page.wait_for_timeout(2000)
        st_after = page_state()
        changed = st_before != st_after
        r["hints"].append("状态对比=" + json.dumps({"before": st_before, "after": st_after}, ensure_ascii=False))
        r["result"] = f"点击后：弹窗出现={len(st_after['dialogs'])>0}、URL变化={st_before['url']!=st_after['url']}、状态变化={changed}"
        if changed or st_after["dialogs"] or st_after["new_form"]:
            r["verdict"] = "PASS"
        else:
            r["verdict"] = "FAIL"
            r["hints"].insert(0, "OBS 候选确认：API 测试页「新建」按钮点击无响应")
        r["screenshot"] = shot(page, "explore-TC13.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC13.png")
    return finalize(r, page, api_log[s0:])

def tc14(page):
    r = make_result("TC14", "异常现象确认：CI/CD 页面两表格表头混排",
                    "项目详情 → 设置 → CI/CD 集成 (/settings/ci) → 检查最近 CI 触发表格列头",
                    "「最近 CI 触发」应只显示 ID/触发/套件/状态/时间/操作；若混入 API Token 列则异常（OBS 候选）")
    s0 = len(api_log)
    try:
        goto(page, f"{BASE}/projects/{PID}/settings/ci")
        ths = page.locator(".el-table__header th")
        headers = [clean(ths.nth(k).inner_text()) for k in range(ths.count())]
        headers = [h for h in headers if h]
        r["hints"].append("表头=" + json.dumps(headers, ensure_ascii=False))
        token_cols = ["名称", "Token 前缀", "最后使用", "创建时间"]
        has_token = any(c in headers for c in token_cols)
        has_ci = any(c in headers for c in ["触发", "套件"])
        mixed = has_token and has_ci and len(headers) > 6
        r["result"] = f"表头={headers}；含API Token列={has_token}；含CI列={has_ci}；疑似混排={mixed}"
        if mixed:
            r["verdict"] = "FAIL"
            r["hints"].insert(0, "OBS 候选确认：CI/CD 页面两表格表头混排")
        else:
            r["verdict"] = "PASS"
        r["screenshot"] = shot(page, "explore-TC14.png")
    except Exception as e:
        r["result"] = f"执行异常: {str(e)[:200]}"; r["verdict"] = "BLOCKED"
        r["screenshot"] = shot(page, "explore-TC14.png")
    return finalize(r, page, api_log[s0:])

# ================= 主流程 =================

def main():
    global ts, RUN_AT, PROJ, CASE, SUITE, ENV, KW, TOKEN, SCHED
    part = 1
    if "--part" in sys.argv:
        idx = sys.argv.index("--part")
        part = int(sys.argv[idx + 1])
    ts_file = os.path.join(OUT_DIR, "explore-ts.txt")
    if part == 1:
        ts = time.strftime("%Y%m%d%H%M%S")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write(ts)
    else:
        try:
            with open(ts_file, "r", encoding="utf-8") as f:
                ts = f.read().strip()
        except Exception:
            ts = time.strftime("%Y%m%d%H%M%S")
    RUN_AT = time.strftime("%Y-%m-%d %H:%M:%S")
    PROJ = f"proj_{ts}"
    CASE = f"case_{ts}"
    SUITE = f"suite_{ts}"
    ENV = f"env_{ts}"
    KW = f"kw_{ts}"
    TOKEN = f"token_{ts}"
    SCHED = f"sched_{ts}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = new_context(browser, use_auth=(part in (2, 3)))
        page = ctx.new_page()
        page.set_default_timeout(15000)
        page.on("dialog", lambda d: (results_ctx and results_ctx[-1].setdefault("dialogs", []).append(d.message), d.accept()))
        page.on("response", on_response)

        if part == 1:
            login(page)
            ctx.storage_state(path=AUTH_PATH)
            print("[OK] 登录态已保存:", AUTH_PATH, flush=True)

        results_ctx = []

        if part == 1:
            for fn in [tc01, tc02, tc03, tc04, tc05]:
                r = fn(page)
                results_ctx.append(r)
                print(f"{r['id']} | {r['verdict']:7s} | {r['result'][:90]}", flush=True)
            dump = os.path.join(OUT_DIR, "explore-test-results-part1.json").replace("\\", "/")
            with open(dump, "w", encoding="utf-8") as f:
                json.dump({"ts": ts, "run_at": RUN_AT, "script": SCRIPT, "results": results_ctx}, f, ensure_ascii=False, indent=2)
            print("part1 输出:", dump, flush=True)
        elif part == 2:
            for fn in [tc06, tc07, tc08, tc09, tc10]:
                r = fn(page)
                results_ctx.append(r)
                print(f"{r['id']} | {r['verdict']:7s} | {r['result'][:90]}", flush=True)
            dump = os.path.join(OUT_DIR, "explore-test-results-part2.json").replace("\\", "/")
            with open(dump, "w", encoding="utf-8") as f:
                json.dump({"ts": ts, "run_at": RUN_AT, "script": SCRIPT, "results": results_ctx}, f, ensure_ascii=False, indent=2)
            print("part2 输出:", dump, flush=True)
        elif part == 3:
            for fn in [tc11, tc12, tc13, tc14]:
                r = fn(page)
                results_ctx.append(r)
                print(f"{r['id']} | {r['verdict']:7s} | {r['result'][:90]}", flush=True)
            # 合并
            all_results = []
            for pf in ["explore-test-results-part1.json", "explore-test-results-part2.json"]:
                pf_path = os.path.join(OUT_DIR, pf)
                if os.path.exists(pf_path):
                    with open(pf_path, "r", encoding="utf-8") as f:
                        all_results.extend(json.load(f)["results"])
            all_results.extend(results_ctx)
            dump = os.path.join(OUT_DIR, "explore-test-results.json").replace("\\", "/")
            with open(dump, "w", encoding="utf-8") as f:
                json.dump({"ts": ts, "run_at": RUN_AT, "script": SCRIPT, "results": all_results}, f, ensure_ascii=False, indent=2)
            print("最终输出:", dump, flush=True)
            print("\n===== 汇总 =====")
            for rr in all_results:
                print(f"{rr['id']} | {rr['verdict']:7s} | {rr['desc'][:28]} | {rr['result'][:80]}", flush=True)
        browser.close()

# 用于 dialog handler 的全局容器
results_ctx = []

if __name__ == "__main__":
    main()
