---
name: speckit-taskstoissues
description: 根据已获用户批准的 tasks.md，把任务安全、去重地同步为 GitLab 或 GitHub Issues；用于显式选择外部 Issue 管理并校验精确目标项目。
---

# 将任务同步为 GitLab 或 GitHub Issues

## 所需工具

- GitLab provider：依赖官方 `glab` CLI 的 `auth status`、`issue list` 和 `issue create`。缺少命令或精确 host 的认证时必须停止；不得回退为在命令行参数中传递 token 的临时 `curl`。
- GitHub provider：依赖 GitHub MCP server 的 `list_issues` 和 `issue_write`。缺少任一能力时必须停止。
- 任何 provider 都不得用未经授权的凭据或其他写入路径替代。

## 用户输入

```text
$ARGUMENTS
```

如果用户输入非空，必须在继续之前加以考虑。

## 执行前检查

### 本地后端禁止外部同步（最高优先级）

读取 `.specify/task-management.json`。如果 `backend` 为 `local` 或 `vcs` 为 `none`，立即停止：不得执行 `git`、`glab`、GitHub MCP 或任何 before/after hook，也不得创建外部 Issue。提示用户如需同步必须先明确切换后端并批准精确目标。

### 任务批准与目标关卡（阻塞）

- 先确认用户已经看到当前 `tasks.md`，并在该文件最后一次实质修改后明确回复“批准任务”或等价表达；否则展示路径并询问，然后**停止**。
- 读取 `.specify/task-management.json`，并结合用户本次输入确定 provider：
  - `local`：报告“当前使用本地 tasks.md 管理，无需创建 Issue”并停止，保持外部系统不变。
  - `gitlab`：必须取得精确项目 URL 或 `group/project` 和 host。
  - `github`：仅在用户明确要求保留上游 GitHub Issue 流程时使用。
- 展示 provider、精确项目、待创建/跳过数量和标题预览。只有用户已明确授权向这个精确目标写入，才能继续；任务批准本身不自动授权任意外部仓库。
- 如果 `remote.origin.url` 存在且属于同一 provider，目标必须匹配 remote；若 remote 不存在，可使用用户明确给出的目标；若不匹配，停止并要求用户纠正或明确指定正确目标。
- 不得输出、记录或把 GitLab/GitHub token 放进 argv、`tasks.md`、Issue 正文或日志。

**检查任务转 Issue 前的扩展钩子**：

- 检查项目根目录中是否存在 `.specify/extensions.yml`。
- 如果存在，读取该文件并查找 `hooks.before_taskstoissues` 下的条目。
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

    等待钩子命令完成，然后再继续执行“大纲”。
    ```

    输出上述区块后，必须实际调用钩子并等待其完成，然后才能继续。采用当前 agent/session 中自己运行该命令时所用的方式；实际调用形式可能不同于上面显示的规范 `{command}` ID，例如 Codex skills 模式使用 `$speckit-*`。仅输出区块并不等于运行钩子。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。

## 大纲

1. 从仓库根目录运行：

   ```bash
   python3 .specify/scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
   ```

   解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS` 列表。所有路径必须为绝对路径。对于参数中类似 `I'm Groot` 的单引号，使用转义语法，例如 `'I'\''m Groot'`；也可以尽量改用双引号：`"I'm Groot"`。

2. **若存在**：加载 `.specify/memory/constitution.md`，获取项目原则和治理约束。

3. 从脚本结果中提取 `tasks.md` 路径，解析所有 `T` 加三位数字的任务 ID、标题、描述、阶段、依赖和 `[P]`/`[US#]` 标记。ID 必须唯一；发现重复或格式错误时停止。

4. 运行以下命令获取 Git remote（允许不存在）：

   ```bash
   git config --get remote.origin.url
   ```

   规范化 SSH/HTTPS remote 与用户目标进行 host、namespace、project 比较；忽略末尾 `.git`，但不得忽略 namespace。

5. **GitLab provider 预检与去重**：

   - 使用 `glab auth status --hostname <host>` 验证认证，不读取或打印凭据。
   - 使用分页命令读取 open 和 closed Issues：

     ```bash
     glab issue list --repo <exact-project> --all --per-page 100 --page <N> --output json
     ```

   - 从第 1 页开始；当前页少于 100 条时停止。所有待处理 ID 已匹配时也立即停止，不扫描无关的完整历史。
   - 对每个标题使用 `\bT\d{3}\b` 匹配；word boundaries 防止把 `ST001` 或 `T0010` 当作 `T001`。
   - 在任何写入前输出计划：精确 host/project、总任务数、已有数量、将创建数量以及规范标题列表。

6. **GitLab provider 创建**：只为未匹配的任务逐项执行参数数组形式的命令：

   ```bash
   glab issue create --repo <exact-project> --title "T001: <description>" --description "<可追踪正文>" --yes
   ```

   正文包含 feature 相对路径、原始任务行、用户故事/阶段和依赖；不包含凭据。每次创建后验证返回的 Issue URL 属于批准的 host/project。任一创建失败时停止后续写入，报告已创建与未创建 ID，重试时仍先去重。

7. **GitHub provider 去重与创建**（保留上游能力）：

   - 使用 GitHub MCP `list_issues`，省略 `state` 以同时返回 open/closed，`perPage: 100`，按 `endCursor` 分页；所有待处理 ID 已匹配时停止。
   - 以相同的 `\bT\d{3}\b` 标题规则去重。
   - 使用 `issue_write` 仅在精确匹配用户批准的 GitHub 仓库中创建规范标题 `T001: <description>`；跳过已有 ID。

8. **完成报告**：报告 provider、精确目标、tasks 路径、创建/跳过/失败的任务 ID 和 Issue URL。不得把“命令成功”替代为目标校验，也不得声称本地 `tasks.md` 已删除；它仍是 SDD 的审计产物。

## 执行后检查

**检查任务转 Issue 后的扩展钩子**：

- 检查项目根目录中是否存在 `.specify/extensions.yml`。
- 如果存在，读取该文件并查找 `hooks.after_taskstoissues` 下的条目。
- 如果 YAML 无法解析或无效，静默跳过钩子检查并照常继续。
- 过滤掉 `enabled` 明确为 `false` 的钩子；没有 `enabled` 字段的钩子默认视为已启用。
- 对每个剩余钩子，不要尝试解释或计算 `condition` 表达式：
  - 如果钩子没有 `condition` 字段，或该字段为 null/空值，则将其视为可执行。
  - 如果钩子定义了非空 `condition`，跳过该钩子，把条件计算留给 `HookExecutor` 实现。
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

    输出上述区块后，必须实际调用钩子并等待其完成，然后才能继续。采用当前 agent/session 中自己运行该命令时所用的方式；实际调用形式可能不同于上面显示的规范 `{command}` ID，例如 Codex skills 模式使用 `$speckit-*`。仅输出区块并不等于运行钩子。
- 如果没有注册钩子，或 `.specify/extensions.yml` 不存在，则静默跳过。
