# -*- coding: utf-8 -*-
"""test-assets-mcp：测试资产登记与报告归档 MCP server（Reasonix [[plugins]] stdio）

工具：
  assets_list(module)         模块资产版本清单 + 下次版本号
  assets_read_json(module, version)  读取指定版本结果 JSON
  assets_register(module, version, script, json_file, screenshots)  登记资产
  report_archive(module, version)    归档报告到 reports/ 并更新索引
  report_index()              已归档报告清单

命令行：python test-assets-mcp.py --init   # 扫描现有资产初始化 index.json 并归档报告（不进 MCP 模式）
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None

WS = r"C:\Users\ahusj\claude-code-vibe\test-ds-v4-flash"      # 工作区根（绝对路径常量）
TMP = os.path.join(WS, ".reasonix", "tmp")                     # 测试资产仓库
INDEX = os.path.join(WS, ".reasonix", "assets-index.json")     # 资产登记表
REPORTS = os.path.join(WS, "reports")                          # 报告归档目录


def load_index():
    if os.path.exists(INDEX):
        return json.load(open(INDEX, encoding="utf-8"))
    return {}


def save_index(data):
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def version_of(name):
    m = re.search(r"-v(\d+)\.", name)
    return int(m.group(1)) if m else 1


def scan_module(module):
    """扫描 .reasonix/tmp/ 下某模块的全部资产"""
    prefix = f"test-{module}-cases"
    entries = {"scripts": [], "results": [], "screenshots": 0, "reports": []}
    if os.path.isdir(TMP):
        for f in sorted(os.listdir(TMP)):
            if f.startswith(prefix) and f.endswith(".py"):
                entries["scripts"].append(f)
            elif f.startswith(f"{module}-test-results") and f.endswith(".json"):
                entries["results"].append(f)
            elif f.startswith(f"{module}-TC") and f.endswith(".png"):
                entries["screenshots"] += 1
    if os.path.isdir(REPORTS):
        for f in sorted(os.listdir(REPORTS)):
            if f.startswith(f"{module}-") and f.endswith(".html"):
                entries["reports"].append(f)
    ver = max([version_of(x) for x in entries["scripts"] + entries["results"]], default=0)
    entries["latest_version"] = ver
    entries["next_version"] = ver + 1
    return entries


def init_index():
    """扫描现有资产，初始化/更新 index.json（幂等）"""
    index = load_index()
    for module in ("login", "register"):
        index[module] = scan_module(module)
    # 归档报告（工作区根目录中的历史报告）
    for f in os.listdir(WS):
        if f.startswith("自动化测试平台-") and f.endswith(".html"):
            m2 = re.search(r"(登录|注册)页自动化测试报告(-v\d+)?\.html", f)
            if m2:
                mod = "login" if m2.group(1) == "登录" else "register"
                src = os.path.join(WS, f)
                dst = os.path.join(REPORTS, f)
                if os.path.abspath(src) != os.path.abspath(dst) and os.path.exists(src):
                    os.makedirs(REPORTS, exist_ok=True)
                    import shutil
                    shutil.copy2(src, dst)
                    if f not in index[mod]["reports"]:
                        index[mod]["reports"].append(f)
    save_index(index)
    return index


def build_report_index_html():
    index = load_index()
    rows = ""
    for mod, info in sorted(index.items()):
        for r in sorted(info.get("reports", [])):
            rows += f'<tr><td>{mod}</td><td><a href="{r}">{r}</a></td><td>{r.replace("自动化测试平台-","").replace(".html","")}</td></tr>'
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"/><title>测试报告索引</title>
<style>body{{font-family:"Microsoft YaHei",sans-serif;max-width:900px;margin:40px auto;padding:0 16px;}}
table{{border-collapse:collapse;width:100%;}} th,td{{border:1px solid #e4e7ed;padding:8px 12px;text-align:left;}}
th{{background:#f0f4f9;}}</style></head><body>
<h2>自动化测试平台 · 测试报告索引</h2>
<p>更新于 {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
<table><tr><th>模块</th><th>报告</th><th>版本</th></tr>{rows}</table>
</body></html>"""
    with open(os.path.join(REPORTS, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.join(REPORTS, "index.html")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        idx = init_index()
        idx_path = build_report_index_html()
        print("index.json 已更新，模块:", list(idx.keys()))
        print("报告索引:", idx_path)
        for mod, info in idx.items():
            print(f"  {mod}: latest=v{info['latest_version']} next=v{info['next_version']} "
                  f"脚本{len(info['scripts'])} 结果{len(info['results'])} 截图{info['screenshots']} 报告{len(info['reports'])}")
        return
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test-assets-mcp",
                  instructions="测试资产登记与报告归档：查询模块资产版本清单、读取结果 JSON、登记新资产、归档报告。")

    @mcp.tool()
    def assets_list(module: str) -> dict:
        """查询某模块（login/register）的资产版本清单，返回脚本/结果/截图/报告及下次版本号。"""
        module = module.lower()
        info = scan_module(module)
        return {"module": module, **info}

    @mcp.tool()
    def assets_read_json(module: str, version: int) -> str:
        """读取指定模块、指定版本的测试结果 JSON 内容（字符串）。"""
        path = os.path.join(TMP, f"{module}-test-results-v{version}.json")
        if not os.path.exists(path):
            return f"ERROR: {os.path.basename(path)} 不存在"
        return open(path, encoding="utf-8").read()

    @mcp.tool()
    def assets_register(module: str, version: int, script: str, json_file: str, screenshots: int = 0) -> str:
        """登记一轮新产出的测试资产（脚本名/结果 JSON 文件名/截图数），更新登记表。"""
        index = load_index()
        info = index.setdefault(module, scan_module(module))
        if script and script not in info["scripts"]:
            info["scripts"].append(script)
        if json_file and json_file not in info["results"]:
            info["results"].append(json_file)
        info["screenshots"] = max(info.get("screenshots", 0), screenshots)
        info = scan_module(module)
        index[module] = info
        save_index(index)
        return f"已登记 {module} v{version}: script={script} json={json_file} 截图={screenshots}"

    @mcp.tool()
    def report_archive(module: str, version: int) -> str:
        """把工作区根目录的报告归档到 reports/ 并重建索引页。"""
        name = f"自动化测试平台-{'登录' if module == 'login' else '注册'}页自动化测试报告-v{version}.html"
        src = os.path.join(WS, name)
        if not os.path.exists(src):
            return f"ERROR: {name} 不存在于工作区根目录"
        os.makedirs(REPORTS, exist_ok=True)
        import shutil
        dst = os.path.join(REPORTS, name)
        shutil.copy2(src, dst)
        index = load_index()
        info = index.setdefault(module, scan_module(module))
        if name not in info["reports"]:
            info["reports"].append(name)
        save_index(index)
        idx_path = build_report_index_html()
        return f"已归档 {dst}\n索引: {idx_path}"

    @mcp.tool()
    def report_index() -> str:
        """列出全部已归档报告（模块/文件名/版本）。"""
        index = load_index()
        out = []
        for mod, info in sorted(index.items()):
            for r in sorted(info.get("reports", [])):
                out.append(f"{mod} | {r}")
        return "\n".join(out) if out else "暂无归档报告"

    mcp.run()


if __name__ == "__main__":
    main()
