# -*- coding: utf-8 -*-
"""case-runner：步骤化用例 JSON 执行引擎（Playwright）。
CLI:  python case-runner.py --cases <用例定义JSON> [--out <输出目录>] [--only TC01,TC02] [--headed] [--report]
MCP:  暴露 case_execute / case_report 工具（reasonix.toml [[plugins]]）
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS = os.environ.get("TEST_WS", r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash")
TMP = os.path.join(WS, ".reasonix", "tmp")
INDEX = os.path.join(WS, ".reasonix", "assets-index.json")
GEN_REPORT = os.path.join(TMP, "gen-report.py")

PAGE_TIMEOUT = 30000
STEP_TIMEOUT = 15000


def next_version(module):
    if os.path.exists(INDEX):
        info = json.load(open(INDEX, encoding="utf-8")).get(module)
        if info:
            return info.get("latest_version", 1) + 1
    return 1


def load_cases(cases_file):
    data = json.load(open(cases_file, encoding="utf-8"))
    assert "meta" in data and "cases" in data, "用例文件需含 meta 与 cases"
    return data


def build_context(meta, ts):
    pid = meta.get("project_id", "")
    return {
        "base_url": meta["base_url"],
        "ts": ts,
        "pid": pid,
    }


def resolve(value, ctx):
    if isinstance(value, str):
        return (value.replace(meta_ts(ctx), ctx["ts"])
                    .replace("{pid}", ctx["pid"]))
    return value


def meta_ts(ctx):
    return "<ts>"


def install_toast_catcher(page):
    page.add_init_script("""
    window.__toasts = [];
    const obs = new MutationObserver(() => {
        document.querySelectorAll('.el-message, .el-message__content').forEach(el => {
            const t = el.textContent.trim();
            if (t && !window.__toasts.includes(t)) window.__toasts.push(t);
        });
    });
    obs.observe(document.body, {childList: true, subtree: true});
    """)


def do_login(page, meta, ctx):
    page.goto(meta["base_url"] + meta["login"]["url"], wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
    page.fill(meta["login"]["username_selector"], meta["login"]["username"])
    page.fill(meta["login"]["password_selector"], meta["login"]["password"])
    page.click(meta["login"]["submit_selector"])
    page.wait_for_url("**" + meta["login"].get("success_url", "/dashboard"), timeout=STEP_TIMEOUT)
    print("  ✓ 登录成功:", meta["login"]["username"])


def run_case(page, case, ctx):
    rid = case["id"]
    result = {
        "id": rid, "desc": case["desc"],
        "step": " → ".join(f"{s.get('action')}({s.get('selector','') or s.get('url','')})" for s in case["steps"]),
        "expect": case["expect"], "result": "", "url": "", "title": "",
        "verdict": "BLOCKED", "screenshot": "",
        "api_responses": [], "hints": [], "dialogs": [], "body_excerpt": "",
        "script": os.path.basename(__file__), "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    apis = []

    def on_resp(resp):
        if "/api/" in resp.url:
            apis.append({"status": resp.status, "url": resp.url, "method": resp.request.method})
    page.on("response", on_resp)

    try:
        for i, s in enumerate(case["steps"]):
            act = s["action"]
            if act == "goto":
                url = resolve(s["url"], ctx)
                page.goto(url if url.startswith("http") else ctx["base_url"] + url,
                          wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            elif act == "click":
                page.click(resolve(s["selector"], ctx), timeout=STEP_TIMEOUT)
            elif act == "fill":
                page.fill(resolve(s["selector"], ctx), resolve(s["value"], ctx), timeout=STEP_TIMEOUT)
            elif act == "select_first":
                sel = page.locator(resolve(s["selector"], ctx)).first
                options = sel.locator("option")
                n = options.count()
                if n > 1:
                    sel.select_option(index=1)  # 跳过 placeholder/请选择
                elif n == 1:
                    sel.select_option(index=0)
            elif act == "wait":
                page.wait_for_timeout(int(s.get("ms", 1000)))
            elif act == "expect":
                kind = s["kind"]
                try:
                    if kind == "toast":
                        page.wait_for_selector(".el-message", timeout=STEP_TIMEOUT)
                        texts = page.eval_on_selector_all(".el-message", "els => els.map(e => e.textContent)")
                        found = any(s["text"] in t for t in texts)
                        result["hints"].extend(t.strip() for t in texts if t.strip())
                        if not found:
                            raise AssertionError(f"toast 未出现: {s['text']} (实际: {texts})")
                    elif kind == "form_error":
                        page.wait_for_timeout(1200)
                        errs = page.eval_on_selector_all(".el-form-item__error", "els => els.map(e => e.textContent)")
                        result["hints"].extend(t.strip() for t in errs if t.strip())
                        if not any(s["text"] in t for t in errs):
                            raise AssertionError(f"表单校验提示未出现: {s['text']} (实际: {errs})")
                    elif kind == "no_toast":
                        page.wait_for_timeout(2000)
                        texts = page.eval_on_selector_all(".el-message", "els => els.map(e => e.textContent)")
                        result["hints"].extend(t.strip() for t in texts if t.strip())
                        if any(s["text"] in t for t in texts):
                            raise AssertionError(f"不应出现 toast: {s['text']} (实际: {texts})")
                    elif kind == "visible":
                        page.wait_for_selector(resolve(s["selector"], ctx), timeout=STEP_TIMEOUT)
                    elif kind == "not_visible":
                        page.wait_for_timeout(800)
                        cnt = page.locator(resolve(s["selector"], ctx)).count()
                        if cnt > 0:
                            raise AssertionError(f"元素应不可见但存在({cnt}个): {s['selector']}")
                    elif kind == "url":
                        page.wait_for_timeout(1200)
                        if s["text"] not in page.url:
                            raise AssertionError(f"URL 应包含 {s['text']}，实际: {page.url}")
                except Exception as e:
                    raise AssertionError(f"断言失败[{kind}]: {e}") from e
        # 全断言通过
        if case.get("semantic") == "defect":
            result["verdict"] = "FAIL"
            result["result"] = f"缺陷复现确认（{case.get('defect','?')}）：断言全部成立"
        else:
            result["verdict"] = "PASS"
            result["result"] = "所有断言通过"
    except AssertionError as e:
        if case.get("semantic") == "defect":
            result["verdict"] = "PASS"  # 断言失败 = 缺陷未复现
            result["result"] = f"缺陷未复现（断言失败: {e}）"
        else:
            result["verdict"] = "FAIL"
            result["result"] = f"断言失败: {e}"
    except Exception as e:
        result["verdict"] = "BLOCKED"
        result["result"] = f"执行异常: {type(e).__name__}: {e}"
    finally:
        page.remove_listener("response", on_resp)
        result["api_responses"] = apis
        result["url"] = page.url
        result["title"] = page.title()
        result["body_excerpt"] = page.evaluate("document.body.innerText.slice(0, 200)") or ""
        shot = os.path.join(ctx["out_dir"], f"{ctx['module']}-{rid}.png")
        try:
            page.screenshot(path=shot, full_page=False)
            result["screenshot"] = shot
        except Exception:
            result["screenshot"] = ""
    return result


def execute(cases_file, out_dir=None, only=None, headed=False):
    from playwright.sync_api import sync_playwright

    data = load_cases(cases_file)
    meta, cases = data["meta"], data["cases"]
    module = meta["module"]
    if only:
        allow = {x.strip() for x in only.split(",")}
        cases = [c for c in cases if c["id"] in allow]
    if not out_dir:
        out_dir = TMP
    os.makedirs(out_dir, exist_ok=True)
    ver = next_version(module)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    ctx = build_context(meta, ts)
    ctx.update({"out_dir": out_dir, "module": module})

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(STEP_TIMEOUT)
        install_toast_catcher(page)
        if meta.get("login"):
            do_login(page, meta, ctx)
        for case in cases:
            print(f"\n▶ {case['id']} {case['desc']}")
            page.goto(meta["base_url"], wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            r = run_case(page, case, ctx)
            print(f"  {'✅' if r['verdict']=='PASS' else '❌' if r['verdict']=='FAIL' else '⏸'} {r['verdict']} | {r['result'][:80]}")
            results.append(r)
        browser.close()

    out_json = os.path.join(out_dir, f"{module}-test-results-v{ver}.json")
    payload = {"ts": ts, "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "script": os.path.basename(cases_file), "results": results}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    npass = sum(1 for r in results if r["verdict"] == "PASS")
    nfail = sum(1 for r in results if r["verdict"] == "FAIL")
    print(f"\n结果: {len(results)} 条 | PASS {npass} / FAIL {nfail} / BLOCKED {len(results)-npass-nfail}")
    print("输出:", out_json)
    return out_json, ver


def generate_report(module, version):
    import subprocess
    r = subprocess.run([sys.executable, GEN_REPORT, module, str(version)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return f"报告生成失败: {r.stderr[-500:]}"
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--report", action="store_true", help="执行后生成报告")
    args = ap.parse_args()
    out_json, ver = execute(args.cases, args.out, args.only, args.headed)
    if args.report:
        module = load_cases(args.cases)["meta"]["module"]
        print(generate_report(module, ver))


def mcp_main():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("case-runner-mcp",
                  instructions="步骤化用例执行：读取用例定义 JSON（meta+cases），用 Playwright 执行并产出标准结果 JSON 与报告。")

    @mcp.tool()
    def case_execute(cases_file: str, only: str = "", out_dir: str = "") -> str:
        """执行步骤化用例定义 JSON（meta+cases），返回结果 JSON 路径与 PASS/FAIL 统计。only 例: 'TC01,TC02'"""
        out_json, ver = execute(cases_file, out_dir, only)
        return f"完成 v{ver}: {out_json}"

    @mcp.tool()
    def case_report(module: str, version: int) -> str:
        """基于结果 JSON 生成自包含 HTML 测试报告（gen-report.py）。"""
        return generate_report(module, version)

    mcp.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        mcp_main()
    else:
        main()
