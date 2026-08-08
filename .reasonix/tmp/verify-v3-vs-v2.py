# -*- coding: utf-8 -*-
"""校验 v3 与 v2 脚本：比较 import 之后的代码主体是否完全一致（含版本号规范化）"""
import re, difflib, os

HERE = os.path.dirname(os.path.abspath(__file__))
v2 = open(os.path.join(HERE, 'test-login-cases-v2.py'), encoding='utf-8').read()
v3 = open(os.path.join(HERE, 'test-login-cases-v3.py'), encoding='utf-8').read()

def norm(s):
    s = re.sub(r'v\d', 'VN', s)
    s = re.sub(r'"script": "test-login-cases-VN\.py"', '"script": X', s)
    return s

a = norm(v2)
b = norm(v3)
# 从 import sys 开始取代码主体（跳过 docstring）
a_body = a[a.index('import sys'):]
b_body = b[b.index('import sys'):]
if a_body == b_body:
    print('PASS: v2 与 v3 代码主体（import 之后）除版本号/script 字段外完全一致')
else:
    print('DIFF FOUND in code body:')
    for line in difflib.unified_diff(a_body.splitlines(), b_body.splitlines(), lineterm=''):
        print(line)
