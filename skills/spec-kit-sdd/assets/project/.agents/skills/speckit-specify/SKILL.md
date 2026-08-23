---
name: speckit-specify
description: 根据自然语言功能描述创建或更新中文版功能规格；为已有项目识别 PB-### 受保护行为、变化边界与缺陷复现，生成 spec.md、需求质量检查表并完成批准关卡。
---

## 用户输入

```text
$ARGUMENTS
```

如果用户输入非空，**必须**在继续之前考虑它。

## 执行前检查

### 本地零 Git 命令策略（最高优先级）

读取 `.specify/task-management.json`。如果已选择 `local` 或 `vcs` 为 `none`，本阶段不得执行 `git`、检查 `.git`、读取 remote/branch/status/diff/log，且 before/after hooks 中所有 `speckit.git.*` 或会启动 `git` 的钩子一律跳过；此规则覆盖钩子的强制标志。

### 任务管理后端选择（阻塞关卡）

- 在写入任何功能文件前，检查用户是否已为本轮 feature 明确选择 `local` 或 `gitlab`。
- 如果没有明确选择，询问：“本功能的任务使用本地 `tasks.md` 管理，还是同步到 GitLab Issues 管理？”然后**停止并等待用户回复**；不得从 Git remote 推断。
- `local`：`tasks.md` 是任务管理入口，不创建外部 Issues；把选择写为 `{"backend":"local","vcs":"none"}`。这是严格零 Git 命令模式：不得执行 `git`、检查 `.git`、读取 remote、创建或切换分支、调用 `speckit.git.*` 钩子，或用 Git 状态定位 feature。
- `gitlab`：要求精确 GitLab 项目 URL 或 `group/project`。把不含凭据的选择写入 `.specify/task-management.json`；此时只记录目标，不创建 Issue。
- 每个新 feature 都要向用户复述选择。用户可变更后端，但切换到 GitLab 仍需在 `tasks.md` 获批后单独授权外部写入。

### Hook 产物完整性协议（所有实际执行的 before/after hook 强制）

- 在**每一个** hook 执行前单独建立快照，不得让多个 hook 共用一组快照。快照至少包含 `.specify/feature.json`、`.specify/task-management.json`，以及当前 feature 可解析时的 `spec.md`、`checklists/requirements.md`、`plan.md`、`research.md`、`data-model.md`、`quickstart.md`、`contracts/` 全部普通文件和 `tasks.md`。逐个普通文件记录绝对解析路径与 SHA-256；目录同时记录相对路径，不存在的预期文件记录为 `MISSING`。不得用 mtime、大小或 Git 状态代替。
- Hook 完成后重新解析 feature 路径并重新计算同一集合；新增、删除、重命名、解析目标变化或 SHA-256 变化都算实质变化。可选 hook 仅展示时无需快照，但用户随后实际执行时必须在执行当下使用本协议。
- 每个 hook 后无论摘要是否变化，都重新读取存在的规格、检查表和下游产物，完整重跑 `PB-###` 唯一性与覆盖、变化/不变边界、旧调用方/公共契约、Bug 复现与相邻场景，以及 requirements checklist；若已有 plan/tasks，还要重验复用决策、`NM-###`、调用方、变更前基线和回归矩阵。缺失、冲突或不可验证立即阻断，不能进入大纲或完成报告。
- Hook 不得删除或弱化 `## 存量行为与兼容性`，也不得以 replace override、preset、extension 或自定义模板移除红线内容；活动模板缺少该章节时，本阶段必须主动补齐，而不是照缺失模板输出。
- Hook 造成 `spec.md` 或其验证证据发生实质变化时，已有规格批准及所有下游批准立即失效。报告变化文件和前后 SHA-256，并在继续规划前要求用户重新批准当前规格。

**检查扩展钩子（规格编写之前）**：

- 检查项目根目录是否存在 `.specify/extensions.yml`。
- 如果存在，读取它并查找 `hooks.before_specify` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并正常继续。
- 过滤掉显式设置 `enabled: false` 的钩子。没有 `enabled` 字段的钩子默认视为启用。
- 如果任务后端是 `local`，再过滤所有 extension 为 `git`、命令 ID 以 `speckit.git.` 开头或实际执行会启动 `git` 的钩子。即使这类钩子标为强制也不得执行；报告“已按本地零 Git 策略跳过”，然后继续纯文件流程。
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
    `$speckit-...`。只输出块并不等于运行钩子。执行前后必须完成“Hook 产物完整性协议”；
    若 hook 改变已有规格或验证证据，在重验和重新批准完成前停止，不得继续大纲。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，静默跳过。

## 大纲

用户在触发消息中输入于 `$speckit-specify` 之后的文本**就是**功能描述。即使下方按字面
出现 `{ARGS}`，也应假定对话中始终可以取得该描述。除非用户提交了空命令，否则不要要求
用户重复描述。

根据该功能描述执行以下工作：

1. 为功能**生成简洁短名称**（2–4 个词）：
   - 分析功能描述并提取最有意义的关键词。
   - 创建能概括功能实质的 2–4 词短名称。
   - 尽可能使用 action-noun 格式，例如 `add-user-auth`、`fix-payment-bug`。
   - 保留技术术语和缩写，例如 OAuth2、API、JWT。
   - 名称保持简洁，但应具有足够描述性，使人一眼理解功能。
   - 示例：
     - “我想添加用户身份验证” → `user-auth`
     - “为 API 实现 OAuth2 集成” → `oauth2-api-integration`
     - “创建分析仪表板” → `analytics-dashboard`
     - “修复支付处理超时缺陷” → `fix-payment-timeout`

2. **创建分支**（仅非本地模式可选，通过钩子完成）：

   本地模式必须完全跳过本步骤。如果上述执行前检查中的非 Git 本地策略之外的
   `before_specify` 钩子成功运行，它可能创建或切换 git 分支，并
   输出包含 `BRANCH_NAME` 和 `FEATURE_NUM` 的 JSON。记录这些值供参考，但分支名称
   **不决定**规格目录名称。

   如果用户显式提供了 `GIT_BRANCH_NAME`，将其原样传给钩子，使分支脚本使用该精确值
   作为分支名，绕过所有前缀/后缀生成。

3. **创建规格功能目录**：

   除非用户显式提供 `SPECIFY_FEATURE_DIRECTORY`，规格默认位于 `specs/` 目录下。

   **`SPECIFY_FEATURE_DIRECTORY` 解析顺序**：

   1. 如果用户显式提供了 `SPECIFY_FEATURE_DIRECTORY`，例如通过环境变量、参数或配置，
      原样使用。
   2. 否则在 `specs/` 下自动生成：
      - 检查 `.specify/init-options.json` 中的 `feature_numbering`（首选）或
        `branch_numbering`（已弃用，仅用于迁移；将在未来版本删除）。
      - 如果值为 `"timestamp"`：前缀使用当前时间戳 `YYYYMMDD-HHMMSS`。
      - 如果值为 `"sequential"` 或不存在：扫描 `specs/` 中的现有目录，前缀使用下一个
        可用的三位数 `NNN`。
      - 构造目录名 `<prefix>-<short-name>`，例如 `003-user-auth` 或
        `20260319-143022-user-auth`。
      - 将 `SPECIFY_FEATURE_DIRECTORY` 设为 `specs/<directory-name>`。
      - 如果使用了 `branch_numbering` 且没有 `feature_numbering`，输出一行警告：
        `⚠️ branch_numbering in init-options.json is deprecated. Rename to feature_numbering.`

   **创建目录和规格文件**：

   - 运行 `mkdir -p SPECIFY_FEATURE_DIRECTORY`。
   - 通过 Spec Kit preset/template 解析栈解析活动 `spec-template`，等同于
     `specify preset resolve spec-template`。
   - 将解析后的 `spec-template` 文件复制到 `SPECIFY_FEATURE_DIRECTORY/spec.md` 作为起点。
   - 将 `SPEC_FILE` 设置为 `SPECIFY_FEATURE_DIRECTORY/spec.md`。
   - 将解析后的路径持久化到 `.specify/feature.json`：

     ```json
     {
       "feature_directory": "<resolved feature dir>"
     }
     ```

     写入真实解析目录路径，例如 `specs/003-user-auth`，不得写入字面字符串
     `SPECIFY_FEATURE_DIRECTORY`。这样，下游 Skill（`$speckit-plan`、
     `$speckit-tasks` 等）无需依赖 git 分支命名约定即可定位功能目录。

   **重要**：

   - 每次调用 `$speckit-specify` 必须只创建一个功能。
   - 规格目录名与 git 分支名相互独立；它们可以相同，但这是用户的选择。
   - 规格目录和文件始终由本 Skill 创建，绝不由钩子创建。

4. 加载已解析的活动 `spec-template` 文件，了解必需章节。

5. **如果存在**，加载 `/memory/constitution.md` 中的项目原则和治理约束。

5a. **建立存量行为基线（已有项目或 Bug 修复强制）**：
   - 读取与需求最接近的现有用户流程、公共接口文档和测试；先看目标类/组件，再看同模块和同项目的相似行为。
   - 这里只提取调用方可观察的行为，不把 method/class 等实现细节写入规格。
   - 为每项不得改变的行为分配稳定 `PB-###`，覆盖正常路径、异常路径、边界条件、公共契约和数据兼容性。
   - 对 Bug 修复记录最小复现条件、当前错误、期望结果以及相邻不应改变的场景。
   - 把未被用户明确要求改变的现有行为视为受保护契约；无法确定高影响行为时使用澄清问题，不能自行假定可以破坏。

6. 遵循以下执行流程：
   1. 从参数解析用户描述。
      如果为空：ERROR `No feature description provided`。
   2. 从描述中提取关键概念。
      识别：actors、actions、data、constraints。
   3. 对不清晰之处：
      - 根据上下文和行业标准作出有依据的推断。
      - 仅在以下条件成立时使用 `[NEEDS CLARIFICATION: specific question]` 标记：
        - 该选择显著影响功能范围或用户体验。
        - 存在多个合理解释，且影响不同。
        - 不存在合理默认值。
      - **限制：总共最多 3 个 `[NEEDS CLARIFICATION]` 标记。**
      - 按影响排序澄清：scope > security/privacy > user experience > technical details。
   4. 填写 User Scenarios & Testing 章节。
      如果没有清晰用户流程：ERROR `Cannot determine user scenarios`。
   5. 生成功能需求。
      每项需求都必须可测试。对未指定细节使用合理默认值，并记录在 Assumptions 章节。
   6. 定义成功标准。
      创建可度量且技术无关的结果；同时包含定量指标（时间、性能、容量）和定性指标
      （用户满意度、任务完成情况）；每项标准无需实现细节即可验证。
   7. 如果涉及数据，识别关键实体。
   8. 返回 SUCCESS，表示规格已可进入规划。

7. 使用模板结构将规格写入 `SPEC_FILE`。以功能描述（参数）推导的具体细节替换占位符，
   同时保留章节顺序和标题。

8. **规格质量验证**：写入初始规格后，按质量标准进行验证：

   a. **创建规格质量检查表**：使用以下检查表模板结构，在
      `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` 生成文件：

      ```markdown
      # 规格质量检查表：[FEATURE NAME]

      **目的**：在进入规划前验证规格的完整性与质量
      **创建日期**：[DATE]
      **功能**：[链接到 spec.md]

      ## 内容质量

      - [ ] 不包含实现细节（语言、框架、API）
      - [ ] 聚焦用户价值和业务需求
      - [ ] 面向非技术利益相关者编写
      - [ ] 所有必填章节均已完成

      ## 需求完整性

      - [ ] 不再保留 [NEEDS CLARIFICATION] 标记
      - [ ] 需求可测试且无歧义
      - [ ] 成功标准可度量
      - [ ] 成功标准与技术无关（无实现细节）
      - [ ] 所有验收场景均已定义
      - [ ] 已识别边界情况
      - [ ] 范围边界清晰
      - [ ] 已识别依赖和假设

      ## 功能就绪度

      - [ ] 所有功能需求都有清晰验收标准
      - [ ] 用户场景覆盖主要流程
      - [ ] 功能满足 Success Criteria 中定义的可度量结果
      - [ ] 规格中没有泄漏实现细节

      ## 存量兼容与回归

      - [ ] 所有受影响的既有行为均以 PB-### 记录并可验证
      - [ ] 已明确本次会改变与不会改变的边界
      - [ ] 公共契约、旧调用方和数据兼容要求已记录
      - [ ] Bug 修复已定义复现条件、期望行为及相邻不变场景

      ## 备注

      - 标记为未完成的项目必须在 `$speckit-clarify` 或 `$speckit-plan` 前更新规格
      ```

   b. **运行验证检查**：对照每个检查项审查规格：
      - 判断每项通过或失败。
      - 记录发现的具体问题，并引用相关规格章节。

   c. **处理验证结果**：

      - **如果所有项目均通过**：将检查表标记为完成，进入“强制执行后钩子”章节。

      - **如果有项目失败，但不涉及 `[NEEDS CLARIFICATION]`**：
        1. 列出失败项和具体问题。
        2. 更新规格，解决每个问题。
        3. 重新运行验证，直到全部通过，最多 3 轮。
        4. 如果 3 轮后仍有失败项，在检查表备注中记录剩余问题并警告用户。

      - **如果仍有 `[NEEDS CLARIFICATION]` 标记**：
        1. 从规格中提取全部 `[NEEDS CLARIFICATION: ...]` 标记。
        2. **限制检查**：如果标记超过 3 个，仅保留按 scope/security/UX 影响衡量最关键的
           3 个，其余使用有依据的推断。
        3. 对每项需要澄清的问题（最多 3 个），按以下格式向用户提供选项：

           ```markdown
           ## 问题 [N]：[Topic]

           **上下文**：[引用相关规格章节]

           **需要确认**：[NEEDS CLARIFICATION 标记中的具体问题]

           **建议答案**：

           | 选项 | 答案 | 影响 |
           |------|------|------|
           | A | [第一个建议答案] | [这对功能意味着什么] |
           | B | [第二个建议答案] | [这对功能意味着什么] |
           | C | [第三个建议答案] | [这对功能意味着什么] |
           | Custom | 提供自定义答案 | [说明如何提供自定义输入] |

           **你的选择**：_[等待用户回复]_
           ```

        4. **关键——表格格式**：确保 Markdown 表格格式正确：
           - 使用一致的间距，并对齐竖线。
           - 每个单元格内容两侧都有空格：使用 `| Content |`，不要使用 `|Content|`。
           - 表头分隔符至少含 3 个连字符：`|--------|`。
           - 在 Markdown 预览中测试表格能否正确渲染。
        5. 依次编号问题：Q1、Q2、Q3，总数最多 3 个。
        6. 在等待回复前一次展示所有问题。
        7. 等待用户回复所有问题的选择，例如
           `Q1: A, Q2: Custom - [details], Q3: B`。
        8. 用用户选择或提供的答案替换每个 `[NEEDS CLARIFICATION]` 标记，更新规格。
        9. 所有澄清解决后重新运行验证。

   d. **更新检查表**：每轮验证后，用当前通过/失败状态更新检查表文件。

## 强制执行后钩子

**向用户报告完成之前，必须完成本章节。**

对每个实际执行的 `after_specify` hook，在执行前先对本次 `SPEC_FILE`、
`SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md`、`.specify/feature.json`、
`.specify/task-management.json` 和存在的 plan/research/data model/contracts/quickstart/tasks
分别记录 SHA-256；执行后重新解析路径、重新计算并逐文件比较。随后无条件重新读取全部存在
的相关产物，完整重跑本阶段的存量兼容检查和整个规格质量检查表；若已有下游产物，同时重验
`NM-###`、调用方、变更前基线和回归矩阵。只有重验全部通过才能进入完成报告；变化会使此前
对该规格及下游产物的批准失效。

检查项目根目录是否存在 `.specify/extensions.yml`。

- 如果不存在，或 `hooks.after_specify` 下没有注册钩子，跳到完成报告。
- 如果存在，读取它并查找 `hooks.after_specify` 键下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并继续到完成报告。
- 过滤掉显式设置 `enabled: false` 的钩子。没有 `enabled` 字段的钩子默认视为启用。
- 对每个剩余钩子，**不要**尝试解释或求值钩子的 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或其值为 null/空，则视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，并将条件求值留给 HookExecutor 实现。
- 对每个可执行钩子，根据其 `optional` 标志输出以下内容：
  - **强制钩子**（`optional: false`）——对每个强制钩子都**必须输出
    `EXECUTE_COMMAND:`**：

    ```text
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```

    输出上述块后，**必须**实际调用钩子并等待其完成，再继续。调用方式与当前
    agent/session 中自行运行该命令的方式相同；实际调用形式可能不同于上面显示的字面
    `{command}` id，例如 skills 模式 agent 使用 `/skill:speckit-...` 或
    `$speckit-...`。只输出块并不等于运行钩子。调用前后必须完成逐 hook SHA-256 快照、
    重新读取和重验；失败时立即阻断，不得进入完成报告。
  - **可选钩子**（`optional: true`）：

    ```text
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## 完成报告

向用户报告完成情况，包括：

- `SPECIFY_FEATURE_DIRECTORY`——功能目录路径。
- `SPEC_FILE`——规格文件路径。
- 检查表结果摘要。
- 当前任务管理后端：本地 `tasks.md` 或精确 GitLab 项目。
- 明确列出规格范围、主要需求、假设、未决问题和 `spec.md` 路径。
- 对已有项目列出 `PB-###` 受保护行为、变化/不变边界；Bug 修复还要列出复现与相邻场景。
- 询问：“请审阅当前 `spec.md`。是否批准此版本进入澄清/规划阶段？请回复‘批准规格’，或指出需要修改的内容。”

输出上述确认问题后**必须停止**。不得在同一轮自动调用 `$speckit-plan`，也不得把用户最初“完成整个功能”的请求视为对尚未生成规格的预批准。批准只适用于用户看到的当前 `spec.md`；规格被实质修改后必须重新确认。

**注意**：分支创建由 `before_specify` 钩子（git extension）处理。规格目录和规格文件始终
由本 core Skill 创建。

## 快速指南

- 聚焦用户需要**什么（WHAT）**以及**为什么（WHY）**。
- 避免描述如何实现（HOW）；不得包含技术栈、API 或代码结构。
- 面向业务利益相关者而不是开发者编写。
- 不得在规格内部创建任何检查表；那将由独立命令处理。

### 章节要求

- **必填章节**：每个功能都必须完成。
- **可选章节**：仅在与该功能相关时包含。
- 如果某章节不适用，完整删除；不要保留为 `N/A`。

### AI 生成规则

根据用户 prompt 创建规格时：

1. **项目证据优先**：已有项目先使用当前代码、测试、接口文档和相邻行为填补缺口；只有项目没有证据时，才使用行业标准和常见模式。项目传统与通用最佳实践不一致时，默认保留项目传统，除非违反宪章、安全要求或用户指令。
2. **记录假设**：在 Assumptions 章节记录合理默认值。
3. **限制澄清**：最多 3 个 `[NEEDS CLARIFICATION]` 标记，仅用于以下关键决策：
   - 显著影响功能范围或用户体验。
   - 有多个合理解释且影响不同。
   - 没有任何合理默认值。
4. **确定澄清优先级**：scope > security/privacy > user experience > technical details。
5. **像测试人员一样思考**：每项含糊需求都应无法通过“可测试且无歧义”检查项。
6. **常见澄清领域**，仅在不存在合理默认值时使用：
   - 功能范围和边界，包括/排除特定用例。
   - 用户类型和权限，如果存在多个相互冲突的解释。
   - 安全/合规需求，如果具有重大法律或财务影响。

**合理默认值示例**（不要询问这些内容）：

- 数据保留：采用该领域的行业标准做法。
- 性能目标：除非另有说明，采用标准 web/mobile app 预期。
- 错误处理：使用用户友好消息和适当 fallback。
- 身份验证方式：web app 使用标准 session-based 或 OAuth2。
- 集成模式：采用适合项目的模式，例如 web service 使用 REST/GraphQL、library 使用函数
  调用、tool 使用 CLI args 等。

### 成功标准指南

成功标准必须：

1. **可度量**：包含明确指标，例如时间、百分比、数量、速率。
2. **技术无关**：不提及框架、语言、数据库或工具。
3. **面向用户**：从用户/业务角度描述结果，而非系统内部行为。
4. **可验证**：无需了解实现细节即可测试或验证。

**良好示例**：

- “用户可在 3 分钟内完成结账。”
- “系统支持 10,000 名并发用户。”
- “95% 的搜索在 1 秒内返回结果。”
- “任务完成率提高 40%。”

**不良示例**（聚焦实现）：

- “API 响应时间低于 200ms”（过于技术化；改用“用户立即看到结果”）。
- “数据库可处理 1000 TPS”（实现细节；改用面向用户的指标）。
- “React 组件高效渲染”（特定于框架）。
- “Redis cache hit rate 高于 80%”（特定于技术）。

## 完成条件

- [ ] 规格已写入 `SPEC_FILE`，并通过质量检查表验证。
- [ ] 已按照上述“强制执行后钩子”规则分派或跳过扩展钩子。
- [ ] 已向用户报告功能目录、规格文件路径和检查表结果。
