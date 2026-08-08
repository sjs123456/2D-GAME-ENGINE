# -*- coding: utf-8 -*-
"""将 test-register-cases-v2.py 的动态部分替换为 v3 版本。
只改：账号前缀 / JSON 版本 / 截图版本 / 上轮对比文件 / 上轮已存在账号 / 文案版本标注。
用例输入与判定逻辑保持与 v2 完全一致。
"""
import io

SRC = "test-register-cases-v3.py"

REPL = [
    # --- 文件头注释 ---
    ("注册功能第二轮复测（回归测试）", "注册功能第三轮复测（回归测试）"),
    ("与上轮 register-test-results.json 完全相同的 12 条用例与判定逻辑，验证结果稳定性与缺陷复现。",
     "与上轮 register-test-results-v2.json 完全相同的 12 条用例与判定逻辑，验证结果稳定性与缺陷复现。"),
    ("输出: register-test-results-v2.json（字段与上轮完全一致）+ register-TC{NN}-v2.png",
     "输出: register-test-results-v3.json（字段与上轮完全一致）+ register-TC{NN}-v3.png"),
    ("末尾与上轮 verdict 逐条对比", "末尾与上轮 v2 verdict 逐条对比"),
    # --- 文件路径 ---
    ('PREV_JSON = os.path.join(OUT_DIR, "register-test-results.json")',
     'PREV_JSON = os.path.join(OUT_DIR, "register-test-results-v2.json")'),
    ('NEW_JSON = os.path.join(OUT_DIR, "register-test-results-v2.json")',
     'NEW_JSON = os.path.join(OUT_DIR, "register-test-results-v3.json")'),
    # --- 唯一账号：本轮 testuser_v3_<时间戳> ---
    ('REG_USER = f"testuser_retest_{SUFFIX}"   # testuser_复测+时间戳（retest=复测，符合字母数字下划线规则）',
     'REG_USER = f"testuser_v3_{SUFFIX}"   # testuser_v3+时间戳（本轮第三轮，符合字母数字下划线规则）'),
    # --- 上轮(v2)已存在账号，TC05b 补充验证 ---
    ('PREV_EXIST_USER = "testuser_202608062048216900"  # 上轮已存在账号，补充验证',
     'PREV_EXIST_USER = "testuser_retest_202608062055097400"  # 上轮(v2)已存在账号，补充验证'),
    # --- 截图版本 v2 -> v3 ---
    ('os.path.join(OUT_DIR, "register-TC12-v2.png")',
     'os.path.join(OUT_DIR, "register-TC12-v3.png")'),
    ("os.path.join(OUT_DIR, f\"register-{case['id']}-v2.png\")",
     "os.path.join(OUT_DIR, f\"register-{case['id']}-v3.png\")"),
    ('os.path.join(OUT_DIR, "register-TC05b-v2.png")',
     'os.path.join(OUT_DIR, "register-TC05b-v3.png")'),
    # --- TC05b 描述文案 ---
    ('extra["desc"] = "用户名已存在（上轮账号补充验证）"',
     'extra["desc"] = "用户名已存在（v2已存在账号补充验证）"'),
    # --- 汇总标题 / 打印文案 ---
    ("注册功能第二轮复测汇总表", "注册功能第三轮复测汇总表"),
    ('print(f"本轮唯一测试账号(复测): {REG_USER} / {REG_EMAIL} / {REG_PWD}")',
     'print(f"本轮唯一测试账号(v3): {REG_USER} / {REG_EMAIL} / {REG_PWD}")'),
    ('print(f"上轮已存在账号(补充验证): {PREV_EXIST_USER}\\n")',
     'print(f"上轮(v2)已存在账号(补充验证): {PREV_EXIST_USER}\\n")'),
    ('print("\\n[补充] TC05b 用户名已存在(上轮账号 testuser_202608062048216900 补充验证)：")',
     'print("\\n[补充] TC05b 用户名已存在(上轮账号 testuser_retest_202608062055097400 补充验证)：")'),
    # --- 与上轮对比文案 ---
    ('print("与上轮 verdict 对比（复测稳定性）")',
     'print("与上轮 v2 verdict 对比（复测稳定性）")'),
    ('print(f"12条 verdict 全部一致: {all_same}")',
     'print(f"12条 verdict 与 v2 全部一致: {all_same}")'),
]

with io.open(SRC, "r", encoding="utf-8") as f:
    text = f.read()

unmatched = []
for old, new in REPL:
    if old in text:
        text = text.replace(old, new)
    else:
        unmatched.append(old)

with io.open(SRC, "w", encoding="utf-8") as f:
    f.write(text)

print("替换完成。未匹配的旧串数:", len(unmatched))
for u in unmatched:
    print("  [UNMATCHED]", u[:100])
