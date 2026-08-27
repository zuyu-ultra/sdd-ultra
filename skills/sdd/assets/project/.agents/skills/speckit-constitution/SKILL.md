---
name: speckit-constitution
description: 根据交互式输入或用户提供的原则创建或更新项目宪章；用于定义、修订并校验项目级治理原则、语义化版本和同步影响报告。
---

## 用户输入

```text
$ARGUMENTS
```

如果用户输入非空，**必须**在继续之前考虑它。

## 范围防护

本 Skill 自身的工作仅限于更新项目宪章。依赖宪章的模板和命令会在运行时读取宪章，
此处不修改它们。

- 将用户输入的每一部分分类为宪章内容或独立的非治理意图。
- 如果输入包含功能实现、代码生成、重构、构建或部署请求，**不得**执行这些请求；
  必须将其提取为延后意图。
- **不得**创建、修改或删除应用源文件、功能路由、组件、测试、部署文件或其他与宪章
  工作流无关的产物。
- 如果无法确定某条指令是否属于宪章内容，必须先请求澄清，再进行修改。
- 完成宪章更新后，为每项延后意图加入 `Next Actions` 章节。列出原始意图并建议适当的
  后续 Spec Kit Skill，例如 `$speckit-specify`，但不得调用它。
- 如果没有非治理意图，省略 `Next Actions` 章节。

## 执行前检查

### 本地零 Git 命令策略（最高优先级）

读取 `.specify/task-management.json`。如果 `backend` 为 `local` 或 `vcs` 为 `none`，本阶段不得执行 `git`、检查 `.git`、读取 remote/branch/status/diff/log，且 before/after hooks 中所有 `speckit.git.*` 或会启动 `git` 的钩子一律跳过；此规则覆盖钩子的强制标志。

**检查扩展钩子（宪章更新之前）**：

- 在实际执行每个 hook 前，分别计算并记录以下输入的 SHA-256（不存在也要记录 `MISSING`，不得使用 Git）：当前 `.specify/memory/constitution.md`、本轮解析得到的活动 constitution template 内容及所有可定位的 core/override/preset/extension 模板贡献文件、`.specify/task-management.json`，以及当前功能目录中已存在的 `spec.md`、`plan.md`、`tasks.md` 和 checklists。记录 hook ID、绝对路径/逻辑模板 ID与摘要。
- 检查项目根目录是否存在 `.specify/extensions.yml`。
- 如果存在，读取它并查找 `hooks.before_constitution` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并正常继续。
- 过滤掉显式设置 `enabled: false` 的钩子。没有 `enabled` 字段的钩子默认视为启用。
- 对每个剩余钩子，**不要**尝试解释或求值钩子的 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或其值为 null/空，则视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，并将条件求值留给 HookExecutor 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容：
  - **可选钩子**（`optional: true`）：

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **强制钩子**（`optional: false`）：

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```

    输出上述块后，**必须**实际调用钩子并等待其完成，再继续执行大纲。调用方式与当前
    agent/session 中自行运行该命令的方式相同；实际调用形式可能不同于上面显示的字面
    `{command}` id，例如 skills 模式 agent 使用 `/skill:speckit-...` 或
    `$speckit-...`。只输出块并不等于运行钩子。
    - 钩子完成后重新计算同一集合（包括新出现或消失的文件）的 SHA-256。constitution 或任一模板输入变化时，丢弃已加载的草稿和解析结果，从 post-hook 当前状态重新解析模板、读取宪章并重跑步骤 1–5；同一 hook 重验后再次改变输入时阻断并报告不稳定 hook。
    - `spec.md`、`plan.md`、`tasks.md` 或 checklist 变化时，其既有批准和依赖宪章的证据立即失效；报告 hook、变化路径和前后摘要后停止，返回拥有该产物的阶段重新审阅，不得继续写宪章或沿用旧批准。
- 上述逐 hook 的 SHA-256、批准/上下文失效、重新解析和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；`optional` 只决定是否自动执行。可选钩子一旦被执行，必须等待完成并应用完全相同的前后哈希比较。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，静默跳过。

## 大纲

更新 `.specify/memory/constitution.md` 中的项目宪章。活动宪章脚手架在命令运行时通过
Spec Kit preset/template 解析栈从 `constitution-template` 解析得到。

在此 Codex Skill 中，`{SCRIPT}` 保留上游“按运行环境选择模板解析器”的占位符语义：

- Bash：`scripts/bash/resolve-template.sh constitution-template --json`
- PowerShell：`scripts/powershell/resolve-template.ps1 constitution-template -Json`
- Python：`scripts/python/resolve_template.py constitution-template --json`

这些上游路径相对于 `.specify/`。当前中文离线资产提供 Python 实现，因此 Codex 应从仓库
根目录运行 `python3 .specify/scripts/python/resolve_template.py constitution-template --json`。

遵循以下执行流程：

1. 从仓库根目录运行 `{SCRIPT}`，并把 `TEMPLATE_CONTENT` 解析为活动模板。
   - 共享解析器先应用项目 override、组合 preset 层和 extension 层，最后才回退到 core
     template；继续之前解析**必须**成功。
   - 如果解析失败，停止并报告解析错误；不得只使用其中一个贡献模板层继续。
   - 如果 `.specify/memory/constitution.md` 存在，将其作为当前项目特定值和修订内容的来源。
     在应用新解析的脚手架时，保留仍然适用的信息。
   - 如果该文件不存在，使用解析后的模板作为初始文档。
   - 不得回写任何有版本控制的模板层。
   - 识别所有形如 `[ALL_CAPS_IDENTIFIER]` 的占位符 token。
   - **重要**：用户要求的原则数量可能少于或多于模板使用的数量。如果指定了数量，必须
     尊重该数量并遵循通用模板，相应更新文档。

2. 收集或推导占位符值：
   - 如果用户输入（对话）提供了值，使用该值。
   - 否则从现有仓库上下文推断，例如 README、文档或嵌入其中的旧宪章版本。
   - 对治理日期：`RATIFICATION_DATE` 是最初通过日期；如果未知，询问用户或标记 TODO。
     如果发生修改，`LAST_AMENDED_DATE` 是今天；否则保留原值。
   - `CONSTITUTION_VERSION` 必须按照语义化版本规则递增：
     - MAJOR：向后不兼容的治理/原则删除或重新定义。
     - MINOR：新增原则/章节，或实质扩展指导内容。
     - PATCH：澄清、措辞修改、拼写修复或无语义变化的细化。
   - 如果升级类型有歧义，在最终确定前提出理由。

3. 以解析后的模板为必需结构，起草更新后的宪章内容：
   - 用具体文本替换每个占位符；不得留下方括号 token，除非项目明确选择暂不定义某个
     模板槽位，并且必须明确说明保留理由。
   - 保留标题层级。注释被替换后可以移除，除非它仍能提供澄清性指导。
   - 确保每个 Principle 章节包含：简洁的名称行；说明不可妥协规则的段落或项目列表；
     以及在理由不显而易见时给出的明确理由。
   - 对已有代码的项目，宪章必须包含不可妥协的“存量兼容与回归安全”原则：同类/同模块/同项目证据优先，直接复用 > 兼容扩展 > 共享提炼 > `NM-###` 获批新增；新需求不得破坏 `PB-###`，Bug 修复必须先复现、最小修复并通过相邻与完整回归。模板、override 或 hook 不得移除此原则。
   - 确保 Governance 章节列出修订程序、版本策略和合规审查预期。

4. 生成 Sync Impact Report，并在更新后把它作为 HTML 注释前置到宪章文件顶部：
   - 版本变化：old → new。
   - 修改过的原则列表；如有重命名，写为 old title → new title。
   - 新增章节。
   - 移除章节。
   - 如果有意延后任何占位符，列出后续 TODO。

5. 最终输出前进行验证：
   - 没有未解释的方括号 token。
   - 版本行与报告一致。
   - 日期使用 ISO 格式 `YYYY-MM-DD`。
   - 原则具有声明性、可测试，并且没有含糊语言；在适当位置把“should”替换为
     MUST/SHOULD 及其理由。

6. 将完成的宪章写回 `.specify/memory/constitution.md`，覆盖原文件。比较进入本阶段时与写回后的 constitution SHA-256；只要内容变化，任何现存 `spec.md`、`plan.md`、`tasks.md` 和 checklist 的旧批准都立即失效，必须在最终摘要中逐项列出并返回相应阶段按新宪章重验，不得继续沿用。

7. 先准备暂定摘要，但不得在完成“执行后检查”、post-hook 重验和安全原则复核前把它作为最终结果输出。最终摘要包括：
   - 新版本和升级理由。
   - 需要人工跟进的任何 TODO 占位符或延后事项。
   - 非本地模式且用户明确要求版本控制操作时，可建议提交信息，例如
     `docs: amend constitution to vX.Y.Z (principle additions + governance update)`；本地模式不得建议或执行 Git 操作。
   - 针对任何延后的非治理意图加入 `Next Actions` 章节。

格式与风格要求：

- 严格使用模板中的 Markdown 标题，不得提升或降低标题层级。
- 为可读性换行较长的理由行，最好短于 100 个字符；不要为了硬性满足长度而生硬换行。
- 章节之间只保留一个空行。
- 避免行尾空白。

如果用户只提供部分更新，例如只修订一项原则，仍须执行验证和版本判定步骤。

如果缺少关键信息，例如确实不知道最初通过日期，插入
`TODO(<FIELD_NAME>): explanation`，并在 Sync Impact Report 的延后事项中列出。

只写入 `.specify/memory/constitution.md`；不得创建或修改模板源文件。

## 执行后检查

**检查扩展钩子（宪章更新之后）**：

- 在实际执行每个 after hook 前，对最终候选 `.specify/memory/constitution.md`、本轮活动 constitution template 内容及所有可定位的模板贡献文件、`.specify/task-management.json`，以及当前功能目录中已存在的 `spec.md`、`plan.md`、`tasks.md` 和 checklists 分别计算 SHA-256；不存在时记录 `MISSING`，并记录 hook ID。此时的完成摘要只能是暂定报告。
检查项目根目录是否存在 `.specify/extensions.yml`。

- 如果存在，读取它并查找 `hooks.after_constitution` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并正常继续。
- 过滤掉显式设置 `enabled: false` 的钩子。没有 `enabled` 字段的钩子默认视为启用。
- 对每个剩余钩子，**不要**尝试解释或求值钩子的 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或其值为 null/空，则视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，并将条件求值留给 HookExecutor 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容：
  - **可选钩子**（`optional: true`）：

    ```text
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **强制钩子**（`optional: false`）：

    ```text
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```

    输出上述块后，**必须**实际调用钩子并等待其完成，再继续。调用方式与当前
    agent/session 中自行运行该命令的方式相同；实际调用形式可能不同于上面显示的字面
    `{command}` id，例如 skills 模式 agent 使用 `/skill:speckit-...` 或
    `$speckit-...`。只输出块并不等于运行钩子。
    - 钩子完成后重新计算同一集合（包括新出现或消失的文件）的 SHA-256。任何变化都会使暂定完成报告失效，不能报告宪章已完成。
    - constitution 或模板输入变化时，从 post-hook 当前状态重新解析模板、重新读取完整宪章并重跑步骤 1–5；该 post-hook 精确版本不得冒充此前获批版本，必须展示当前内容和 SHA-256、说明旧批准已失效，并请求用户明确批准后停止。
    - `spec.md`、`plan.md`、`tasks.md` 或 checklist 变化时，其旧批准立即失效；报告变化并停止，返回对应阶段重验。
    - 同一 hook 在重验后再次改变跟踪输入时阻断并报告不稳定 hook，不得循环或放行。
- 上述逐 hook 的 SHA-256、批准/报告失效、完整重验和不稳定 hook 规则适用于每个**实际执行**的可选或强制钩子；可选钩子一旦被执行，必须等待完成并按同一规则比较前后摘要。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，静默跳过。

完成所有 after hook（或确认没有可执行 hook）后，仍必须重新读取磁盘上的完整 `.specify/memory/constitution.md`，重新解析当前活动模板，并逐项验证不可妥协的“存量兼容与回归安全”语义仍然存在且没有被模板、override、extension 或 hook 弱化：同类/同模块/同项目证据优先；复用顺序为直接复用 > 兼容扩展 > 共享提炼 > 经批准的 `NM-###` 新增；新需求必须保护全部 `PB-###`；Bug 修复必须先复现、采用最小修复并通过相邻与完整回归；任何模板或 hook 均不得移除这些规则。任一语义缺失、降级为建议、出现绕过条款或无法核实时，按 CRITICAL 治理冲突阻断，不得发布完成报告或继续下游阶段。

只有最终宪章、模板输入与相关产物的 SHA-256 等于最后一次验证所用版本，且上述安全原则全部通过，才可发布最终摘要；摘要必须列出最终宪章 SHA-256、活动模板摘要、hook 稳定性状态，以及因本轮宪章变化而失效、需要重新批准的下游产物。
