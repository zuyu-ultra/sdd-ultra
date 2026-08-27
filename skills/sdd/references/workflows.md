# Workflow、Step 与 Overlay

Workflow engine 可串联命令、agent prompt、shell、初始化、人工 gate、条件、循环与并行分支，并持久化运行状态以恢复。

## 生命周期

```bash
specify workflow search [query]
specify workflow info <id>
specify workflow add <id|path|url>
specify workflow list
specify workflow resolve <id>
specify workflow run <id|local.yml> [inputs...]
specify workflow status [run-id]
specify workflow resume <run-id>
specify workflow disable|enable <id>
specify workflow update [id]
specify workflow remove <id>
```

大多数命令要求已初始化项目。`workflow run <local.yml>` 可在项目外运行，但会在当前目录创建 `.specify/workflows/runs/<run_id>/`。

固定快照的官方基础流程是 `specify → review-spec → plan → review-plan → tasks → implement`。本 Skill 的中文受管 workflow 在其上增加必选任务后端输入、`review-tasks` 人工关卡，以及仅在 `gitlab` 后端被选择时执行的 GitLab Issue 同步：`specify → review-spec → plan → review-plan → tasks → review-tasks → GitLab sync? → implement`。它仍不等于包含 clarify/checklist/analyze/converge 的增强质量周期。

三个 review gate 都必须针对刚生成的当前产物等待用户选择，不能用 workflow 启动时的笼统授权预先通过。`specify` 步骤先判定需求规模：`XS`/`S` 进入精简模式，只产出一份含内联任务与回归的变更说明，`plan`/`tasks` 步骤应报告并停止等待用户选择升档或直接实现；`M`/`L` 走完整流程。`specify` 与 `plan` 步骤在写入产物前分别执行需求共创与技术方案共创：需求关键维度不明确、或存在多条代价不同的技术路径时，先逐个展示带推荐项的选项表并取得用户决定，把结论以 `DD-###` 落盘 `discovery.md`；`review-spec` 同时审阅 `spec.md` 与这些决策。`task_backend` 必须由用户选择 `local` 或 `gitlab`；不得从 remote 推断。GitLab 分支必须同时提供精确 `gitlab_project`，并且只在 `review-tasks=approve` 后进入外部写入步骤。

## 11 种 Step

```text
command, prompt, shell, init, gate,
if, switch, while, do-while, fan-out, fan-in
```

- `command` 调用已注册 Spec Kit command。
- `prompt` 启动 agent 并取得文本结果。
- `shell` 把字符串交给系统 shell 并捕获输出。
- `init` 执行初始化类动作。
- `gate` 暂停等待 accept/reject/revise 等人工裁决。
- `if`、`switch`、`while`、`do-while` 控制分支/循环。
- `fan-out` 展开并行项，`fan-in` 汇合结果。

Custom step 通过：

```bash
specify workflow step search|info|list ...
specify workflow step add <id|path|url>
specify workflow step remove <id>
specify workflow step catalog list|add|remove ...
```

它可带 Python/外部实现，安装与执行都属于代码执行风险。

## 运行状态与恢复

每次运行保存在 `.specify/workflows/runs/<run_id>/`，包含 workflow 快照、inputs、step 状态/输出、gate state 与日志。`resume` 从持久化断点继续，执行前必须重新确认剩余 step 的风险；不能因为前一次批准过就默认批准新的外部状态。

## Overlay

Overlay 位于 `.specify/workflows/overlays/<workflow-id>/<overlay-id>.yml`，对 base step list 执行 add/replace/remove 等编辑。

```bash
specify workflow overlay add <file> [--priority N]
specify workflow overlay list <workflow-id>
specify workflow overlay set-priority <workflow-id> <overlay-id> <N>
specify workflow overlay disable|enable <workflow-id> <overlay-id>
specify workflow overlay remove <workflow-id> <overlay-id>
specify workflow resolve <workflow-id>
```

优先级是 lower-wins，但应用顺序为较大数字先、较小数字后，因此小数字能最终覆盖冲突；同 priority 按 ID 字母序应用，后者赢冲突。Overlay 不能引用另一个 overlay 新增的 step；目标 step 不存在会在 resolve 时失败。

安装/更新 workflow 会保留项目 overlay，因为它们不在 installed workflow 目录内。执行前始终 `resolve`，查看最终 layer stack、step 来源和完整命令。

## 必须明确的安全边界

- `shell` 使用当前用户权限运行，没有 capability sandbox；`requires` 只是前置兼容声明，不限制权限。
- `{{ expression }}` 是纯字符串替换，不进行 shell quoting/escaping。
- agent 的 `prompt` 输出、前置 step stdout、用户 input、文件或网页内容都视为不可信；不要把它们插入 `shell.run`。
- 输入能进入 shell 时必须在源头用 enum/allowlist 限制；引号只改善正确性，不是安全边界。
- 执行前展示最终 resolved `shell.run`、agent binary/args、环境变量、外部写入、timeout 和所有 hooks，并取得 `--allow-code-execution`。

## Catalog 与创作

Workflow/step 都有 official、project、user、community catalog 层；只有 HTTPS 或 loopback 开发 URL。Community 内容未经过官方安全审计。

创作参考 `vendor/spec-kit/workflows/ARCHITECTURE.md`、`PUBLISHING.md` 与 `docs/reference/workflows.md`。至少测试 schema、表达式、每种 step、gate/revise、resume、loop 上限、fan-out failure、overlay 冲突、shell injection、timeout 和中断恢复。
