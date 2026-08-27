# Bundle

Bundle 用一个 `bundle.yml` 固定 integration、extensions、presets、custom steps 和 workflows 的组合与版本。它不是新的执行引擎，而是调用各 primitive 的生命周期并记录 provenance。

## 预览与生命周期

```bash
specify bundle search [query]
specify bundle info <id>
specify bundle install <id> [--integration <id>]
specify bundle list
specify bundle update [id|--all]
specify bundle remove <id>
specify bundle init [id] [--integration <id>]
```

- `info` 展开全部组件、pin、preset priority/strategy、来源与 verified/community 标记；安装前必须先看这一计划。
- 未初始化目录上，`install`/`init` 可先幂等初始化项目。
- Bundle pin 的 integration 与现有项目 active integration 冲突时，安装中止，不会静默切换。
- 安装是幂等的：已经存在的组件 ID 会跳过。
- 失败时不写 provenance，并 best-effort 移除本次新装组件；移除错误会被吞掉，因此仍需检查磁盘残留。
- `update` 重新解析并通过 primitive update path 刷新所有 pin；`--all` 是破坏性批量操作。
- `remove` 依据 provenance 移除 bundle 拥有的组件；先检查共享/手工安装组件和本地修改。

## 校验、构建与发布

```bash
specify bundle validate <bundle.yml> [--offline]
specify bundle build <source-dir> [--output <dir>]
```

`validate --offline` 只检查 bundled/installed 组件。在线校验中，只有可达 catalog 明确确认引用不存在才失败；离线或 catalog 不可达导致的无法验证只是 warning，不能把 warning 当成供应链已验证。

`build` 生成可发布 artifact。发布时 bundle catalog 只定位 bundle manifest/artifact；其中声明的每个 primitive 仍要通过各自 catalog/bundled/installed 来源解析。

## Catalog

```bash
specify bundle catalog list
specify bundle catalog add <https-url> [--name <name>] [--priority N]
specify bundle catalog remove <source>
```

`search`/`info` 可以在项目外使用 user+built-in catalog。其他状态命令要求项目；`install`/`init` 是例外，可按需初始化。

## 安全验收

安装前输出展开后的组件矩阵：type、ID、version pin、source URL/path、hash/trust、scripts/hooks/shell、预计写路径、integration 冲突。安装后逐一核对 primitive registry 与 bundle provenance；若回滚不完整，保留现场并明确列出残留，不要宣称事务已完全恢复。
