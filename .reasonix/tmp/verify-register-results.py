# -*- coding: utf-8 -*-
"""验证 register-test-results.json 格式与截图文件完整性"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(OUT, 'register-test-results.json'), encoding='utf-8'))
print('用例数:', len(d))
keys = set()
for r in d:
    keys |= set(r.keys())
print('字段集合:', sorted(keys))
verdicts = {}
for r in d:
    verdicts[r['verdict']] = verdicts.get(r['verdict'], 0) + 1
print('verdict 统计:', verdicts)
print()
for r in d:
    ok = os.path.isfile(r['screenshot']) and os.path.getsize(r['screenshot']) > 0
    print(f"{r['id']} {r['verdict']:7s} 截图存在={ok} {os.path.basename(r['screenshot'])} API={len(r['api_responses'])}条 hints={len(r['hints'])}条 url={r['url']}")
for f in ['register-page.png', 'register-page-empty-submit.png', 'register-form-info.json']:
    p = os.path.join(OUT, f)
    if os.path.isfile(p):
        print(f, '存在, 大小 =', os.path.getsize(p))
    else:
        print(f, '缺失!')
