# [CHECKLIST TYPE] 检查表：[FEATURE NAME]

**目的**：[Brief description of what this checklist covers]
**创建日期**：[DATE]
**功能**：[Link to spec.md or relevant documentation]

**说明**：此自定义检查表由 `$speckit-checklist` 命令根据功能上下文和需求生成。
**审查所有权**：本检查表是由审查者负责的需求质量审查产物。只有当审查者判定需求质量准则已经满足时，才将项目标记为 `[x]`。
**标记语义**：`[x]` 表示该准则已完成审查，并满足需求质量要求；它不表示实现工作已经完成。

<!--
  ============================================================================
  重要：下面的检查项只是用于说明格式的示例。

  $speckit-checklist 命令必须根据以下内容，用真实检查项替换它们：
  - 用户提出的具体检查表请求
  - spec.md 中的功能需求
  - plan.md 中的技术上下文
  - tasks.md 中的实现细节
  - 已有项目的 PB-### 受保护行为、复用决策、项目惯例和回归验证矩阵
  - Bug 的 BUG-### / RC-###、事实时间线、复现证据、因果链、根因置信度和检测缺口

  生成的检查表文件中不得保留这些示例检查项。
  ============================================================================
-->

## [Category 1]

- [ ] CHK001 第一个具有清晰审查动作的检查项
- [ ] CHK002 第二个检查项
- [ ] CHK003 第三个检查项

## [Category 2]

- [ ] CHK004 另一个类别中的检查项
- [ ] CHK005 带有具体判定准则的检查项
- [ ] CHK006 本类别的最后一个检查项

<!-- SDD_BROWNFIELD_SAFETY_V1:checklist-template -->

## 存量兼容与回归（已有项目必含）

- [ ] CHK007 是否清晰定义了所有受影响旧行为的 PB-### 保护要求？[Coverage]
- [ ] CHK008 是否要求先检索并优先复用同类/同项目现有实现？[Completeness]
- [ ] CHK009 是否定义了新功能和 Bug 修复的基线、相邻场景与回归阻断条件？[Measurability]
- [ ] CHK010 Bug 规格是否在写方案前记录了可复核的 `BUG-###`/`RC-###`、完整因果链、根因置信度与检测缺口？[Completeness, Root Cause]
- [ ] CHK011 未确认根因是否明确阻断 plan/tasks/implement，而没有被写成既定事实？[Consistency, Gate]

## 说明

- 只有在审查确认需求质量准则已满足后，才将项目标记为 `[x]`
- 仍需澄清、修正或审查者判断的项目必须保持未勾选
- `$speckit-implement` 把检查表 checkbox 状态作为关卡读取，且不得修改这些标记
- `checklists/requirements.md` 有独立的内置生命周期，由 `$speckit-specify` 和 `$speckit-clarify` 维护
- 在行内添加评论或发现
- 链接到相关资源或文档
- 检查项按顺序编号，以便引用
