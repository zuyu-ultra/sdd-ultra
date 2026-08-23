# 自定义能力索引

按目标选择最小机制：

| 目标 | 机制 | 读取 |
|---|---|---|
| 单项目替换模板 | `.specify/templates/overrides/` | `presets.md` |
| 组合 commands/templates/scripts | preset | `presets.md` |
| 增加命令、配置、hooks 或 scripts | extension | `extensions.md` |
| 自动化多步流程 | workflow、custom step、overlay | `workflows.md` |
| 固定整套组件与版本 | bundle | `bundles.md` |
| 新 agent 文件格式 | integration | `integrations.md` |

所有目录安装、搜索、升级与移除都通过固定 `scripts/specify_runtime.py`，不依赖 PATH 上的 `specify`。网络、代码执行、覆盖删除、凭据和全局写入的规则见 `security-offline.md`。
