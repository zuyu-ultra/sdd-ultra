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

## 行为评测

`scripts/verify_skill.py` 只验证规则文本存在，不验证 agent 是否遵守。行为层验收走 `evals/`：

```bash
python3 scripts/run_evals.py list                       # 列出全部评测及可确定性验证的断言数
python3 scripts/run_evals.py brief --id 17              # 输出 prompt、期望产出与判分项
python3 scripts/run_evals.py prepare --id 17 --sandbox <dir>   # 建沙箱并完成初始化与中文叠加
python3 scripts/run_evals.py check --id 17 --sandbox <dir>     # 对最终状态执行确定性断言
```

- `prepare` 从 `evals/fixtures/` 复制隔离副本，记录源码 SHA-256 基线，再跑官方 `init` 与中文叠加。fixture 若自带 `.specify`/`.agents`/`specs` 则视为真实冲突并拒绝自动覆盖。
- `check` 只判断可确定的产物状态：该在的文件、不该在的文件、规格必需标识、fixture 源码是否被越权修改、本地模式是否偷偷建了 Git 仓库。
- **`check` 通过不等于行为正确。** 推理是否成立（根因是否指向真正的第一个错误状态、是否先搜过调用方再定档、复用判断是否合理）属于 `expectations`，由 `brief` 单独列出交给人工或 LLM 判分。任何把 `check` 结果当作行为已验证的说法都是错的。
- 对抗性 fixture 及其考点：

  | fixture | 陷阱 | 考察 |
  |---|---|---|
  | `hidden-caller-project` | 调用方通过返回值**字符串形态**耦合，签名不变的改动也会打断它 | 定档前是否真的搜过调用方；`PB-###` 识别；升档触发 |
  | `renamed-duplicate-project` | 等价实现名为 `to_url_key`，名字里没有 `slug` 等关键词 | 检索是否止于关键词匹配；复用优先与 `NM-###` 纪律 |
  | `red-herring-project` | 症状在 `report.py`，根因是 `rules.py` 的真值判断把 `0` 吞成 `None` | `RC-###` 是否指向第一个错误状态而非报错位置；检测缺口 |

  这三个 fixture 的陷阱由 `tests/test_eval_harness.py` 实际执行验证——天真改动必须真的失败，否则视为陷阱失效。

## 发布前门槛

- vendored source/wheel manifest 100% 匹配。
- CLI leaf count 与 Typer 实时注册完全一致。
- Integration catalog count/IDs、三类 helper、bundled 组件 count 完全一致。
- 10 个中文核心阶段与同 commit 英文 origin 结构覆盖完整，无旧占位符。
- 离线 runtime 能启动并报告固定 version/commit。
- 上游测试与 Skill 安全/E2E 测试通过。
- 行为评测沙箱可复现建立，确定性断言全部通过，判分项已由人工或 LLM 复核并记录结论。
- 所有未解决差异和平台限制在交付报告中明确列出。
