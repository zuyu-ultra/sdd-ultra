---
name: speckit-tasks
description: 根据当前功能已有的设计产物，生成可直接执行、按依赖排序并以用户故事为核心组织的中文 tasks.md；对存量项目强制复用旧实现、保护既有行为并建立不可跳过的防回归任务。
---

# 任务生成

## 后续交接

- **一致性分析**：本阶段在请求任务批准前必须实际调用 `$speckit-analyze`，并把当前 `tasks.md` 与分析结果一起交给用户审阅；不得把分析留成可选后续步骤。
- **实施项目**：调用 `$speckit-implement`，提示“按阶段开始实施”。

## 脚本映射

根据项目安装的脚本类型选择对应脚本；本中文版 Skill 默认优先使用 Python：

```text
sh: scripts/bash/setup-tasks.sh --json
ps: scripts/powershell/setup-tasks.ps1 -Json
py: scripts/python/setup_tasks.py --json
```

## 用户输入

```text
$ARGUMENTS
```

继续之前，**必须**考虑非空的用户输入。

## 执行前检查

### 本地零 Git 命令策略（最高优先级）

读取 `.specify/task-management.json`。如果 `backend` 为 `local` 或 `vcs` 为 `none`，本阶段不得执行 `git`、检查 `.git`、读取 remote/branch/status/diff/log，且 before/after hooks 中所有 `speckit.git.*` 或会启动 `git` 的钩子一律跳过；此规则覆盖钩子的强制标志。

### 计划批准关卡（阻塞）

- 只有用户在看到当前 `plan.md` 和设计产物后明确回复“批准计划”或等价表达，才能生成任务。
- 如果当前对话中没有该批准证据，或 `spec.md`/`plan.md` 在批准后发生实质修改，报告当前路径并询问是否批准，然后**停止**。
- 读取 `.specify/task-management.json`。缺失时先询问用户选择 `local` 或 `gitlab` 并停止；不得根据 remote 自动选择。
- GitLab 模式必须包含用户确认的精确项目 URL 或 `group/project`，但本阶段仍只生成 `tasks.md`，不得创建 Issues。

**检查扩展钩子（生成任务前）**：

- 在实际执行每个 hook 前，对当前 `spec.md`、`plan.md`、已有 `tasks.md`（若存在）、constitution，以及 plan 点名的源码/测试路径分别计算 SHA-256；记录 hook ID、路径和摘要。不得用 Git 取得快照。

- 检查项目根目录是否存在 `.specify/extensions.yml`。
- 如果存在，读取该文件并查找 `hooks.before_tasks` 键下的条目。
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
    输出上述区块后，**必须**在当前 agent/session 中以自己执行命令时相同的方式实际调用该钩子，并等待其完成，然后重新计算同一组 SHA-256。实际调用形式可能不同于上面显示的规范 `{command}` ID；在 Codex skills 模式下使用 `$speckit-...`。仅输出区块并不会运行钩子。
    - `spec.md` 或 `plan.md` 变化：当前计划批准立即失效，报告 hook 与变化路径并停止；必须返回对应阶段重新批准。
    - constitution、源码或测试变化：计划证据和影响面失效，停止并返回 `$speckit-plan` 重建基线。
    - 仅已有 `tasks.md` 变化：不得沿用旧报告；后续必须从变化后的当前版本重新生成并验证任务。
- 上述逐 hook 的 SHA-256、批准失效、重验和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；`optional` 只决定是否自动执行，不能降低安全关卡。可选钩子一旦被执行，必须等待完成并应用完全相同的前后哈希比较。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。

## 大纲

1. **设置**：从仓库根目录运行 `{SCRIPT}`，解析 `FEATURE_DIR`、`TASKS_TEMPLATE_CONTENT`、`TASKS_TEMPLATE` 和 `AVAILABLE_DOCS` 列表。提供时，`FEATURE_DIR` 和 `TASKS_TEMPLATE` 必须是绝对路径。`AVAILABLE_DOCS` 是 `FEATURE_DIR` 下可用的文档名称/相对路径列表，例如 `research.md` 或 `contracts/`。对于参数中类似 "I'm Groot" 的单引号，使用转义语法，例如 `'I'\''m Groot'`；如有可能，也可使用双引号：`"I'm Groot"`。

2. **加载设计文档**：从 `FEATURE_DIR` 读取：
   - **必需**：`plan.md`（技术栈、库、结构）、`spec.md`（带优先级的用户故事）。
   - **可选**：`data-model.md`（实体）、`contracts/`（接口契约）、`research.md`（决策）、`quickstart.md`（测试场景）。
   - **如果存在**：加载 `/memory/constitution.md`，获取项目原则和治理约束。
   - 注意：并非所有项目都有全部文档。根据实际可用的文档生成任务。
   - 模板、replace override、preset、extension 或 hook 不得削弱存量兼容红线。即使解析后的模板或旧 `tasks.md` 缺少安全章节，也必须主动加入复用证据、`PB-###`、`NM-###`、基线和回归任务。

3. **执行任务生成工作流**：
   - 加载 `plan.md`，提取技术栈、库和项目结构。
   - 加载 `spec.md`，提取用户故事及其优先级（P1、P2、P3 等）。
   - 如果存在 `data-model.md`：提取实体并映射到用户故事。
   - 如果存在 `contracts/`：把接口契约映射到用户故事。
   - 如果存在 `research.md`：提取决策，用于生成设置任务。
   - 从 `spec.md` 提取全部 `PB-###`、允许/禁止改变边界和 Bug 复现；从 `plan.md` 提取现有符号、调用方、项目惯例、复用决策、所有 `NM-###` 与回归验证矩阵。
   - 先执行阻塞校验：每个代码触点必须引用将复用/扩展的现有符号与准确路径，或引用已获计划批准的 `NM-###`；每个 `PB-###` 必须有变更前后验证。缺任一项时停止并要求修订计划。
   - 按用户故事组织生成任务（参见下面的“任务生成规则”）。
   - 生成依赖图，显示用户故事的完成顺序。
   - 为每个用户故事创建并行执行示例。
   - 验证任务完整性：每个用户故事都包含全部必要任务，并且可以独立测试。

4. **生成 `tasks.md`**：使用上述 JSON 输出中的 `TASKS_TEMPLATE_CONTENT` 作为结构。为兼容不输出 `TASKS_TEMPLATE_CONTENT` 的旧版设置脚本，改为读取 `TASKS_TEMPLATE`。填充以下内容：
   - 来自 `plan.md` 的正确功能名称。
   - 阶段 1：存量基线与复用确认；仅明确的 Greenfield 项目才使用项目初始化任务。
   - 阶段 2：基础任务（所有用户故事共同依赖的阻塞性前置条件），优先扩展既有基础能力。
   - 阶段 3+：每个用户故事各占一个阶段，按 `spec.md` 中的优先级排序。
   - 每个阶段包括：故事目标、独立测试标准、必需的保护/复现/目标测试和实施任务。
   - 最终阶段：完善与横切关注点。
   - 所有任务必须遵守严格的 checklist 格式（参见下面的“任务生成规则”）。
   - 每项任务都有清晰的文件路径。
   - Dependencies 部分显示故事完成顺序。
   - 每个故事都有并行执行示例。
   - Implementation Strategy 部分说明 MVP 优先与增量交付。

## 强制执行后钩子

**向用户报告完成之前，必须完成本节。**

检查项目根目录是否存在 `.specify/extensions.yml`。

- 在实际执行每个 after hook 前，对当前 `spec.md`、`plan.md`、`tasks.md`、constitution，以及 plan 点名的源码/测试路径分别计算 SHA-256，并记录 hook ID。

- 如果不存在，或 `hooks.after_tasks` 下没有注册钩子，则跳到“完成报告”。
- 如果存在，读取该文件并查找 `hooks.after_tasks` 键下的条目。
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
    输出上述区块后，**必须**在当前 agent/session 中以自己执行命令时相同的方式实际调用该钩子，并等待其完成，然后重新计算同一组 SHA-256。实际调用形式可能不同于上面显示的规范 `{command}` ID；在 Codex skills 模式下使用 `$speckit-...`。仅输出区块并不会运行钩子。
    - `spec.md`、`plan.md`、constitution、源码或测试发生变化：当前任务结果和上游批准失效，停止并返回拥有变化的阶段；不得请求批准陈旧的 `tasks.md`。
    - `tasks.md` 发生变化：从 post-hook 当前版本重新执行格式、复用/`NM-###`、`PB-###`、基线和回归完整性校验，然后对该精确版本重新运行 `$speckit-analyze`。
    - 同一 hook 在重新校验后再次改变被跟踪输入时，停止并报告不稳定 hook；不得循环执行或放行。
  - **可选钩子**（`optional: true`）：
    ```text
    ## 扩展钩子

    **可选钩子**：{extension}
    命令：`$speckit-...`（由 {command} 转换）
    描述：{description}

    提示：{prompt}
    如需执行：`$speckit-...`（由 {command} 转换）
    ```

- 上述逐 hook 的 SHA-256、批准/报告失效、完整重验和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；可选钩子一旦被执行，必须等待完成并按同一规则比较前后摘要。

## 完成报告

完成全部 after hook 和 post-hook 校验后，先在同一 session 中对当前精确版本实际调用 `$speckit-analyze`，等待其完成，并记录被分析的 `spec.md`、`plan.md`、`tasks.md` SHA-256。分析不得由模型自行概括替代。

- 如果分析报告包含任一 `CRITICAL`，任务关卡失败：展示当前 `tasks.md` 路径、分析发现与应返回的阶段，然后停止。不得询问“是否仍批准”、不得调用 implement 或同步 Issues。
- 如果分析期间或其 hook 改变任一被分析产物/证据文件，分析报告立即失效；必须按 `$speckit-analyze` 的稳定性规则重验。无法得到稳定报告时停止。
- 只有当前三个产物 SHA-256 与分析所用版本完全一致且 `CRITICAL` 数为 0，才输出生成的 `tasks.md` 路径、分析报告和以下摘要：

- 任务总数。
- 每个用户故事的任务数。
- 识别出的并行机会。
- 每个故事的独立测试标准。
- 建议的 MVP 范围（通常只有 User Story 1）。
- 格式验证：确认**所有**任务都遵循 checklist 格式（checkbox、ID、labels、file paths）。
   - 当前任务管理后端；GitLab 模式还要显示精确项目目标，但不得显示凭据。
   - 复用/扩展任务数、所有 `NM-###` 新建例外、`PB-###` 覆盖率、Bug 复现任务、变更前基线与最终回归任务。

展示当前 `tasks.md` 摘要与针对同一 SHA-256 版本的分析结果后，最后询问：“请同时审阅当前 `tasks.md` 与一致性分析。是否批准按此任务清单执行？请回复‘批准任务’，或指出需要修改的内容。”然后**停止**。不得在同一轮自动调用 `$speckit-implement` 或 `$speckit-taskstoissues`。GitLab 模式只有在任务获批并再次确认精确项目写入后，才能同步 Issues。

任务生成上下文：`{ARGS}`

`tasks.md` 必须可以立即执行——每项任务都必须足够具体，使 LLM 无需额外上下文即可完成。

## 任务生成规则

**关键要求**：任务**必须**按用户故事组织，以便独立实施和测试。

**存量验证不可选**：凡会改变源码行为，必须生成变更前基线、目标验证和变更后回归任务。新需求必须覆盖所有受影响 `PB-###`；Bug 修复必须先生成会因正确原因失败的复现任务，再做最小修复，并验证相邻正常/边界路径和项目标准测试。若项目没有自动测试，必须生成可重复的特征验证；若无法运行可靠验证，则任务清单必须把它标为阻塞，不能进入实现。

### Checklist 格式（必需）

每项任务都**必须**严格使用以下格式：

```text
- [ ] [TaskID] [P?] [Story?] 带文件路径的描述
```

**格式组成**：

1. **Checkbox**：始终以 `- [ ]`（Markdown checkbox）开头。
2. **Task ID**：按执行顺序使用连续编号（T001、T002、T003……）。
3. **`[P]` 标记**：仅当任务可并行执行时加入（修改不同文件，并且不依赖尚未完成的任务）。
4. **`[Story]` 标签**：仅用户故事阶段任务必需。
   - 格式为 `[US1]`、`[US2]`、`[US3]` 等，与 `spec.md` 中的用户故事对应。
   - 设置阶段：没有 story label。
   - 基础阶段：没有 story label。
   - 用户故事阶段：必须有 story label。
   - 完善阶段：没有 story label。
5. **描述**：包含清晰动作与准确文件路径。

**示例**：

- ✅ 正确：`- [ ] T001 运行 tests/existing/test_user.py 并记录变更前基线退出码`
- ✅ 正确：`- [ ] T005 [P] 在 src/middleware/auth.py 扩展现有 authorize()，保持 PB-002 错误语义`
- ✅ 正确：`- [ ] T012 [P] [US1] 在 src/models/user.py 复用 User.normalize_name() 实现 FR-003`
- ✅ 正确：`- [ ] T014 [US1] 按 NM-001 在 src/services/user_service.py 添加获批 helper，并补 tests/services/test_user_service.py`
- ❌ 错误：`- [ ] 扩展 User.normalize_name()`（缺少 ID、Story label 和 file path）
- ❌ 错误：`T001 [US1] 创建模型`（缺少 checkbox）
- ❌ 错误：`- [ ] [US1] 扩展 User.normalize_name()`（缺少 Task ID 和 file path）
- ❌ 错误：`- [ ] T001 [US1] 创建模型`（缺少 file path）

### 任务组织

1. **来自用户故事（`spec.md`）——首要组织方式**：
   - 每个用户故事（P1、P2、P3……）各自占一个阶段。
   - 把所有相关触点映射到它服务的故事：现有符号/准确路径、受影响调用方、`PB-###`、目标测试和必要的 `NM-###`；不得强套 Model/Service/Endpoint 分层。
   - 标记故事依赖关系；大多数故事应当彼此独立。

2. **来自契约**：
   - 把每份接口契约映射到它服务的用户故事。
   - 每份受影响接口契约在该故事阶段的实施任务之前对应保护旧契约和验证新需求的测试任务。

3. **来自数据模型**：
   - 把每个实体映射到需要它的用户故事。
   - 如果实体服务多个故事：放入最早的故事或设置阶段。
   - 把关系转换成相应用户故事阶段中沿用现有调用链/数据访问层的任务；项目没有 service layer 时不得为此新建一层。

4. **来自设置/基础设施**：
   - 共享基础设施 → 设置阶段（阶段 1）。
   - 基础性/阻塞性任务 → 基础阶段（阶段 2）。
   - 故事专属的设置 → 放在该故事阶段内。

### 阶段结构

- **阶段 1**：存量基线、目标类/模块惯例和复用确认；仅明确 Greenfield 才是项目初始化。
- **阶段 2**：基础（阻塞性前置条件——必须在用户故事之前完成）。
- **阶段 3+**：按优先级排序的用户故事（P1、P2、P3……）。
  - 每个故事内部：`PB-###` 保护/失败复现 → 复用或获批 `NM-###` 实施 → 目标/相邻测试 → 回归验证；结构遵循当前项目真实调用链。
  - 每个阶段都应形成完整、可独立测试的增量。
- **最终阶段**：完善与横切关注点。

## 完成条件

- [ ] 已生成包含所有阶段、任务 ID 和文件路径的 `tasks.md`。
- [ ] 每个代码任务均引用现有符号或已批准的 `NM-###`；所有 `PB-###`、Bug 复现、相邻场景和项目标准回归均有可执行任务。
- [ ] 已确认模板/override/hook 没有削弱红线；验证不可用或计划证据缺失时已阻止进入实现。
- [ ] 每个实际 hook 均有前后 SHA-256；变化已使旧批准/报告失效并完成重验或阻断。
- [ ] 已对当前精确 `tasks.md` 强制运行 `$speckit-analyze`；存在 CRITICAL 时已阻断，零 CRITICAL 时才展示 tasks 与分析并请求批准。
- [ ] 已按照上面“强制执行后钩子”的规则分派或跳过扩展钩子。
- [ ] 已向用户报告任务总数、故事拆分和 MVP 范围。
- [ ] 已请求用户批准当前任务清单，并在批准前停止实现与 Issue 同步。
