# -*- coding: utf-8 -*-
"""对 explore-cases-v1.py 打补丁：
1) tc03 添加测试步骤
2) ts 跨 part 一致（explore-ts.txt）
"""
import io, re

path = ".reasonix/tmp/explore-cases-v1.py"
src = io.open(path, encoding="utf-8").read()

# 补丁1：tc03 添加步骤
old1 = '''            r["hints"].append("前置=" + fill_by_label(page, None, "前置条件", f"前置条件-{ts}"))
            page.wait_for_timeout(300)'''
new1 = '''            r["hints"].append("前置=" + fill_by_label(page, None, "前置条件", f"前置条件-{ts}"))
            # 系统要求至少一个测试步骤（用例设计未含步骤字段，动态补充）
            try:
                page.locator("button:has-text('+ 添加步骤')").first.click()
                page.wait_for_timeout(600)
                page.fill("input[placeholder='步骤说明']", "打开首页并验证标题")
                r["hints"].append("已添加测试步骤（步骤说明）")
            except Exception as e:
                r["hints"].append(f"添加测试步骤失败: {str(e)[:80]}")
            page.wait_for_timeout(300)'''
assert old1 in src, "补丁1 锚点未找到"
src = src.replace(old1, new1)

# 补丁2：ts 跨 part 一致
old2 = '''def main():
    part = 1
    if "--part" in sys.argv:
        idx = sys.argv.index("--part")
        part = int(sys.argv[idx + 1])'''
new2 = '''def main():
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
    SCHED = f"sched_{ts}"'''
assert old2 in src, "补丁2 锚点未找到"
src = src.replace(old2, new2)

io.open(path, "w", encoding="utf-8").write(src)
print("补丁完成")
