# Preset 与模板解析

Preset 在不修改 CLI 逻辑的前提下替换或组合 commands、templates 和 scripts。固定快照内置：

- `lean`：精简 constitution/specify/plan/tasks/implement。
- `constitution-sync`：同步 constitution 的特化命令。

## 生命周期

```bash
specify preset search [query]
specify preset info <id>
specify preset add <id|path|url> [--priority N]
specify preset list
specify preset resolve <relative-file>
specify preset set-priority <id> <N>
specify preset disable|enable <id>
specify preset remove <id>
```

较小 priority 先解析且胜出；同 priority 以 ID 字母序稳定排序。每个文件独立解析，因此同一项目的不同文件可以来自不同 preset。

重要区别：`disable` 只把 preset 排除在未来 template/script 解析之外，已经注册进 agent 的 command 仍可能存在。要停止 command 影响，使用 `remove`；要暂时比较模板行为，才使用 `disable`。

## 解析栈

从高到低：

```text
.specify/templates/overrides/
-> .specify/presets/<id>/（priority 小者先）
-> .specify/extensions/<id>/（priority 小者先）
-> .specify/templates/ core
```

物理目录分别含 `templates/`、`commands/`、`scripts/`；不要误写成聚合的 `.specify/presets/templates/`。

组合策略：

| 资产 | 策略 | 占位符 |
|---|---|---|
| template/command | `replace`、`prepend`、`append`、`wrap` | wrap 中用 `{CORE_TEMPLATE}` |
| script | `replace`、`wrap` | wrap 中用 `$CORE_SCRIPT` |

`replace` 是默认策略。用 `preset resolve` 显示某个文件最终来源和层次，不要根据目录存在猜测。

## Catalog

```bash
specify preset catalog list
specify preset catalog add <https-url> --name <name> [--priority N]
specify preset catalog remove <name>
```

解析顺序：`SPECKIT_PRESET_CATALOG_URL`（以同版本 `--help/source` 核对变量名）→ 项目 `.specify/preset-catalogs.yml` → 用户配置 → built-in catalogs。Community preset 未经 Spec Kit 维护者审核。

## 本 Skill 的中文层

中文 10 阶段是 Codex 项目级受管叠加层，用于提供完整中文操作体验；它不伪装为已翻译的第三方 preset。安装 `lean` 等 preset 后，其命令内容以组件原文为准，但本 Skill 的交流和产物仍默认中文。若 preset 覆盖核心命令，先用 `preset resolve` 确认真正生效的文件，再执行。

## 创作与发布

参考 `vendor/spec-kit/presets/ARCHITECTURE.md`、`PUBLISHING.md`、`scaffold/`。发布前验证 safe ID、manifest/schema、所有 composition strategy、跨平台 script wrapper、冲突优先级、disable/remove 语义和来源 hash。
