# 上游开发与同步

## 修改 Spec Kit 本身

用户要开发 upstream CLI、integration、extension、preset、workflow、step 或 bundle 时，以 `vendor/spec-kit/` 为只读基线，在独立工作副本修改，不直接污染已锁定执行快照。

常用入口：

- Python package：`src/specify_cli/`
- Core commands/templates/scripts：`templates/`
- Integration registry/implementations：`src/specify_cli/integrations/`
- Extensions：`extensions/`
- Presets：`presets/`
- Workflows/steps：`workflows/` 与 workflow engine source
- Bundler：`src/specify_cli/bundler/`、`bundles/`
- 官方测试：`tests/`

依赖与 Python 版本以 vendored `pyproject.toml` 为准；当前锁定 Python `>=3.11`。

## 同步新上游

同步必须是可审核的版本迁移，不是 `specify self upgrade`：

1. 在临时目录 fetch 指定 tag/commit，记录完整 SHA。
2. 核对 repository、license、package version、Python/dependency constraints。
3. 生成 tree diff，重点审阅 CLI 注册、下载/认证、path/archive、shell/subprocess、catalog schema 和所有 bundled assets。
4. 运行上游全量测试；在 Python 3.11–3.13、Ubuntu/macOS/Windows 覆盖可用平台。
5. 替换 vendored source，重新构建跨平台 wheelhouse。
6. 运行 `build_vendored_manifest.py --write` 与 `generate_capability_manifest.py`。
7. 比较 `capability-map.json`：任何新增 leaf command 在没有风险分级前不得激活。
8. 比较 10 个 core command、5 个 template、三类 helper、38 integrations、bundled extensions/presets/workflows/catalogs；用户可见中文层的 origin 变更必须重新翻译/复核。
9. 运行 Skill verifier、安装器对抗测试、离线 bootstrap、完整中文 SDD E2E 与生态 smoke tests。
10. 更新 `vendor/upstream-lock.json`，保留旧快照/测试结果以回滚。

## 完整性定义

“完整复制能力”指固定版本的所有 production CLI 命令和运行资产都可从 vendored runtime 到达，并有同版本测试/文档验收；不要求把 Git 历史、CI secrets 或开发者本机缓存当作运行资产。

官方源码和 package data 不做本地逻辑魔改；中文控制面、风险网关和项目叠加层是独立层。若发现上游安全缺陷，先在网关 fail closed，同时在独立开发副本准备可上游化补丁。

## 发布前门槛

- vendored source/wheel manifest 100% 匹配。
- CLI leaf count 与 Typer 实时注册完全一致。
- Integration catalog count/IDs、三类 helper、bundled 组件 count 完全一致。
- 10 个中文核心阶段与同 commit 英文 origin 结构覆盖完整，无旧占位符。
- 离线 runtime 能启动并报告固定 version/commit。
- 上游测试与 Skill 安全/E2E 测试通过。
- 所有未解决差异和平台限制在交付报告中明确列出。
