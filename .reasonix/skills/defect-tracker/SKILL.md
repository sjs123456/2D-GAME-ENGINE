---
name: defect-tracker
description: 缺陷登记与跟踪：测试问题入库 JSON，支持复测核对（reproduced/verified 状态流转）、摘要汇报，每轮测试后自动核对。触发词：登记缺陷、缺陷跟踪、缺陷管理、更新缺陷状态。
---

# Skill: defect-tracker

缺陷登记与跟踪：将测试发现的问题登记入库（JSON），支持复测核对、状态流转、摘要汇报。与 web-automation 的「缺陷复测确认」环节衔接，每轮复测后必须核对更新。

## 数据文件

`.reasonix/tmp/defects.json`（不存在则初始化空数组；读写统一 `encoding="utf-8"`，`indent=2`）

## 数据结构

```json
{
  "id": "BUG-001",
  "title": "登录失败时前端无任何错误提示",
  "severity": "中",
  "module": "login",
  "status": "reproduced",
  "impact_cases": ["TC02", "TC03"],
  "description": "登录接口返回 401 时前端不渲染任何提示，用户无法得知失败原因",
  "repro_steps": "输入错误密码或不存在账号 → 点击登录",
  "expected": "页面提示「用户名或密码错误」",
  "actual": "页面无任何变化，仅 API 401",
  "evidence": [".reasonix/tmp/login-TC02-v3.png"],
  "discovered": {"round": 1, "time": "2026-08-06 20:21"},
  "last_check": {"round": 3, "time": "2026-08-07 09:40", "result": "reproduced"},
  "notes": ""
}
```

## 状态机

```
new → reproduced → fixed → verified → closed
```
- 复测**仍复现**：`status=reproduced`，更新 `last_check`
- 复测**不再复现**：`status=verified`（疑似修复，需人工确认后 `closed`）
- 修复后回归通过：人工标记 `verified` → `closed`

## 工作流程

1. 读 `defects.json`；无则初始化为 `[]`。
2. 按用户指令执行操作：
   - **register 登记**：新缺陷 → 分配 ID（模块前缀 `BUG`/`OBS` + 序号，取现有最大 +1）、填全字段、`evidence` 必须含可复现证据（截图/日志/API 响应）、`status=new`。
   - **recheck 复测核对**：按模块找出所有缺陷，对照本轮结果逐一更新 `last_check`（本轮仍复现 → `reproduced`；本轮未复现 → 核实后 `verified`）。**每轮测试后必做**。
   - **fix / close 状态更新**：人工指令标记。
   - **summary 摘要**：输出缺陷总览表（ID / 严重度 / 模块 / 状态 / 影响用例 / 最近核对）。
3. 写回 `defects.json`。
4. 汇报：本次操作内容 + 缺陷总览表。

## 规则

- ID 规范：`BUG-序号`（功能缺陷）/ `OBS-序号`（观察项/体验问题）；序号按模块内现有最大 +1，不重复。
- 同现象不重复登记：登记前先按 `title`/`description` 关键词查重。
- 严重度：高（阻塞主流程）/ 中（功能缺陷有影响）/ 低（体验/文案）/ 观察（安全或潜在风险）。
- 每轮复测后必须执行 recheck（衔接 web-automation 汇报中的缺陷复现确认），保证缺陷状态实时。

## 完成标准

- `defects.json` 更新且 JSON 有效（`json.load` 校验通过）
- 汇报含：本次操作（登记/核对/更新）、缺陷总览表（ID/严重度/模块/状态/影响用例/最近核对）
