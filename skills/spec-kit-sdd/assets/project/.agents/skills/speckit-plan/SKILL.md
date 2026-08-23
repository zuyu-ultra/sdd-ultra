---
name: speckit-plan
description: 使用计划模板执行实施规划工作流，为当前功能生成完整的中文设计产物；对存量项目强制提炼同类惯例、优先复用既有符号、记录新建例外，并建立变更前后回归矩阵。
---

# 技术实施计划

## 后续交接

- **创建任务**：调用 `$speckit-tasks`，提示“把计划拆解为任务”。
- **创建检查表**：调用 `$speckit-checklist`，提示“为以下领域创建检查表……”。

## 脚本映射

根据项目安装的脚本类型选择对应脚本；本中文版 Skill 默认优先使用 Python：

```text
sh: scripts/bash/setup-plan.sh --json
ps: scripts/powershell/setup-plan.ps1 -Json
py: scripts/python/setup_plan.py --json
```

## 用户输入

```text
$ARGUMENTS
```

继续之前，**必须**考虑非空的用户输入。

## 执行前检查

### 本地零 Git 命令策略（最高优先级）

读取 `.specify/task-management.json`。如果 `backend` 为 `local` 或 `vcs` 为 `none`，本阶段不得执行 `git`、检查 `.git`、读取 remote/branch/status/diff/log，且 before/after hooks 中所有 `speckit.git.*` 或会启动 `git` 的钩子一律跳过；此规则覆盖钩子的强制标志。

### 规格批准关卡（阻塞）

- 只有用户在看到当前 `spec.md` 后明确回复“批准规格”或等价表达，才能生成计划。
- 如果当前对话中没有该批准证据，或 `spec.md` 在批准后发生实质修改，展示规格路径和简要差异，询问是否批准，然后**停止**。
- 不得把初始的“全部执行”“直接实现”等请求当作对尚未生成产物的预批准。

### Hook 产物完整性协议（所有实际执行的 before/after hook 强制）

- 在执行首个 hook 前，通过 `.specify/feature.json` 或 paths-only helper 解析当前 feature；若提前运行 helper，后续设置步骤不得重复运行。对**每一个** hook 单独建立执行前、执行后快照，不得跨 hook 合并。
- 快照至少包含 `.specify/feature.json`、`FEATURE_SPEC`、requirements checklist、`IMPL_PLAN`、`research.md`、`data-model.md`、`quickstart.md`、`contracts/` 全部普通文件和存在的 `tasks.md`；还应包含计划/研究已经引用的目标实现、调用方和测试文件。逐文件记录解析路径与 SHA-256，目录同时记录相对路径；缺失文件使用 `MISSING`。不得用 mtime、大小或 Git 状态替代。
- Hook 后重新解析路径并逐文件比较；新增、删除、重命名、解析目标变化或摘要变化都属于实质变化。无论摘要是否变化，都重新读取并重验：规格全部 `PB-###` 和调用方/公共契约、每个复用决策和 `NM-###`、影响面、变更前基线及完整回归矩阵。适用且安全的既有基线命令必须重新运行并与记录结果比较。
- `spec.md` 被 hook 改变时，规格以及 plan/tasks 批准立即失效，必须停止规划并请求重新批准规格。Plan/research/data model/contracts/quickstart 被改变时，计划和任务批准失效；`tasks.md` 被改变时任务批准失效。报告每个变化文件及前后 SHA-256。
- Hook、replace override、preset、extension 或 bundle 删除/弱化“现有实现与项目惯例”“复用决策”“影响面与变更预算”或“回归验证矩阵”时，主动恢复必需章节并完整重验；无法恢复或验证失败时立即阻断。
- 可选 hook 只展示时无需快照；用户随后实际执行时也必须在执行当下完成本协议。Hook 新写入的验证命令不得直接当作可信 shell 执行，仍须经过项目证据核对和相应代码执行授权。

**检查扩展钩子（规划前）**：

- 检查项目根目录是否存在 `.specify/extensions.yml`。
- 如果存在，读取该文件并查找 `hooks.before_plan` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并按正常流程继续。
- 过滤掉 `enabled` 被明确设为 `false` 的钩子。没有 `enabled` 字段的钩子默认视为已启用。
- 对每个剩余钩子，**不要**尝试解释或求值钩子的 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或该字段为 null/空值，则将钩子视为可执行。
  - 如果钩子定义了非空 `condition`，则跳过该钩子，把条件求值留给 HookExecutor 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容。执行已注册的 Codex Skill 时，把规范命令 ID 中的点号转换为连字符，例如 `speckit.foo` 以 `$speckit-foo` 调用：
  - **可选钩子**（`optional: true`）：
    ```text
    ## 扩展钩子

    **可选前置钩子**：{extension}
    命令：`$speckit-...`（由 {command} 转换）
    描述：{description}

    提示：{prompt}
    如需执行：`$speckit-...`（由 {command} 转换）
    ```
  - **强制钩子**（`optional: false`）：
    ```text
    ## 扩展钩子

    **自动前置钩子**：{extension}
    正在执行：`$speckit-...`（由 {command} 转换）
    EXECUTE_COMMAND: {command}

    等待钩子命令返回结果，然后再继续执行“大纲”。
    ```
    输出上述区块后，**必须**在当前 agent/session 中以自己执行命令时相同的方式实际调用该钩子，并等待其完成，然后才能继续。实际调用形式可能不同于上面显示的规范 `{command}` ID；在 Codex skills 模式下使用 `$speckit-...`。仅输出区块并不会运行钩子。
    调用前后必须完成逐 hook SHA-256 快照和全部适用重验；若规格发生变化，在重新批准规格前停止，不得进入“大纲”。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。

## 大纲

1. **设置**：从仓库根目录运行 `{SCRIPT}`，解析 JSON 中的 `FEATURE_SPEC`、`IMPL_PLAN`、`SPECS_DIR`、`BRANCH`。对于参数中类似 "I'm Groot" 的单引号，使用转义语法，例如 `'I'\''m Groot'`；如有可能，也可使用双引号：`"I'm Groot"`。

2. **加载上下文**：读取 `FEATURE_SPEC`、`/memory/constitution.md` 和当前代码库。加载 `IMPL_PLAN` 模板（已经复制完成）。已有 `plan.md`、replace 型 override、preset、extension、bundle 或 hook 都不得删除或弱化本 Skill 的存量兼容红线；模板缺少对应章节时必须主动补齐。

   在填写技术上下文前，按以下顺序执行只读证据扫描：目标类/函数 → 同模块或包 → 同业务域 → 同项目。记录相关现有符号、调用方、公开契约、配置、错误处理、命名/分层惯例、相邻测试和项目标准验证命令。外部最佳实践只能补充项目没有答案的部分，不能覆盖可工作的项目传统。

3. **执行计划工作流**：遵循 `IMPL_PLAN` 模板的结构：
   - 填写 Technical Context（把未知项标记为 `NEEDS CLARIFICATION`）。
   - 填写“现有实现与项目惯例”：每个需求触点必须选择直接复用、兼容扩展、提炼共享实现或新增。
   - 每个拟新增 method/class/module/helper/endpoint/schema/dependency 必须分配 `NM-###`，列出搜索范围、候选、不能复用的具体理由和沿用的项目样例。缺少 `NM-###` 时以 ERROR 结束。
   - 从 spec 提取全部 `PB-###`、允许/禁止改变边界和受影响调用方，填写影响面与变更预算。
   - 建立回归验证矩阵：记录变更前基线命令与预期、每个 `PB-###`/`FR-###` 的目标测试、Bug 复现与相邻边界测试，以及变更后必须运行的同一基线和项目标准 lint/typecheck/build/test。
   - 在计划阶段实际运行安全且可用的变更前基线并记录命令、退出码和已知失败。未知失败或验证环境不可用时停止并报告阻塞，不得声称计划可安全实施。
   - 根据 constitution 填写 Constitution Check 部分。
   - 评估关卡；存在没有合理理由的违规时，以 ERROR 结束。
   - 阶段 0：生成 `research.md`，解决所有 `NEEDS CLARIFICATION`。
   - 阶段 1：生成 `data-model.md`、`contracts/`、`quickstart.md`。
   - 设计完成后重新评估 Constitution Check。

## 强制执行后钩子

**向用户报告完成之前，必须完成本节。**

每个 `after_plan` hook 执行前后必须按“Hook 产物完整性协议”分别快照并比较。Hook 后无条件
重新读取规格、计划、research、data model、contracts、quickstart、检查表及存在的 tasks，
重验全部 `PB-###`、复用/扩展证据、`NM-###`、调用方、变更前基线和回归矩阵，并重新运行
安全且适用的既有基线验证。只有全部通过才能进入完成报告；任一变化按产物所有权使批准失效。

检查项目根目录是否存在 `.specify/extensions.yml`。

- 如果不存在，或 `hooks.after_plan` 下没有注册钩子，则跳到“完成报告”。
- 如果存在，读取该文件并查找 `hooks.after_plan` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并继续到“完成报告”。
- 过滤掉 `enabled` 被明确设为 `false` 的钩子。没有 `enabled` 字段的钩子默认视为已启用。
- 对每个剩余钩子，**不要**尝试解释或求值钩子的 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或该字段为 null/空值，则将钩子视为可执行。
  - 如果钩子定义了非空 `condition`，则跳过该钩子，把条件求值留给 HookExecutor 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容：
  - **强制钩子**（`optional: false`）——每个强制钩子都**必须输出 `EXECUTE_COMMAND:`**：
    ```text
    ## 扩展钩子

    **自动钩子**：{extension}
    正在执行：`$speckit-...`（由 {command} 转换）
    EXECUTE_COMMAND: {command}
    ```
    输出上述区块后，**必须**在当前 agent/session 中以自己执行命令时相同的方式实际调用该钩子，并等待其完成，然后才能继续。实际调用形式可能不同于上面显示的规范 `{command}` ID；在 Codex skills 模式下使用 `$speckit-...`。仅输出区块并不会运行钩子。
    调用前后必须完成 SHA-256 快照、重新读取、重验、基线复跑和批准失效处理；失败时立即阻断，不得进入完成报告。
  - **可选钩子**（`optional: true`）：
    ```text
    ## 扩展钩子

    **可选钩子**：{extension}
    命令：`$speckit-...`（由 {command} 转换）
    描述：{description}

    提示：{prompt}
    如需执行：`$speckit-...`（由 {command} 转换）
    ```

## 完成报告

命令在阶段 1 设计完成后结束。报告分支、`IMPL_PLAN` 路径、所有生成的产物、关键技术选择、宪章偏差与风险，并列出复用/扩展的现有符号、所有 `NM-###`、受保护 `PB-###`、变更前基线结果和回归矩阵覆盖。随后询问：“请审阅当前 `plan.md` 及设计产物。是否批准此版本进入任务拆分？请回复‘批准计划’，或指出需要修改的内容。”

输出确认问题后**必须停止**，不得在同一轮自动调用 `$speckit-tasks`。批准只适用于用户看到的当前计划版本；`spec.md` 或计划产物发生实质修改后，计划批准失效并必须重新确认。

## 阶段

### 阶段 0：大纲与研究

1. **从上面的 Technical Context 提取未知项**：
   - 每个 `NEEDS CLARIFICATION` → 一项研究任务。
   - 每个依赖 → 先定位项目中同类依赖及用法；没有项目证据时再建最佳实践研究任务。
   - 每个集成 → 先研究项目现有集成模式，再按需补充外部模式研究。
   - 每个需求触点 → 一项现有符号、调用方和相邻测试研究；每个新增候选 → 一项 `NM-###` 反重复检索。

2. **生成并分派研究 agent**：

   ```text
   对 Technical Context 中的每个未知项：
     任务："针对 {feature context} 研究 {unknown}"
   对每个技术选择：
     任务："先在目标类、同模块和同项目查找 {tech}/{domain} 的真实惯例；项目无答案时再查外部最佳实践"
   ```

3. **在 `research.md` 中汇总结论**，使用以下格式：
   - 决定：[选择了什么]
   - 理由：[为什么这样选择]
   - 考虑过的替代方案：[还评估了什么]
   - 项目证据：[现有符号、路径、调用方、测试和惯例]
   - 复用结论：[直接复用/扩展/共享提炼，或 `NM-###` 新增例外]

**输出**：所有 `NEEDS CLARIFICATION` 均已解决的 `research.md`。

### 阶段 1：设计与契约

**前置条件：** `research.md` 已完成。

1. **从功能规格中提取实体** → `data-model.md`：
   - 实体名称、字段、关系。
   - 来自需求的验证规则。
   - 适用时记录状态转换。

2. **定义接口契约**（如果项目有外部接口）→ `/contracts/`：
   - 识别项目向用户或其他系统暴露的接口。
   - 使用适合项目类型的契约格式记录接口。
   - 示例：库的 public API、CLI 工具的命令 schema、Web 服务的 endpoint、parser 的 grammar、应用程序的 UI contract。
   - 如果项目完全是内部用途（构建脚本、一次性工具等），则跳过。

3. **创建快速验证指南** → `quickstart.md`：
   - 记录可运行的验证场景，证明功能能够端到端工作。
   - 包括前置条件、设置命令、测试/运行命令和预期结果。
   - 同时包含变更前基线、功能目标验证、全部 `PB-###` 与 Bug 相邻场景，以及变更后相同的项目标准验证命令。
   - 链接或引用契约和数据模型细节，不要重复粘贴。
   - 不要包含完整实现代码、model/service/controller 的完整函数体、migration 或完整测试套件。
   - 将该产物保持为验证/运行指南；实现细节属于 `tasks.md` 和实施阶段。

**输出**：`data-model.md`、`/contracts/*`、`quickstart.md`。

## 关键规则

- 文件系统操作使用绝对路径；文档内引用使用项目相对路径。
- 关卡失败或仍有未解决的澄清项时，以 ERROR 结束。
- 发现等价旧实现、未映射的受保护行为、无测试/验证路径、未经批准的新符号或顺手重构时，以 ERROR 结束。不得用模板、override、preset、extension 或 hook 绕过。

## 完成条件

- [ ] 已执行计划工作流并生成设计产物。
- [ ] 已记录同类实现与项目惯例、复用决策、所有 `NM-###`、影响调用方和完整 `PB-###` 回归矩阵。
- [ ] 已运行并记录可重复的变更前基线；若无法运行，已阻止计划进入任务拆分。
- [ ] 已按照上面“强制执行后钩子”的规则分派或跳过扩展钩子。
- [ ] 已向用户报告分支、计划路径和生成的产物。
- [ ] 已请求用户批准当前计划，并在批准前停止。
