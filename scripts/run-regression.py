# -*- coding: utf-8 -*-
"""回归驱动：本地/CI 通用，串行执行 测试→报告→归档。
用法: python scripts/run-regression.py [--module login|register|all] [--archive]
"""
import argparse
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

PLAN = {
    "login": [
        ("登录回归", ".reasonix/tmp/test-login-cases-v3.py", []),
        ("登录报告", ".reasonix/tmp/gen-report.py", ["login", "3"]),
    ],
    "register": [
        ("注册回归", ".reasonix/tmp/test-register-cases-v4.py", []),
        ("注册报告", ".reasonix/tmp/gen-report.py", ["register", "4"]),
    ],
}


def run_step(name, script, args):
    print(f"\n▶ {name}: python {script} {' '.join(args)}")
    r = subprocess.run([PY, os.path.join(ROOT, script), *args],
                       env={**os.environ, "TEST_WS": ROOT}, cwd=ROOT)
    if r.returncode != 0:
        print(f"  ✗ {name} 失败 (exit={r.returncode})")
        sys.exit(r.returncode)
    print(f"  ✓ {name} 完成")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", choices=["login", "register", "all"], default="all")
    args = ap.parse_args()
    mods = ["login", "register"] if args.module == "all" else [args.module]
    print(f"回归开始: 模块={mods} TEST_WS={ROOT}")
    for m in mods:
        for step in PLAN[m]:
            run_step(*step)
    print("\n✅ 回归全部完成。报告在: " + ROOT)


if __name__ == "__main__":
    main()
