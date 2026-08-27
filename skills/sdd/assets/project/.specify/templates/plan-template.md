# 实施计划：[FEATURE]

**分支**：`[###-feature-name]` | **日期**：[DATE] | **规格**：[link]

**输入**：来自 `/specs/[###-feature-name]/spec.md` 的功能规格

**说明**：本模板由 `$speckit-plan` 命令填写；该命令的定义描述了执行工作流。

## 摘要

[Extract from feature spec: primary requirement + technical approach from research]

## 技术上下文

<!--
  需要操作：用项目的具体技术细节替换本节内容。
  此处结构仅作为建议，用于指导迭代过程。
-->

**语言/版本**：[e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**主要依赖**：[e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**存储**：[if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**测试**：[e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**目标平台**：[e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**项目类型**：[e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**性能目标**：[domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**约束**：[domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**规模/范围**：[domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

<!-- SDD_BROWNFIELD_SAFETY_V1:plan-template -->

## 现有实现与项目惯例 *（已有项目必填）*

<!--
  必须先检查同一个类/组件，再检查同模块和同项目的同类实现。
  引用真实符号、文件和测试；不要用通用“最佳实践”替代项目证据。
-->

### 惯例证据

| 关注点 | 同类现有实现（符号 + 路径） | 本次沿用的惯例 |
|--------|-----------------------------|----------------|
| [命名/分层/错误处理/日志/测试等] | `[symbol]` — `path/to/file` | [具体惯例] |

### 复用决策

| 需求触点 | 最近的现有符号/路径 | 决策（复用/扩展/新增） | `NM-###`（仅新增） | 依据 |
|----------|---------------------|------------------------|---------------------|------|
| [FR-###] | `[symbol]` — `path/to/file` | [复用/扩展] | — | [为何满足需求] |

新增 method/class/module/endpoint/schema/helper/dependency 时，必须分配稳定的 `NM-###`，并在“依据”中记录搜索范围、拒绝复用的具体原因、考虑过的候选，以及将遵循的既有样例。缺少编号或证据时不得新增。

### 影响面与变更预算

| 触点 | 现有调用方/契约 | 允许修改的既有文件 | 必要的新文件 | 兼容/迁移要求 |
|------|-----------------|--------------------|--------------|---------------|
| [touchpoint] | [callers/contracts] | [paths] | [paths or none] | [requirement] |

Bug 修复不得夹带无关重构、改名、搬目录或格式化；新功能也只修改获批影响面内的文件。

### 根因到方案追踪 *（Bug 修复必填）*

<!--
  只接受 spec.md 中有可复核证据且状态为“已确认”的 RC-###。
  每项变更必须说明切断因果链的位置；不能用方案反推或替换根因。
-->

| `BUG-###` / `RC-###` | 已确认根因与证据 | 因果链阻断点 | 最小变更触点 | 检测缺口补强 | 范围外 |
|----------------------|------------------|--------------|--------------|--------------|--------|
| `BUG-001` / `RC-001` | [来自 spec 的结论和证据] | [阻止第一个错误状态产生或传播的位置] | [现有符号/准确路径] | [新增/扩展的回归保护] | [不由本修复处理的事项] |

任一 `RC-###` 未确认、证据无法解释复现，或方案没有直接命中因果链时，计划状态必须为 blocked。

## 回归验证矩阵 *（必填）*

| 追踪项 | 修复/变更前基线 | 实现后验证 | 测试路径/命令 | 预期结果 |
|--------|-----------------|------------|---------------|----------|
| PB-001 | [当前通过证据] | [同一验证] | `[test path or command]` | 保持通过 |
| FR-001 | [现状] | [新增行为测试] | `[test path or command]` | 满足需求 |
| BUG-001 | 修复前稳定失败 | 修复后通过 | `[regression test]` | 仅目标缺陷被修复 |
| RC-001 | [因果链/第一个错误点证据] | [根因被切断且证据仍成立] | `[diagnostic/regression command]` | 根因结论未被实现证据推翻 |

必须包含项目已有的标准 lint/typecheck/build/test 命令。必需验证无法运行时，计划状态为 blocked，不能把它降级成备注。

## 宪章检查

*关卡：必须在阶段 0 研究前通过；阶段 1 设计后重新检查。*

[Gates determined based on constitution file]

## 项目结构

### 文档（本功能）

```text
specs/[###-feature]/
├── plan.md              # 本文件（$speckit-plan 命令输出）
├── research.md          # 阶段 0 输出（$speckit-plan 命令）
├── data-model.md        # 阶段 1 输出（$speckit-plan 命令）
├── quickstart.md        # 阶段 1 输出（$speckit-plan 命令）
├── contracts/           # 阶段 1 输出（$speckit-plan 命令）
└── tasks.md             # 阶段 2 输出（$speckit-tasks 命令；不由 $speckit-plan 创建）
```

### 源代码（仓库根目录）
<!--
  需要操作：先记录并沿用仓库已有布局；默认修改现有文件和结构，而不是创建一套新目录。
  只有复用决策表证明不存在合适位置且用户批准计划后，才允许新增目录/层。
  用本功能的具体布局替换下面的占位树。
  删除未使用的选项，并用真实路径扩展选定结构，例如 apps/admin、packages/something。
  最终交付的计划中不得包含“选项”标签。
-->

```text
# [REMOVE IF UNUSED] 用仓库中本次实际触达的现有路径替换本说明
path/to/existing/module.ext       # existing Class.method / function
path/to/adjacent/module.ext       # project convention evidence
path/to/existing/test.ext         # PB-### baseline and regression

# 只有明确 Greenfield，或 NM-### 已证明现有布局无安全放置点时，才列出获批的新路径。
# 不得从模板推导 models/services/controllers、frontend/backend 或其他平行分层。
```

**结构决策**：[Document the selected structure and reference the real directories captured above]

## 复杂度跟踪

> **仅当宪章检查存在必须论证的违规时填写**

| 违规 | 必要原因 | 拒绝更简单替代方案的原因 |
|---|---|---|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., NM-001 new abstraction] | [specific constraint in current code] | [searched candidates and why reuse is unsafe] |
