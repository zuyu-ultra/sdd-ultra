# AI Agent Integration

Integration 把同一套 Spec Kit 命令渲染成不同 agent 的 commands、prompts、recipes 或 skills。核心 SDD 语义不因 agent 改变。

## 38 个官方 ID

```text
agy, alquimia, amp, auggie, bob, claude, cline, codebuddy, codex,
command-code, copilot, cursor-agent, devin, droid, firebender, forge,
gemini, generic, goose, grok, hermes, junie, kilocode, kimi, kiro-cli,
lingma, omp, opencode, pi, qodercli, qwen, rovodev, shai, tabnine,
trae, vibe, zcode, zed
```

不要凭记忆假设 agent 路径或 invocation；先运行 `integration list`、`info` 和目标命令的 `--help`。特殊情况包括：

- `codex`：`.agents/skills/speckit-*/SKILL.md`，调用 `$speckit-*`。
- `copilot`：默认 skills；`--commands` 可切换 `.github/agents` + `.github/prompts`。
- `generic`：必须通过 `--commands-dir` 提供自定义目录。
- `kimi`：`--migrate-legacy` 可迁移 `.kimi/skills` 到 `.kimi-code/skills`。
- `hermes`：官方 integration 写全局 `~/.hermes/skills`，属于额外的用户目录写入。
- `pi`：默认没有 MCP，`taskstoissues` 不能按设计工作。
- `rovodev`：生成 skills、prompt wrappers 与 `prompts.yml`。

## 生命周期

```bash
specify integration list [--catalog]
specify integration search [query]
specify integration info <id>
specify integration install <id> [--script py] [--integration-options="..."]
specify integration use <installed-id>
specify integration switch <id>
specify integration upgrade [id]
specify integration status --json
specify integration uninstall [id]
```

- `install` 增加 integration，但不改变 default。只有所有参与者都声明 multi-install safe 时才自动共存，否则需 `--force` 明确认可。
- `use` 只切换已安装的 default，并重新生成共享模板以及所有 enabled extension/preset 的注册产物。
- `switch` 对未安装目标相当于卸载当前 default 再安装；对已安装目标近似 `use`。
- `upgrade` 刷新某个已安装 integration；修改过的托管文件默认阻止升级，`--force` 才覆盖。
- `uninstall` 依据 SHA-256 manifest 自动删除未修改文件并保留已修改文件；`--force` 才删除修改过的文件。
- command/skills layout 改变且 preset 产物仍注册时，先移除 preset，再迁移 layout，再重新安装 preset。

`.specify/integration.json` 记录 `default_integration`、`installed_integrations`、`integration_settings` 和 schema。不要只读取旧的 `integration` alias。

## Extension/Preset 的归属

Extension 和 preset 只注册到当前 default integration。安装另一个非默认 integration 不会自动复制它们；切换 `use`/`switch` 到该 integration 时才重建。升级非默认 integration 也不会注册这些层。

## Catalog

```bash
specify integration catalog list
specify integration catalog add <https-url> [--name <name>]
specify integration catalog remove <zero-based-index>
```

解析顺序：`SPECKIT_INTEGRATION_CATALOG_URL` → 项目 `.specify/integration-catalogs.yml` → 用户 `~/.specify/integration-catalogs.yml` → 官方与 community 内置目录。第一匹配项胜出。

Catalog 添加只允许 HTTPS；loopback HTTP 仅供开发测试。Community integration 不是官方安全审计结果。

## 创作 Integration

在 vendored Spec Kit 开发仓库根运行：

```bash
specify integration scaffold <kebab-case-id> --type markdown|skills|toml|yaml
```

随后补 registry、formatter/setup、tool check、invocation style 与测试。必须保证目标路径 containment、单独 manifest、稳定 invocation，以及 multi-install 声明与真实路径不冲突。
