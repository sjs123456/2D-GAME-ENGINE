# -*- coding: utf-8 -*-
"""补丁2：TC03 判定兼容表格类型列显示 'Web'"""
import io

path = ".reasonix/tmp/explore-cases-v1.py"
src = io.open(path, encoding="utf-8").read()

old = '''                r["result"] = f"toast={toasts}；URL={page.url}；表含case={CASE in tbody}、Web={'Web 测试' in tbody}、活跃={'活跃' in tbody}、P1={'P1' in tbody}"
                r["verdict"] = "PASS" if (CASE in tbody and "Web 测试" in tbody and "活跃" in tbody) else "PARTIAL"'''
new = '''                web_col = ("Web 测试" in tbody) or ("Web" in tbody)
                r["hints"].append("表格类型列显示 Web（等价 Web 测试）")
                r["result"] = f"toast={toasts}；URL={page.url}；表含case={CASE in tbody}、Web={web_col}、活跃={'活跃' in tbody}、P1={'P1' in tbody}"
                r["verdict"] = "PASS" if (CASE in tbody and web_col and "活跃" in tbody and "P1" in tbody) else "PARTIAL"'''
assert old in src, "锚点未找到"
src = src.replace(old, new)
io.open(path, "w", encoding="utf-8").write(src)
print("补丁2完成")
