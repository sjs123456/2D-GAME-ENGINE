---
name: generate-test-report
description: 把测试结果（JSON + 截图）汇总成自包含 HTML 测试报告：统计、步骤级记录含内嵌截图、用例明细、API 记录、缺陷与结论。报告版本与数据版本对齐，可追溯历史。触发词：生成测试报告、测试报告、报告生成。
---

# Skill: generate-test-report

将测试执行结果（结果 JSON + 截图 PNG）汇总生成**自包含 HTML 测试报告**：统计卡片、步骤级操作记录（含内嵌截图）、用例明细表、API 响应记录、缺陷报告、结论建议。单文件可离线分享。报告与数据版本对齐、保留历史，可追溯每次执行。

## 何时使用

- 用户说「生成测试报告」「汇总测试结果」「把刚才的测试出个报告」
- 已有 `web-automation` 测试产生的 `*-results.json` 和截图时

## 输入约定

- **结果 JSON**：优先取**最新版本**（`.reasonix/tmp/` 下 `{模块}-test-results-vN.json`，版本号最大者；无版本后缀视为 v1）。数组，每元素一条用例，字段（缺省容错）：
  ```json
  {"id":"TC01","desc":"用例描述","step":"操作步骤","expect":"预期结果","result":"实际结果",
   "url":"最终URL","title":"页面标题","verdict":"PASS|FAIL|BLOCKED",
   "screenshot":"截图绝对路径","api_responses":[[200,"http://..."], ...],"hints":["提示文案"],
   "script":"test-xxx-cases-v2.py","run_at":"2026-08-06 20:55:00"}
  ```
  `script`/`run_at` 为 web-automation 追加的追溯字段，报告头部展示。
- **截图**：PNG 文件，路径由 JSON 的 `screenshot` 字段给出；JSON 缺失时从 `.reasonix/tmp/` 按 `{id}[-vN].png` 模式匹配。

## 工作流程

1. **收集数据**：在 `.reasonix/tmp/` 定位结果 JSON（默认最新版本；用户指定历史版本时按其指定，如 `-v1.json`），读取全部用例；确认截图文件存在（缺失的截图在报告中标注「截图缺失」，不中断）。
2. **统计**：PASS / FAIL / BLOCKED 数量、通过率。
3. **生成 HTML**（Python 脚本，放 `.reasonix/tmp/`）：
   - 截图用 base64 内嵌：`data:image/png;base64,...`，`max-width:720px`
   - 报告输出到**工作区根目录**，文件名格式：`{被测对象}-自动化测试报告[-vN].html`，**版本号与数据版本一致**（数据 v2 → 报告 v2；无版本数据 → 无后缀或 v1）
4. **验证**（必做，见下方清单）。
5. **汇报**：报告路径、大小、PASS/FAIL 统计、报告中包含的截图数、对应数据版本。

## HTML 报告模板（章节顺序）

```
头部：被测对象/地址、页面标题、生成时间、执行引擎
      数据来源：结果 JSON 文件名（版本）+ 执行脚本名 + 执行时间（来自 script/run_at 字段，如有）
统计卡片：用例总数 | PASS | FAIL | BLOCKED | 通过率
一、测试目标与范围（简述覆盖场景；复测时注明轮次与对比对象）
二、执行过程（步骤级）：每步一个卡片 = 步骤标题 + 操作meta + 结果描述 + 内嵌截图
三、用例明细汇总表：用例 | 描述 | 操作 | 预期 | 实际 | 判定徽章（绿PASS/红FAIL）
四、后端 API 响应记录表：用例 | HTTP状态码（着色）| 接口
五、缺陷报告（有 FAIL/BLOCKED 或观察项时）：BUG/OBS-xxx 编号 + 影响用例 + 复现 + 实际/预期 + 定位建议
六、测试结论与建议
页脚：生成方式说明 + 数据版本
```

样式：`Microsoft YaHei` 字体、蓝色系头部渐变、白色卡片圆角、表格 `#e4e7ed` 边框。判定徽章用圆角色块（PASS 绿 `#67c23a` / FAIL 红 `#f56c6c` / BLOCKED 橙 `#e6a23c`）。

## 关键坑（务必遵守）

1. **输出路径显式化**：报告输出路径用**绝对路径常量**写在脚本顶部（`OUT = os.path.join(os.getcwd(), "xxx报告.html")`），或由参数传入。
   ⚠️ 禁止用 `os.path.dirname(os.path.abspath(__file__))` 推导输出目录——脚本以相对路径运行时 `__file__` 基于 cwd 解析，会**偏移一层**导致报告写进 `.reasonix/` 之类的错误目录（实测踩坑）。
2. **编码**：写文件 `encoding="utf-8"`；脚本顶部加 `sys.stdout` UTF-8 包装，避免 Windows 控制台中文报错。
3. **f-string 内嵌 HTML**：`{}` 转义用 `{{ }}`；大段 HTML 用 `f"""..."""`，避免 `+` 拼接地狱。
4. **截图缺失容错**：`img_tag()` 里 `open` 前先 `os.path.exists`，不存在则返回占位 `<p style="color:#e6a23c">⚠ 截图缺失：{name}</p>`。
5. **版本对齐**：报告文件名、头部数据来源、页脚版本三处必须一致，并与结果 JSON 版本对应。

## 验证清单（生成后必跑）

```bash
python -c "
from pathlib import Path
p = Path(r'<报告绝对路径>')
html = p.read_text(encoding='utf-8')
assert p.exists() and p.stat().st_size > 50000, '文件过小'
assert html.count('data:image/png;base64') >= 1, '无内嵌截图'
for kw in ['TC01', 'PASS', 'FAIL']: assert kw in html, f'缺关键内容: {kw}'
assert html.rstrip().endswith('</html>'), 'HTML 未闭合'
print('报告验证通过:', p.stat().st_size, 'bytes')
"
```

## 完成标准

- 报告在指定路径生成、验证通过（大小合理、截图内嵌、关键内容齐全、标签闭合）
- 报告版本与数据版本对齐，头部含数据来源（JSON/脚本/时间，如有）
- 汇报含：路径、大小、截图数、PASS/FAIL/BLOCKED 统计
