# Extension、Hook 与 Event

Extension 为核心 SDD 增加命令、模板、脚本、配置和 before/after hooks。固定快照内置 4 个生产 extension：

| ID | 能力 |
|---|---|
| `agent-context` | 从 plan 更新 agent 上下文文件，支持 Bash/PowerShell/Python |
| `assess` | intake → research → shape → define → decide 评估流程 |
| `bug` | assess → test → fix 的 agentic bugfix 流程 |
| `git` | 初始化、feature branch、remote、validate、commit 及三类脚本 |

`selftest` 与 `template` 是上游测试/创作材料，不列为 production bundled catalog 项。

## 生命周期

```bash
specify extension search [query] [--verified]
specify extension info <id>
specify extension add <id> [--priority N]
specify extension add <path> --dev
specify extension add <id> --from <https-url>
specify extension list [--available|--all]
specify extension set-priority <id> <N>
specify extension disable|enable <id>
specify extension update [id]
specify extension remove <id> [--keep-config]
```

较小 priority 具有更高命令/模板解析优先级。安装会把命令注册到当前 default integration；切换 integration 后由 `integration use/switch` 重建注册。

`disable` 使 extension 不再加载且命令不可用；`remove` 删除安装内容，默认备份配置。更新和移除前检查本地改动、config 和 hook 影响。

## 配置层

```text
extension.yml defaults
-> .specify/extensions/<id>/<id>-config.yml
-> .specify/extensions/<id>/<id>-config.local.yml
-> SPECKIT_<EXT>_* environment variables
```

后者覆盖前者。项目 config 可提交，`.local.yml` 应保持本地且被 gitignore。

## Hook

项目注册表在 `.specify/extensions.yml`。事件一般是 `before_<core-command>` 或 `after_<core-command>`。每项可含 `extension`、`command`、`enabled`、`optional`、`priority`、`prompt`、`description`、`condition`。

- `optional: false` 的 command template 会输出 `EXECUTE_COMMAND:`，必须按阶段 Skill 的 hook 协议处理。
- `optional: true` 先向用户展示 prompt，可跳过。
- 当前 core command templates 直接按 YAML 顺序展示 hooks，不按 priority 排序；`HookExecutor` API 才会正规化并按较小 priority 排前。
- 当前 command templates 遇到非空 `condition` 会跳过；不要声称它已在模板阶段求值。
- `settings.auto_execute_hooks` 当前是保留字段，不是执行开关。

Hook 命令与 extension 脚本都是外部行为。先检查 manifest、命令正文、script、网络和外部写入，再决定是否执行。

## Event

`specify event run` 是 extension event 分派的内部入口。它从 stdin 接收有大小上限的 JSON payload，并可能调用 agent CLI；不应把未经验证的任意输入直接透传。普通用户工作流优先使用已注册的 core/extension command，而不是手工调用内部 event。

## Catalog

```bash
specify extension catalog list
specify extension catalog add <https-url> --name <name> [--priority N]
specify extension catalog remove <name>
```

解析顺序：`SPECKIT_CATALOG_URL` → 项目 `.specify/extension-catalogs.yml` → 用户配置 → official/community。Catalog 的 `install_allowed` 只是安装政策，不等于内容经过安全审核。

## 创作与发布

完整 schema、hooks、resources、constraints、configuration 和发布流程见：

- `vendor/spec-kit/extensions/EXTENSION-DEVELOPMENT-GUIDE.md`
- `vendor/spec-kit/extensions/EXTENSION-API-REFERENCE.md`
- `vendor/spec-kit/extensions/EXTENSION-PUBLISHING-GUIDE.md`
- `vendor/spec-kit/extensions/template/`

创作时至少测试 manifest validation、所有命令注册格式、三平台脚本、config merge、hook before/after、disable/enable、update/remove 和恶意 archive/path。
