---
name: spec-kit-sdd
description: GitHub Spec Kit 的简体中文全能力 Skill。凡用户提到 Spec Kit、Specify CLI、规格驱动开发（SDD）、constitution/spec/plan/tasks/implement/converge、存量项目兼容与回归、安装或升级 Spec Kit、切换 AI integration、extension、preset、workflow、bundle、catalog、认证、离线部署、组件创作或上游开发，都应使用本 Skill。它内置固定官方运行时与中文阶段，强制优先复用项目既有实现和惯例，并阻断破坏老功能或引入新 Bug 的变更。
---

# GitHub Spec Kit 中文全能力

把固定版本的官方 `specify-cli` 当作执行内核，把本 Skill 当作中文控制面。不要重新实现官方 extension、preset、workflow、bundle、catalog、authentication 或 integration 生命周期。

## 固定能力基线

- 官方仓库：`https://github.com/github/spec-kit`
- 提交：`83883a2ebad7e7de667fd00381b100d597faf846`
- 版本：`0.16.4.dev0`
- 叶子 CLI 命令：84
- Integration：38
- 核心 agentic commands：10

官方仓库除 `.git` 对象数据库外的全部 539 个文件原样位于 `vendor/spec-kit/`，覆盖源码、运行资产、文档、测试、CI、开发容器、媒体与项目元数据；SHA-256 清单位于 `vendor/MANIFEST.sha256`。28 个跨平台离线 wheel 位于 `vendor/wheelhouse/`，其他受支持平台若没有匹配 wheel，可在用户授权联网后从 vendored 源码安装依赖。

需要精确命令和参数时读取 `references/capability-map.json`，并以固定运行时的实时 `--help` 为最终依据。禁止调用 PATH 上版本不明的 `specify`。

## 语言与兼容性

- 默认用简体中文交流，并用简体中文生成 constitution、spec、plan、research、data model、contracts、quickstart、tasks、checklist 和分析报告。
- 用户明确指定其他语言时遵从用户。
- 命令、路径、文件名、integration ID、extension/preset/workflow/bundle ID、环境变量、JSON/YAML 键、占位符、`FR-*`、`SC-*`、`T###`、`[P]` 与 `[US#]` 保持英文。
- 第三方组件保持原文并标明“外部内容，未由本 Skill 翻译或审计”；不得暗示社区目录已经安全审查。

## 存量项目兼容红线

已有代码的功能开发或缺陷修复必须读取 `references/brownfield-compatibility.md`，并执行其中的复用证据、受保护行为、影响面、回归矩阵和完成证据要求。

- 项目既有惯例优先于模型偏好的通用模式：先检查同一个类/组件，再检查同模块，最后检查项目同类实现。
- 存在等价 method/class/service/helper/endpoint/schema、dependency 或测试夹具时必须复用或扩展；每个确需新增的符号必须以 `NM-###` 记录检索范围、候选和不能复用的具体理由，并随 `plan.md` 一起批准。实施时才出现的未批准新符号会使 plan/tasks 批准失效。
- **红线 1：新需求不得破坏老功能。** 每个受影响既有行为必须分配 `PB-###`，并在变更前后运行同一组基线/回归验证。
- **红线 2：修复 Bug 不得引入新 Bug。** 必须先复现失败，再做最小修复，并验证相邻正常、异常和边界路径。
- 任一旧测试由通过变为失败、公共契约发生不兼容变化、`PB-###` 未通过或必需验证未运行，立即阻断；不得勾选任务或报告完成。两条红线绝对不可通过用户批准、规格声明、风险接受、override、preset、extension、workflow 或 hook 豁免。
- 需求确实要替换既有行为时，只能在当前 `PB-###` 和既有调用方继续通过的前提下，增加兼容适配层、并行版本或迁移路径；旧入口只能在调用方全部完成迁移、旧基线仍通过且另立独立退役 feature 后处理。当前 feature 不得把“用户批准破坏性变更”解释为允许回退旧行为。
- 模板、replace override、preset、extension、bundle、workflow 和 hook 只能增加约束，不能删除或弱化本节；阶段资产过旧或缺少安全章节时仍以本节为最高优先级，并回到对应阶段补齐文档。
- 每个实际执行的 before/after hook（包括用户随后选择执行的可选 hook）必须在执行前后分别对该阶段相关产物逐文件计算 SHA-256；新增、删除、重命名、目标变化或摘要变化都视为实质变化。每个 hook 后立即重新读取并重验 `PB-###`、`NM-###`、调用方、变更前基线和回归矩阵；不能通过时立即阻断。Hook 造成的实质变化使相关 spec/plan/tasks 批准失效，必须回到拥有该产物的阶段重新批准。

## 每次开始时

1. 将 `<skill-dir>` 解析为本文件所在目录。
2. 验证固定资产：

   ```bash
   python3 <skill-dir>/scripts/build_vendored_manifest.py
   python3 <skill-dir>/scripts/specify_runtime.py status
   ```

3. 运行时缺失时先尝试离线安装：

   ```bash
   python3 <skill-dir>/scripts/specify_runtime.py ensure
   ```

   若当前平台没有匹配 wheel，说明将下载 Python 依赖；用户同意后才加 `--allow-network`。
4. 解析项目根：显式 `--target` 最高；其次使用 `SPECIFY_INIT_DIR`；再从当前目录查找 `.specify/`；只有非 project-scoped 操作才可不依赖项目。
5. 对现有项目读取 `.specify/init-options.json`、`.specify/integration.json`、托管 manifest、registry 和 locale 元数据。只有任务后端不是 `local` 且当前请求确实需要版本控制信息时才可读取 Git 状态；不得从分支名猜活动 feature。
   - 对 Codex skills 项目先运行 `python3 <skill-dir>/scripts/install_project.py --target <repo-root> --check`。只有目标文件 SHA-256 精确匹配本 Skill 自带的 `manifests/managed-predecessors.json`，或精确匹配固定上游原文件时，才运行一次不带 `--force` 的安全升级。项目内可写的 integration manifest 只能在安全更新后刷新，绝不能授权覆盖。
   - 用户改过的阶段 Skill、模板或元数据，以及没有随 Skill 固定哈希清单的未知旧版本资产，必须原样保留并报告；混合状态不得把 `bundle_revision` 伪装成当前版本，也不得为升级使用 `--force`。即使项目副本过旧，仍以本根 Skill 的兼容红线为最高优先级，并要求用户审阅冲突后再决定逐文件迁移。
6. 在创建本轮功能规格前确定任务管理后端。不得根据 Git remote、目录名或已安装 CLI 猜测：
   - 如果用户已在本轮请求中明确选择，采用该选择。
   - 否则阻塞并询问：“本功能的任务使用本地 `tasks.md` 管理，还是同步到 GitLab Issues 管理？”
   - `local` 是安全默认选项；只维护 `tasks.md`，禁止外部 Issue 写入，并把 `vcs` 记录为 `none`。
   - `local` 是严格零 Git 命令模式：不得启动 `git` 可执行文件，不得检查 `.git`、读取 remote、创建/切换分支、运行 status/diff/log，不得调用 `speckit.git.*` Skill 或 extension hook，也不得仅为版本控制创建或修改 `.gitignore`。用目录清单、文件内容、SHA-256、manifest 和 `.specify/feature.json` 完成定位与验证。此规则覆盖项目阶段 Skill、官方提示模板和扩展钩子的相反指令。
   - `gitlab` 必须同时取得精确项目 URL 或 `group/project`；在 `tasks.md` 获得用户批准前不得创建 Issue。
   - 将选择写入 `.specify/task-management.json`：本地模式至少包含 `{"backend":"local","vcs":"none"}`；GitLab 模式包含 `backend`、`project` 和 `host`，不得写入 token。每个新 feature 都要向用户复述当前选择并允许变更。

## 安全调用网关

所有完整 CLI 操作都通过：

```bash
python3 <skill-dir>/scripts/specify_runtime.py classify -- <specify-args>
python3 <skill-dir>/scripts/specify_runtime.py run --target <repo-root> [授权参数] -- <specify-args>
```

网关只运行固定 runtime、使用参数数组而非 shell 字符串，并默认剥离常见凭据环境变量。

| 风险 | 授权参数 | 允许条件 |
|---|---|---|
| 本地只读 | 无 | 可直接执行并报告 |
| 网络读取或下载 | `--allow-network` | 用户请求搜索、联网检查、下载或安装 |
| 项目写入 | `--allow-project-write` | 用户明确要求初始化、安装、切换、生成或修改项目 |
| 第三方/工作流代码执行 | `--allow-code-execution` | 已展示来源、hooks、shell/custom step，并且用户明确要求执行 |
| 覆盖、删除、卸载或批量更新 | `--allow-destructive` | 已解析精确目标、展示影响和恢复方式，且用户明确同意 |
| Runtime/全局写入 | `--allow-runtime-write` | 用户明确要求 CLI 自更新；优先更新本 Skill 的固定上游快照 |
| 凭据 | `--allow-credentials` | 用户授权精确 provider、host 和操作；不得在输出中显示 token |

- `workflow run/resume`、`event run` 和自定义 step 没有安全沙箱；执行前读取并展示解析后的 `shell`、agent command、输入插值和 hooks。
- 不把未约束用户输入或 agent 输出直接插入 workflow `shell.run`；官方表达式不会自动做 shell escaping。
- 外部 URL 必须是 HTTPS（loopback 开发地址除外），安装前检查来源、manifest、hash、路径、脚本和 hooks。
- `taskstoissues`、发布、认证和其他外部写入必须由用户明确指定目标。GitHub 或 GitLab Issues 目标必须与用户批准的精确仓库/项目一致；不能只凭当前目录推断。
- 固定 runtime 中的 `specify self upgrade` 会破坏版本锁；除非用户明确要求在可丢弃环境测试，否则使用“上游同步”流程。

## 初始化完整项目

新项目或需要补齐官方能力的项目，先运行官方初始化，再叠加中文资产：

```bash
python3 <skill-dir>/scripts/specify_runtime.py run \
  --target <repo-root> --allow-project-write -- \
  init --here --integration codex --integration-options=--skills \
  --script py --ignore-agent-tools

python3 <skill-dir>/scripts/install_project.py --target <repo-root>
```

- 官方 `init` 本身不执行 Git 命令；`--ignore-agent-tools` 还会跳过 agent CLI 探测。`--force` 也不是 Git 的 force：它只让 `specify init --here` 在非空目录跳过交互确认，并允许合并或覆盖同名初始化文件。
- 官方支持 `sh`、`ps`、`py` 与 38 个 integration；按用户需求选择。第二条 `install_project.py` 只用于 `codex --skills`，因为它安装的是 `.agents/skills` 中文阶段；使用其他 integration 时只执行官方初始化，并由本 Skill 用中文控制流程，不把 Codex 资产写入其他 agent 目录。
- 非空目录只说明官方 CLI 在非交互调用中无法询问确认，不等于存在文件冲突，也不等于必须立即请求破坏性授权。先仅用文件系统清单和内容哈希检查所有计划写入路径；本地模式禁止用 Git status/diff 做预检。没有 SDD 文件且目标路径无冲突时，明确说明 `--force` 只是跳过上游的“目录非空”确认；存在任一同名且内容不同的文件时停止并列出冲突，只有用户针对这些精确文件明确接受覆盖后才加 `--force` 与 `--allow-destructive`。不得只因目录非空就声称“必须覆盖”。
- 中文叠加层拒绝子路径 symlink，原子写入托管资产，只自动替换已知未填写 constitution；自定义 constitution、`specs/`、override、preset、extension 和用户文件保持不变。
- 初始化后运行 `install_project.py --check`；`missing`、`modified`、错误 locale、错误 commit 或 unsafe path 都必须返回非零。

## 核心中文 SDD 路由

执行阶段前完整读取项目中的 `.agents/skills/<stage>/SKILL.md`：

| 用户意图 | 阶段 | 主要产物或行为 |
|---|---|---|
| 建立治理原则 | `speckit-constitution` | `.specify/memory/constitution.md` |
| 定义功能 | `speckit-specify` | `spec.md`、内置需求检查表 |
| 消除高价值歧义 | `speckit-clarify` | 写回 `spec.md` 并重验检查表 |
| 研究和技术设计 | `speckit-plan` | `plan.md`、research、data model、contracts、quickstart |
| 审阅需求写作质量 | `speckit-checklist` | reviewer-owned checklist |
| 拆分可执行任务 | `speckit-tasks` | `tasks.md` |
| 只读一致性分析 | `speckit-analyze` | 不写文件的分析报告 |
| 按任务实现 | `speckit-implement` | 源码与已完成任务标记 |
| 规格到代码收敛 | `speckit-converge` | 只追加剩余任务，或保持文件不变 |
| 同步 GitHub/GitLab Issues | `speckit-taskstoissues` | 任务获批且明确授权目标后的去重 Issues |

默认质量周期（`✓` 表示必须等待用户明确批准）：

```text
任务后端选择 -> constitution（通常一次） -> specify -> ✓spec -> clarify? ->
plan -> ✓plan -> checklist? -> tasks -> analyze -> ✓tasks ->
GitLab Issues? -> implement -> converge -> implement? -> converge
```

三个批准关卡不可合并、预授权或由模型代替用户通过：

- 生成/更新 `spec.md` 后，报告范围、关键需求、未决问题和文件路径，询问是否批准进入规划，并停止。
- 生成/更新 `plan.md` 及设计产物后，报告技术选择、宪章偏差、风险和文件路径，询问是否批准生成任务，并停止。
- 生成/更新 `tasks.md` 后，必须先对当前精确版本执行 `$speckit-analyze`，独立核对真实源码、复用证据、`PB-###`、`NM-###` 和回归关卡。存在 `CRITICAL` 时修正任务并重新分析，不得请求批准；通过后同时报告任务摘要与分析结果，再询问是否批准执行。只有批准后才能实现，GitLab 模式也只有此后才能同步 Issues。
- 批准只适用于用户看到的当前版本。批准后若该阶段产物发生实质修改，立即失效；上游产物变化同时使下游批准失效。新对话中看不到明确批准证据时必须重新询问。

官方内置 `speckit` workflow 的本 Skill 中文安全层定义为：`specify -> review-spec -> plan -> review-plan -> tasks -> analyze -> review-tasks -> GitLab sync? -> implement`。`review-tasks` 必须同时审阅当前 tasks 与同一 SHA-256 版本的分析结果。

## CLI 与生态能力路由

| 意图 | 先读取 | 命令族 |
|---|---|---|
| 安装、检查、版本、自更新、初始化 | `references/cli-core.md` | `init`、`check`、`version`、`self` |
| 切换或创作 AI agent integration | `references/integrations.md` | `integration ...` |
| 安装、配置或创作 extension；hooks/events | `references/extensions.md` | `extension ...`、内部 `event run` |
| 叠加或创作 preset、模板解析 | `references/presets.md` | `preset ...` |
| 执行、恢复或创作 workflow、step、overlay | `references/workflows.md` | `workflow ...` |
| 搜索、安装、构建或发布 bundle | `references/bundles.md` | `bundle ...` |
| Catalog、认证、下载和离线策略 | `references/security-offline.md` | 各 `catalog ...` 与 `~/.specify/auth.json` |
| 修改 Spec Kit 本身或同步新上游 | `references/upstream-development.md` | vendored source、测试与同步流程 |
| 核心 SDD 策略、brownfield、monorepo | `references/sdd-strategies.md` | feature state 与阶段组合 |
| 存量代码复用、项目惯例、回归红线 | `references/brownfield-compatibility.md` | `PB-###`、复用决策、影响面与回归矩阵 |

## 标准执行协议

1. 读取相关 reference 和命令的固定 runtime `--help`；文档与 CLI 不一致时以同版本 CLI/source 为准。
2. 先运行只读的 `status`、`list`、`info`、`resolve`、`validate` 或 `--dry-run`，获取当前状态和精确目标。
3. 用 `classify` 输出风险；只把用户当前请求已经授权的能力映射为网关参数。需要新增授权时停止并说明影响。
4. 对组件安装读取来源 manifest；对 workflow 展开 step graph、overlay 和 shell；对 bundle 展开完整组件集合。
5. 执行后核对退出码、manifest/registry、locale、生成文件和组件状态；本地模式用文件清单与 SHA-256 验证，禁止运行 Git diff。不要靠英文终端文本猜成功。
6. 错误应回到拥有问题的层修复：需求、设计、任务、组件 manifest、catalog 或 runtime，不要掩盖状态漂移。
7. 阶段命令不得串行越过人工关卡。即使用户最初要求“全部完成”或 workflow 可自动继续，也必须分别在 `spec`、`plan`、`tasks` 产出后暂停，等待针对当前产物的明确批准。
8. 对存量项目，在计划任何新符号前先用项目内搜索和相邻测试证明无可复用实现，并为例外分配 `NM-###`；实现后用与变更前相同的命令验证既有行为。不得以“测试未运行”“看起来没影响”或仅新测试通过作为完成依据。

## 自定义层解析

模板优先级从高到低：

```text
.specify/templates/overrides/
-> .specify/presets/<id>/templates/（priority 小者优先）
-> .specify/extensions/<id>/templates/
-> .specify/templates/
```

Preset 支持 `replace`、`prepend`、`append`、`wrap`；script 只支持 `replace`、`wrap`。`disable` 不会自动删除已经注册的 command；要停止其命令影响需要 `remove`。第三方层不保证中文。

## 上游同步

用户明确要求升级时：

1. 只读检查远端 commit、release 和 CLI 能力差异。
2. 在临时目录取得新版本，核对 repository、commit、version、license、依赖和安全测试。
3. 更新 vendored source、wheelhouse、SHA 清单和 `capability-map.json`。
4. 对 10 个命令、5 个模板及内置 extension/preset/workflow 的用户可见变更重新完成中文覆盖。
5. 运行上游测试、CLI parity、安装器对抗测试和中文端到端评测；任何新增 CLI 命令未分级或中文资产漂移都阻止激活。
6. 保留旧快照用于回滚；不得直接让固定 runtime 静默升级。

## 完成报告

用中文报告：固定版本和 commit、项目根、执行的命令族与授权风险、创建/修改/保留的文件、manifest/registry 状态、测试结果、外部组件来源、未解决风险和下一步。若仅执行只读命令，要明确说明没有写入。
