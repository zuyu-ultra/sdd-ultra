# CLI 核心能力

本 Skill 不使用 `PATH` 上的 `specify`。所有命令通过固定运行时网关执行；完整参数以 `capability-map.json` 和同版本 `--help` 为准。

## 固定入口

```bash
python3 <skill-dir>/scripts/specify_runtime.py status
python3 <skill-dir>/scripts/specify_runtime.py ensure
python3 <skill-dir>/scripts/specify_runtime.py classify -- <args...>
python3 <skill-dir>/scripts/specify_runtime.py run --target <repo> [授权参数] -- <args...>
```

`ensure` 先验证 vendored source 与 wheelhouse 的 SHA-256，然后建立内容寻址 venv。默认只使用离线 wheel；只有当前 Python/平台无匹配 wheel 时，用户授权后才可使用 `--allow-network`。

## 顶层命令

| 命令 | 用途 | 写入与风险 |
|---|---|---|
| `specify init` | 初始化核心模板、三类脚本、workflow、integration、可选 preset/extension | 项目写入；`--force` 是覆盖风险；外部 extension 还涉及网络和代码 |
| `specify check` | 检测 integration 依赖工具 | 本地探测，可能启动外部 CLI 的版本检查 |
| `specify version` | 显示版本和系统信息 | 只读；`--features --json` 可机器读取能力 |
| `specify self check` | 查询可用的新版本 | 网络只读 |
| `specify self upgrade` | 通过 uv tool/pipx 更新安装 | 网络、破坏固定锁、全局 runtime 写入；本 Skill 默认拦截 |
| `specify event run` | 从 stdin 分派内部 extension event | 内部入口；可能触发 agent/extension 行为，不直接暴露给普通用户 |

## 初始化语义

核心 scaffold 随 `specify-cli` 包分发，所以仅安装核心与 built-in integration 时可离线运行。

```bash
# 当前目录，Codex skills 模式，Python helper scripts
... run --target <repo> --allow-project-write -- \
  init --here --integration codex \
  --integration-options="--skills" --script py --ignore-agent-tools
```

关键选项：

- `project_name` 或 `--here`/`.` 选择目标。
- `--script sh|ps|py` 选择 Bash、PowerShell 或 Python helper；官方三套各 6 个。
- `--integration <id>` 与 `--integration-options="..."` 选择 agent 格式。
- `--preset <id>` 可在初始化时加入 preset。
- `--extension <id|path|https-url>` 可重复；URL 在非交互模式还需 `--trust-extension-urls`，但这只表示用户信任，不是安全审计。
- `--force` 不是 Git 参数。它让 `specify init --here` 在非空目录跳过交互确认，并把同名初始化文件交给 merge/overwrite 路径。非空不等于冲突：先检查计划写入的目标路径和内容；本地模式只能用目录清单与哈希，禁止检查 Git 状态。
- `--offline`、`--github-token`、`--skip-tls` 已是兼容性 no-op/deprecated，不应作为安全控制。
- `SPECIFY_INIT_DIR` 是官方 monorepo/外部调用可用的初始化根；显式 `--target` 仍由 Skill 网关确定 cwd。

官方初始化不会把 Git 作为核心必需品。`--ignore-agent-tools` 只跳过 agent 工具探测，不削减安装资产。

## 本地任务模式：零 Git 命令

当 `.specify/task-management.json` 为 `{"backend":"local","vcs":"none"}` 时：

- 不启动 `git`，不检查 `.git`，不读取 remote，不创建或切换分支，不运行 status/diff/log。
- 不调用 `speckit.git.*` Skill 或 extension hook；即使钩子标为强制也按本地安全策略跳过并报告。
- 不执行 GitLab/GitHub Issue 同步，也不为了版本控制单独创建或修改 `.gitignore`。
- 用 `.specify/feature.json` 定位活动 feature，用绝对路径、目录清单、文件内容、SHA-256 和 manifest 检查初始化与实现结果。

官方 `init` 的核心路径未调用 Git；`--force` 只控制非空目录确认与文件合并。Skill 不得因为目录非空就笼统声称“必须覆盖”：先列出实际冲突，只有存在不同内容的同名目标且用户明确批准时才使用破坏性覆盖授权。

## 中文叠加层

`scripts/install_project.py` 是 Codex skills 模式的中文核心叠加层，不替代官方初始化。它安全安装完整中文 10 阶段、5 个模板、Python helper 与 locale/upstream 元数据。

```bash
python3 <skill-dir>/scripts/install_project.py --target <repo>
python3 <skill-dir>/scripts/install_project.py --target <repo> --check
```

- 普通安装不覆盖冲突的托管文件，返回 `attention_required`。
- `--force` 可刷新托管资产，但不会覆盖用户已自定义的 constitution。
- `--check` 对 missing、modified、unsafe path、错误 metadata 或尚未本地化的占位 constitution 返回非零。
- 其他 integration 保留官方原生注册格式；控制面仍用中文工作，但不要把 Codex 的 `.agents/skills` 叠加层写进别的 agent 目录。

## 完成检查

初始化或升级后至少核对：

```bash
... run --target <repo> -- integration status --json
python3 <skill-dir>/scripts/install_project.py --target <repo> --check
```

本地模式到此结束，以退出码、JSON 状态、manifest hash 和磁盘文件为准。只有非本地模式且用户当前请求明确需要版本控制信息时，才可另外检查 Git 状态；不用英文提示词判断成功。
