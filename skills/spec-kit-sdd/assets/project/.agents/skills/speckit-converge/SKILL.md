---
name: speckit-converge
description: 对照功能产物、存量行为与项目惯例评估当前代码库，把尚未满足且不会破坏旧功能的剩余工作作为新任务追加到 tasks.md，并要求重新批准后才可实现。
---

# 实现收敛

## 用户输入

```text
$ARGUMENTS
```

如果用户输入非空，必须在继续之前加以考虑。

## 执行前检查

### 本地零 Git 命令策略（最高优先级）

读取 `.specify/task-management.json`。如果 `backend` 为 `local` 或 `vcs` 为 `none`，本阶段不得执行 `git`、检查 `.git`、读取 remote/branch/status/diff/log，且 before/after hooks 中所有 `speckit.git.*` 或会启动 `git` 的钩子一律跳过；此规则覆盖钩子的强制标志。

**检查收敛前的扩展钩子**：

- 在实际执行每个 hook 前，对 `spec.md`、`plan.md`、`tasks.md`、constitution、实施记录中全部触达的源码/测试/配置路径，以及回归矩阵点名的证据文件分别计算 SHA-256；记录 hook ID、路径与摘要。不得使用 Git。

- 检查项目根目录中是否存在 `.specify/extensions.yml`。
- 如果存在，读取该文件并查找 `hooks.before_converge` 下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并照常继续。
- 过滤掉 `enabled` 明确为 `false` 的钩子；没有 `enabled` 字段的钩子默认视为已启用。
- 对每个剩余钩子，不要尝试解释或计算 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或该字段为 null/空值，则将其视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，把条件计算留给 `HookExecutor` 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容。Codex 中调用扩展 skill 时，把规范命令 ID 中的点替换为连字符并添加 `$` 前缀，例如 `speckit.git.commit` 调用为 `$speckit-git-commit`：
  - **可选钩子**（`optional: true`）：

    ```text
    ## 扩展钩子

    **可选前置钩子**：{extension}
    命令 ID：`{command}`
    说明：{description}

    提示：{prompt}
    执行方式：使用与 `{command}` 对应的 Codex `$speckit-*` skill
    ```

  - **强制钩子**（`optional: false`）：

    ```text
    ## 扩展钩子

    **自动前置钩子**：{extension}
    正在执行：`{command}`
    EXECUTE_COMMAND: {command}

    等待钩子命令完成，然后再继续执行“目标”。
    ```

    输出上述区块后，必须实际调用钩子并等待其完成，然后重新计算同一组 SHA-256。采用当前 agent/session 中自己运行该命令时所用的方式；实际调用形式可能不同于上面显示的规范 `{command}` ID，例如 Codex skills 模式使用 `$speckit-*`。仅输出区块并不等于运行钩子。
    - `spec.md`、`plan.md` 或 constitution 变化：已批准意图失效，停止并返回对应阶段。
    - `tasks.md` 变化：旧任务批准失效；从 post-hook 精确版本重新初始化收敛，不能沿用旧任务映射。
    - 源码、测试或配置变化：重新构建调用方、复用、兼容基线和 provenance 图，并实际运行回归矩阵与项目标准命令；任一新失败立即成为 CRITICAL regression。
    - 同一 hook 在重验后再次改变跟踪输入时停止并报告不稳定 hook，不得循环放行。
- 上述逐 hook 的 SHA-256、批准失效、范围/基线重建、回归重验和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；`optional` 只决定是否自动执行。可选钩子一旦被执行，必须等待完成并应用完全相同的前后哈希比较。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。

## 目标

弥合功能规格、计划和任务所批准的**变更增量**与代码库当前实现之间的差距。`spec.md`、`plan.md` 和 `tasks.md` 定义允许改变什么；现有公开契约、未被规格明确改变的可观察行为、调用方与修改前通过的测试共同构成不可静默破坏的兼容基线，以宪章作为治理约束。评估代码当前状态，确定哪些需求尚未满足以及是否出现重复实现、项目惯例偏离或回归，然后把每一项安全、可追踪的剩余工作追加到 `tasks.md`。

只有在 `$speckit-implement` 已针对当前 `tasks.md` 运行过，并且 `$speckit-tasks` 已生成完整 `tasks.md` 后，才能运行此 skill。

这**不是** diff 工具，也**不**跟踪变更。它评估的是代码相对于功能产物的当前状态，不使用 Git，不比较分支，也不查看历史。

## 操作约束

**只能追加，绝不重写**：此 skill 的**唯一写入**是在 `tasks.md` 末尾追加新的 `## Phase N: Convergence` 章节。它不得：

- 以任何方式修改 `spec.md` 或 `plan.md`；
- 重写、重新编号、重排或删除任何已有任务，包括先前 Convergence 阶段中的任务；
- 修改、创建或删除任何应用代码；完成新追加任务是 `$speckit-implement` 的职责。

如果代码库已经满足全部要求，必须让 `tasks.md` 保持**逐字节不变**，不得添加空的 Convergence 标题，并报告干净结果。

**宪章权威性**：项目宪章（`.specify/memory/constitution.md`）**不可协商**。违反 MUST 原则的代码是最高严重度发现，并且必须生成相应的修复任务。如果宪章仍是未填写模板，应平稳跳过宪章检查，而不是失败。

## 执行步骤

### 1. 初始化收敛上下文

从仓库根目录运行一次：

```bash
python3 .specify/scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
```

解析 JSON 中的 `FEATURE_DIR` 和 `AVAILABLE_DOCS`，并派生以下绝对路径：

- `SPEC = FEATURE_DIR/spec.md`
- `PLAN = FEATURE_DIR/plan.md`
- `TASKS = FEATURE_DIR/tasks.md`
- `CONSTITUTION = .specify/memory/constitution.md`（若存在）

如果缺少 `spec.md`、`plan.md` 或 `tasks.md`，立即停止并输出清晰、可行动的消息，点名应运行的前置命令：缺少 spec 时运行 `$speckit-specify`，缺少 plan 时运行 `$speckit-plan`，缺少 tasks 时运行 `$speckit-tasks`。不得生成部分输出。

对于参数中类似 `I'm Groot` 的单引号，使用转义语法，例如 `'I'\''m Groot'`；也可以尽量改用双引号：`"I'm Groot"`。

### 2. 加载产物（渐进披露）

只从每个产物中加载最低限度的必要上下文。

**从 `spec.md` 加载：**

- 功能需求（`FR-###`）
- 成功标准（`SC-###`）：只纳入需要构建工作的项目；排除上线后的结果指标和业务 KPI
- 用户故事及其验收场景
- 边界情况（若存在）
- `PB-###`、允许/禁止改变边界、Bug 复现与相邻不变场景

**从 `plan.md` 加载：**

- 架构/技术栈选择和技术决策
- 数据模型引用
- 阶段和已命名的触点，即计划要求创建或编辑的文件/组件
- 技术约束
- 现有符号/调用方、项目惯例、复用决策、`NM-###`、变更预算和回归验证矩阵

**从 `tasks.md` 加载：**

- 任务 ID，用于计算下一个 ID 和下一个阶段号
- 描述、阶段分组和引用的文件路径

**从宪章加载**（如果不是未填写模板）：

- 原则名称和 MUST/SHOULD 规范性陈述

### 3. 构建意图清单

创建以下内部模型，不要回显原始产物：

- **需求清单**：为每条 `FR-###`、`SC-###`、用户故事验收场景（例如 `US1/AC2`），以及产生可构建义务的计划决策和宪章原则，建立一个稳定键。
- **代码范围图**：根据 `plan.md` 和 `tasks.md` 中点名的文件路径，再结合需求概念的关键词搜索，推导出评估范围内的源文件和组件集合。评估必须受这些范围约束；不要推断超出产物定义的范围。
- **兼容基线图**：将每个 `PB-###`、公开契约、受影响调用方和修改前通过的测试映射到当前实现与变更后证据。
- **复用图**：把每个新增或变更的符号映射到已批准的现有复用点或 `NM-###`；检查同类/同模块中是否已存在等价实现，并比较命名、错误处理、依赖注入和测试惯例。
- **本轮 provenance 图**：只依据可核实的实施记录、任务 ID、触达路径/符号清单及修改前 SHA-256，把本轮确实新增或改变的符号映射到任务。没有修改前证据时标记为 `provenance-unknown`，不得推断代码是本轮新增。

### 4. 评估代码库并分类发现

对意图清单中的每一项检查范围内的当前代码，只在存在差距时生成一个 `Finding`。按以下**差距类型**分类每项发现：

- **`missing`**：代码中完全不存在必需工作。
- **`partial`**：工作已经存在，但尚未完整满足需求、验收标准或计划决策。
- **`contradicts`**：代码行为与已声明意图或宪章 MUST 原则冲突。
- **`unrequested`**：代码不在当前 feature 产物中，但无法由本轮 provenance 证明是本轮引入。它只能作为信息项报告并视为可能的存量兼容基线；不得生成删除、迁移、重写或“清理”任务。
- **`regression`**：实现破坏 `PB-###`、旧公开契约、原有调用方或修改前通过的测试，或 Bug 修复引入新的失败。
- **`duplicate`**：只有本轮 provenance 能证明新增/改变的 method/class/module/helper/endpoint/schema/dependency 才可归入此类；它重复已有能力、偏离目标类/模块惯例，或没有对应的已批准 `NM-###`。provenance 未知或属于存量的代码不得归为可行动 duplicate。

每个 `Finding` 记录：稳定 ID、可追踪的 `source-ref`、`gap-type`、严重度，以及带证据（观察到的文件/区域）的简短人类可读说明。

**边界情况：**

- **代码很少或尚无代码**：把整个已规定范围视为 `missing` 剩余工作，不要失败。
- **没有任何剩余工作**：生成零项发现，并执行第 7 步中的 converged 分支。

### 5. 分配严重度

- **CRITICAL**：违反宪章 MUST，`missing`/`contradicts` 阻塞 P1 基线功能，任何 `regression`，或未经批准/存在等价旧实现的 `duplicate`。验证没有运行时不得判定安全收敛。
- **HIGH**：核心功能需求或验收标准存在 `missing` 或 `partial` 差距。
- **MEDIUM**：次要需求存在 `partial` 差距。
- **LOW**：轻微部分差距或完善事项。`unrequested`/`provenance-unknown` 仅为信息项，不分配可行动严重度，也不得据此改代码。

### 6. 在会话中展示发现摘要

追加任何内容之前，输出紧凑、按严重度分级的摘要，此时不得写文件：

```markdown
## 收敛发现

| ID | 差距类型 | 严重度 | 来源 | 证据 | 剩余工作 |
|----|----------|--------|------|------|----------|
| F1 | missing | HIGH | FR-008 | 示例：path/to/module.py 写入 tasks.md 时未检测到 append-only 防护 | 增加 append-only 强制措施 |
```

**摘要指标：**

- 已检查的需求/验收标准数量
- 已检查的计划决策数量
- 已检查的宪章原则数量，或“已跳过——模板”
- 按差距类型统计的发现数（`missing`/`partial`/`contradicts`/`unrequested`/`regression`/`duplicate`）
- `provenance-unknown` 信息项数量
- 按严重度统计的发现数

### 7. 追加收敛任务，或报告已收敛

**如果存在一项或多项可行动发现**（`tasks_appended` 结果）：

`unrequested`、`provenance-unknown` 和任何无法证明属于本轮的存量代码都不是可行动发现，不得据此追加任务。`duplicate` 只有在 provenance 完整且任务能复用既有实现、迁移本轮调用点并保持全部 `PB-###` 时才可行动。

严格按照追加契约，把内容追加到 `tasks.md` **末尾**：

1. 扫描全部已有任务 ID，令 `M` 为最大值。确定下一个阶段号 `N`，即当前最高阶段号加 1。
2. 写入一个新的章节标题 `## Phase N: Convergence`。
3. 每项可行动发现生成一个 checklist 项，按 CRITICAL/HIGH 优先排序，并分配补零 ID `T{M+1:03d}, T{M+2:03d}, …`：

   ```markdown
   - [ ] T042 <祈使语气说明> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` 把任务追踪到来源，例如 `FR-003`、`SC-002`、`US1/AC2`、`plan: storage decision`、`Constitution II`。

   `<gap-type>` 必须是 `missing`、`partial`、`contradicts`、`unrequested`、`regression` 或 `duplicate` 之一。

   每个追加的代码任务必须写明要复用/扩展的现有符号与准确路径，或引用已批准的 `NM-###`，并带对应目标测试、`PB-###`/Bug 相邻回归及项目标准验证。duplicate 任务只能消除本轮可证重复，并必须先迁移本轮调用点、保持旧实现和全部 `PB-###`；不得删除 provenance 未知或存量符号。若收敛分析发现计划外新符号需求，不得自行创建 `NM-###`；必须报告计划失效并返回 `$speckit-plan`。

   宪章违规任务必须最先输出，并明确描述为 `CRITICAL`。
4. 绝不复用或重新编号已有 ID。如果已有一个先前 Convergence 阶段，应在其下方添加另一个独立编号的新阶段，不得触碰旧阶段。

**如果没有可行动发现**（`converged` 结果）：

- 完全不要修改 `tasks.md`，也不要添加空阶段标题。
- 只有回归矩阵、受影响调用方和项目标准验证均有待步骤 10 复核的通过证据，才可形成 `converged` 暂定候选；此处不得报告最终成功。验证未运行或结果未知时必须报告阻塞，不得形成候选。
- 包含所检查内容的摘要计数。

### 8. 提供下一步行动（交接）

- 此时只准备暂定的 `tasks_appended` 或 `converged` 结果，不得向用户请求批准或报告最终收敛；必须先完成 after hook 稳定性检查和步骤 10 的实际验证。
- 暂定 `tasks_appended` 必须记录追加前后的 `tasks.md` SHA-256，并明确旧任务批准已失效。

### 9. 检查扩展钩子

生成暂定结果后，检查项目根目录中是否存在 `.specify/extensions.yml`。

- 在实际执行每个 after hook 前，对暂定结果使用的 `spec.md`、`plan.md`、`tasks.md`、constitution、源码、调用方、测试、配置和 provenance 证据分别计算 SHA-256，并记录 hook ID。

- 如果存在，读取该文件并查找 `hooks.after_converge` 下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并照常继续。
- 过滤掉 `enabled` 明确为 `false` 的钩子；没有 `enabled` 字段的钩子默认视为已启用。
- 对每个剩余钩子，不要尝试解释或计算 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或该字段为 null/空值，则将其视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，把条件计算留给 `HookExecutor` 实现。
- 可以说明结果仍为“暂定，等待 hook 后回归”，但不得在 hook 和最终验证前报告 `converged`、请求批准或建议 implement。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容：
  - **可选钩子**（`optional: true`）：

    ```text
    ## 扩展钩子

    **可选钩子**：{extension}
    命令 ID：`{command}`
    说明：{description}

    提示：{prompt}
    执行方式：使用与 `{command}` 对应的 Codex `$speckit-*` skill
    ```

  - **强制钩子**（`optional: false`）：

    ```text
    ## 扩展钩子

    **自动钩子**：{extension}
    正在执行：`{command}`
    EXECUTE_COMMAND: {command}
    ```

    输出上述区块后，必须实际调用钩子并等待其完成，然后重新计算同一组 SHA-256。采用当前 agent/session 中自己运行该命令时所用的方式；实际调用形式可能不同于上面显示的规范 `{command}` ID，例如 Codex skills 模式使用 `$speckit-*`。仅输出区块并不等于运行钩子。
    - `spec.md`、`plan.md` 或 constitution 变化：暂定结果和上游批准失效，停止并返回对应阶段。
    - `tasks.md` 变化：暂定结果与旧批准失效；从 post-hook 当前版本完整重跑收敛分析，不能展示 pre-hook 摘要。
    - 源码、测试、配置、调用方或 provenance 证据变化：暂定结果失效；重建范围、findings 和追加任务，并进入步骤 10 重验。
    - 同一 hook 在重验后再次改变跟踪输入时停止并报告不稳定 hook，不得循环放行。
- 上述逐 hook 的 SHA-256、批准/报告失效、完整重验和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；可选钩子一旦被执行，必须等待完成并按同一规则比较前后摘要。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。

### 10. Hook 后实际验证与最终报告

所有应自动执行的强制 hook 和用户选择实际执行的可选 hook 均已完成且 SHA-256 稳定后，必须从 `plan.md` 读取并**实际执行**完整回归验证矩阵，以及项目标准 lint/typecheck/build/test 命令；不得用 tasks checkbox、旧报告或“看起来通过”代替执行结果。

- 记录每条命令、退出码、修改前基线结果与当前结果。验证环境不可用、命令缺失、`PB-###`/Bug 相邻场景失败或出现任何基线之外的新失败时，结果为 CRITICAL regression，禁止报告 `converged`。
- 如果最终验证产生新的可行动 finding，把它按步骤 7 追加为 CRITICAL convergence 任务，并重新计算 `tasks.md` SHA-256；不得继续执行 implement。若追加后 hook 必须观察最终任务，则最多再执行一次 hook + 完整验证；仍发生变化或失败时停止并报告不稳定状态。
- 对最终 `tasks_appended`：展示 post-hook、post-verification 的当前 `tasks.md`、分析摘要、追加数量和 SHA-256，明确旧批准失效，然后询问用户是否批准当前任务并停止；不得在同一轮建议或调用 `$speckit-implement`。
- 对最终 `converged`：只有所有命令实际通过且当前证据 SHA-256 与验证输入一致，才报告“✅ 已收敛——实现满足获批变更且未发现存量行为回归。”并建议人工审阅；本地模式不得建议 PR 或任何 Git 命令。
