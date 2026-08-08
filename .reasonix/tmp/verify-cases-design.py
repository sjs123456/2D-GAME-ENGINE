import json, sys
from collections import Counter

d = json.load(open('explore-cases-design.json', encoding='utf-8'))
print('用例数:', len(d))
print('优先级:', dict(Counter(x['priority'] for x in d)))
print('ID:', [x['id'] for x in d])
req = ['id', 'priority', 'desc', 'precondition', 'input', 'step', 'expect', 'verify']
for x in d:
    miss = [k for k in req if k not in x]
    assert not miss, (x['id'], miss)
print('字段完整性: OK')
# 动态数据占位符检查
placeholders = ['proj_<ts>', 'case_<ts>', 'suite_<ts>', 'env_<ts>', 'kw_<ts>', 'token_<ts>', 'sched_<ts>']
joined = json.dumps(d, ensure_ascii=False)
for p in placeholders:
    print(f'{p}: {"命中" if p in joined else "缺失!"}')
