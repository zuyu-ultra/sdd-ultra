---
name: sdd
description: 唯一的中文规格驱动开发（SDD）Skill。用户输入 `$sdd`、`$SDD`，或要求执行 constitution、spec、plan、tasks、implement、converge、存量项目兼容、Bug 根因分析及 Spec Kit 工作流时使用。它内置完整能力，但对外只提供普通的 SDD 入口。
---

# SDD

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
- **红线 2：修复 Bug 不得引入新 Bug。** 必须先分析并确认根因，再写可执行的 Bug `spec.md`；先复现失败，再做最小修复，并验证相邻正常、异常和边界路径。
- **Bug 根因前置关卡：** 在创建或填写 Bug `spec.md` 前，先只读调查并追踪“触发条件 → 执行路径 → 第一个错误状态/值 → 外部症状”。用 `BUG-###` 记录缺陷、用 `RC-###` 记录根因证据，区分根因、触发条件、促成因素、影响范围与未被既有测试发现的原因。`spec.md` 必须讲清发现背景、受影响环境、复现证据、因果链、根因及置信度、检测缺口和不受影响边界；已有文件/符号/日志/堆栈只能作为观察证据引用，不能在规格阶段预设新实现。
- 无法确认根因时不得臆测。可以生成明确标为“根因未确认”的诊断草稿，记录证据、候选假设与下一步取证，但该规格不得获准进入 `plan`、`tasks` 或实现；计划关卡只接受有可复核证据的已确认 `RC-###`。
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
6. 在创建或恢复本轮需求前确定 **SDD 产物存储位置**。存储位置与任务管理后端是两个独立选择，不能混为一谈：
   - 解析优先级固定为：用户本轮明确给出的需求目录或存储根目录 > 项目 `.specify/sdd-storage.json` 中已保存的选择 > 项目内默认 `<repo-root>/specs/`。默认值无需额外打断用户。
   - `project` 模式把每个需求保存在 `<repo-root>/specs/<NNN-short-name>/`；这仍是本地任务模式的默认行为。
   - `external` 模式用于 Obsidian 或任意用户指定目录。用户必须给出或明确确认一个**绝对、已存在的目录**作为 `artifact_root`；用户只说“放到 Obsidian”但没有可确定的精确路径时，先询问路径并停止，不能猜 vault。
   - 外置模式下，一个需求只对应一个子目录，默认名称为 `YYYY年MM月DD日-中文需求名`；同日同名已存在时依次使用 `-02`、`-03`。目录内统一保存 `discovery.md`、`spec.md`、`plan.md`、`research.md`、`data-model.md`、`quickstart.md`、`contracts/`、`tasks.md` 和 `checklists/`。除该目录内的 `.sdd-feature.json` 项目归属元数据外，不把这些需求产物复制回项目。
   - 项目内只保留 `.specify/feature.json` 活动需求指针和 `.specify/sdd-storage.json` 存储配置。外置路径必须写为绝对路径；不得把 Obsidian 文件夹创建成 Git 分支，不得因为外置存储而执行 Git。
   - 新需求可复用已保存的外置 `artifact_root`，但必须创建新的独立需求子目录。恢复历史需求时，用户给出的精确目录最高；否则使用已保存的活动指针。若名称匹配多个目录或项目没有唯一活动需求，列出候选并询问，禁止擅自选“最新”目录。读取外置需求前校验它位于获准的根目录内，且 `.sdd-feature.json` 未声明属于其他项目。
   - 后续 `clarify`、`plan`、`checklist`、`tasks`、`analyze`、`implement`、`converge` 必须使用 helper 返回的绝对 `FEATURE_DIR`；不得重新拼接 `<repo-root>/specs/`，不得在项目内生成同名副本。每次阶段报告都复述存储模式、根目录和当前需求目录。
7. 在创建本轮功能规格前确定任务管理后端。不得根据 Git remote、目录名或已安装 CLI 猜测：
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

## 需求规模分级

**仪式感随规模缩放，安全性不缩放。** 改一行文案和重构支付模块不该走同一条流程；但两者的存量兼容红线完全相同。在成熟度评估之前先判定规模，依据必须是可核实的影响面，不是主观感觉。

| 档位 | 判定条件（须全部满足） | 典型 |
|---|---|---|
| `XS` | 单文件；不改公开契约、数据格式或依赖；不新增公开行为；既有测试即可覆盖 | 文案、常量、日志、注释、样式微调 |
| `S` | ≤3 文件且限于单一模块；不改公开契约与数据格式；无新依赖；新符号仅模块内私有 | 加一处校验、加一个可选参数、单点 Bug 修复 |
| `M` | 跨模块，或新增公开接口/数据字段，或新增依赖，或影响任一 `PB-###` | 常规功能需求 |
| `L` | 跨服务/子系统；数据迁移；不可逆变更；公开契约不兼容变化；影响面在评估时无法收敛 | 架构级改动 |

- **不确定就往上取。** 任一判定条件无法用项目证据确认时采用更高一档；不得为了省流程往下压。存量项目必须先只读检索确认影响面，不得凭需求描述的字面篇幅判断。
- 分级结论、支撑证据和该档位跳过的阶段必须写入产物并向用户复述。用户可以要求升档；**用户不能要求降档到红线之下**。

### 各档执行差异

| | XS | S | M | L |
|---|---|---|---|---|
| 产物 | 精简 `spec.md`（变更说明） | 精简 `spec.md`（变更说明） | `spec.md` + `plan.md` 分立 | 全套含 research/data-model/contracts |
| 批准关卡 | 1（批准变更说明） | 1（批准变更说明） | 3（spec/plan/tasks） | 3 + checklist |
| 任务清单 | 内联在 `spec.md` | 内联在 `spec.md` | 独立 `tasks.md` | 独立 `tasks.md` |
| `plan`/`tasks` 阶段 | 跳过 | 跳过 | 强制 | 强制 |
| `analyze` | 可选 | 可选 | 强制 | 强制 |
| `converge` | 不需要 | 不需要 | 需要 | 需要 |
| 共创决策点上限 | 3 | 3 | 7 | 7 |

### 永不缩放的红线（XS 同样全量执行）

1. `PB-###` 受保护行为识别，以及变更前后运行同一组基线回归。
2. Bug 根因前置关卡：`BUG-###`/`RC-###`、完整因果链、先复现失败再最小修复。
3. 存量复用优先：存在等价实现必须复用或扩展，新增符号仍需 `NM-###` 理由。
4. 破坏既有行为必须走兼容适配层或并行版本，不得直接替换。
5. 需求成熟度评估：目标价值、范围边界、成功判据不明确时仍须先讨论并落 `DD-###`。
6. 至少一个人工批准关卡。**任何档位都不存在零批准。**

### 升档是单向的

实施中发现实际影响超出当前档位——需要改第二个模块、要动公开契约、要加依赖、触到评估时未识别的 `PB-###`——**立即停止**，报告触发条件并升档。已有批准全部失效，按新档位补齐缺失阶段后重新批准。不得因为“已经写了一半”而维持低档位继续，也不得把超出部分拆成“后续需求”来保住当前档位。

## 模糊需求的共创讨论

需求模糊时的正确动作是**先把选择摆出来和用户一起定**，不是替用户假定后直接生成 `spec.md` 或 `plan.md`。

- **需求成熟度评估**（`$speckit-specify` 步骤 1b，写入任何文件之前强制）：对目标与价值、用户与角色、范围边界、关键流程、数据与状态、异常与边界、成功判据、约束与非功能、与既有系统的关系、优先级与节奏这十个维度判定 `明确`/`部分`/`缺失`。判定依据只能是用户输入、既往对话中的明确结论或项目内可核实证据，不得把模型的通用假设算作“明确”。
- **路由**：不存在 `缺失`、`部分` 不超过 2 个，且目标价值/范围边界/成功判据三项均 `明确` 时直接起草规格；否则进入共创讨论。只要这三项中任意一项不是 `明确`，即使用户说“你看着办”“直接写”，也必须先把选项摆出来；用户可以把决定权交回给你，但不能跳过展示选项这一步。
- **讨论形式**：先复述需求理解请用户纠正，然后**每次只展示一个决策点**，最多 7 个。每个决策点给出完整疑问句、为什么重要、带理由的推荐项，以及 2–5 个互斥可实施方案的对比表（方案 / 带来什么 / 代价与风险 / 对既有行为的影响），并始终提供自定义与延后选项。用户可回复选项字母、`推荐`、`你定`、自定义描述或 `跳过`。
- **落盘**：讨论结论写入需求目录下的 `discovery.md`，逐条编号为 `DD-###`，记录问题、选项、推荐、用户最终决定和受影响的 `FR-###`/`SC-###`/`PB-###`。判定为直接起草时同样生成精简 `discovery.md`，列出被采用的默认值。`DD-###` 只增不减；改变主意时追加新条目并注明“取代 DD-00X”。
- **单一台账**：`$speckit-clarify` 与 `$speckit-plan` 产生的新决策追加到同一个 `discovery.md`，`spec.md` 只在 `## 需求共创决策` 章节引用 `DD-###`。`$speckit-analyze` 负责检查产物与决策是否一致。
- **技术分歧点**（`$speckit-plan` 步骤 2a）：存在多条都能满足规格但代价不同的技术路径、需要引入新依赖或新边界、会改变公开契约或任一 `PB-###`、需要在最小改动与重构之间取舍时，同样先展示方案对比表并逐个确认，最多 5 个。破坏既有行为、不可逆或需要数据迁移的方案不得作为推荐项。
- **边界**：讨论不能替代证据。Bug 的根因不是可讨论选项，用户选择不得把未确认 `RC-###` 升级为已确认；共创讨论也不得弱化存量兼容红线——用户选择了破坏既有行为的方案时，仍须走兼容适配层或独立退役 feature 的路径。
- 讨论期间不写文件，不输出规格草稿全文，不调用下游阶段。三个批准关卡不因已经讨论过而被跳过。

## 核心中文 SDD 路由

执行阶段前完整读取项目中的 `.agents/skills/<stage>/SKILL.md`：

| 用户意图 | 阶段 | 主要产物或行为 |
|---|---|---|
| 建立治理原则 | `speckit-constitution` | `.specify/memory/constitution.md` |
| 定义功能 | `speckit-specify` | 成熟度评估、共创讨论、`discovery.md`、`spec.md`、内置需求检查表 |
| 消除高价值歧义 | `speckit-clarify` | 写回 `spec.md` 并重验检查表 |
| 研究和技术设计 | `speckit-plan` | 技术方案共创、`plan.md`、research、data model、contracts、quickstart |
| 审阅需求写作质量 | `speckit-checklist` | reviewer-owned checklist |
| 拆分可执行任务 | `speckit-tasks` | `tasks.md` |
| 只读一致性分析 | `speckit-analyze` | 不写文件的分析报告 |
| 按任务实现 | `speckit-implement` | 源码与已完成任务标记 |
| 规格到代码收敛 | `speckit-converge` | 只追加剩余任务，或保持文件不变 |
| 同步 GitHub/GitLab Issues | `speckit-taskstoissues` | 任务获批且明确授权目标后的去重 Issues |

默认质量周期（`✓` 表示必须等待用户明确批准）：

```text
共同前段：
产物存储选择 -> 任务后端选择 -> constitution（通常一次） -> 需求规模判定 ->
Bug 根因调查? -> 需求成熟度评估 -> 需求共创讨论? -> specify

XS / S（精简模式，1 个关卡）：
  ... -> specify（变更说明含内联任务与回归） -> ✓变更说明 -> implement

M / L（完整模式，3 个关卡）：
  ... -> specify -> ✓spec -> clarify? -> 技术方案共创? -> plan -> ✓plan ->
  checklist? -> tasks -> analyze -> ✓tasks -> GitLab Issues? ->
  implement -> converge -> implement? -> converge
```

完整模式的三个批准关卡不可合并、预授权或由模型代替用户通过；精简模式的单一关卡同样不可省略：

- 生成/更新 `spec.md` 后，报告成熟度评估结论、`DD-###` 决策清单（含“由 Agent 代选”和延后项）、范围、关键需求、未决问题和文件路径，询问是否批准进入规划，并停止。目标价值、范围边界或成功判据仍为“缺失”时只报告阻塞，不得请求批准。
- Bug 规格只有在 `RC-###` 已确认、因果链与证据可复核时才能请求“批准规格”；根因未确认的诊断草稿只能请求补充取证，不能进入规划。
- 生成/更新 `plan.md` 及设计产物后，报告技术选择、宪章偏差、风险和文件路径，询问是否批准生成任务，并停止。
- 生成/更新 `tasks.md` 后，必须先对当前精确版本执行 `$speckit-analyze`，独立核对真实源码、复用证据、`PB-###`、`NM-###` 和回归关卡。存在 `CRITICAL` 时修正任务并重新分析，不得请求批准；通过后同时报告任务摘要与分析结果，再询问是否批准执行。只有批准后才能实现，GitLab 模式也只有此后才能同步 Issues。
- 批准只适用于用户看到的当前版本。批准后若该阶段产物发生实质修改，立即失效；上游产物变化同时使下游批准失效。新对话中看不到明确批准证据时必须重新询问。

官方内置 `speckit` workflow 的本 Skill 中文安全层定义为：`Bug root-cause? -> discovery? -> specify -> review-spec -> plan -> review-plan -> tasks -> analyze -> review-tasks -> GitLab sync? -> implement`。Bug 的 root-cause 调查和需求共创讨论都发生在 `specify` 写入前；`review-spec` 同时审阅 `spec.md` 与 `discovery.md` 的 `DD-###`；`review-tasks` 必须同时审阅当前 tasks 与同一 SHA-256 版本的分析结果。

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
| 运行行为评测、准备对抗性沙箱 | `evals/evals.json` | `scripts/run_evals.py list/brief/prepare/check` |
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
9. 对 Bug，在任何 `spec.md` 写入前完成根因调查；`plan`、`tasks` 和实现必须追踪到同一已确认 `RC-###`。实施证据推翻根因时立即停止，所有受影响的 spec/plan/tasks 批准失效，回到根因调查与规格阶段。

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
5. 运行上游测试、CLI parity、安装器对抗测试和中文端到端评测；任何新增 CLI 命令未分级或中文资产漂移都阻止激活。行为评测用 `python3 <skill-dir>/scripts/run_evals.py prepare/check` 在隔离沙箱中执行：`check` 只验证可确定的产物状态（该在的文件、不该在的文件、规格必需标识、fixture 源码未被越权改动、本地模式没有建 Git 仓库），推理正确性仍需按 `brief` 输出的判分项人工或 LLM 判分——**不得把 `check` 通过当作行为已验证**。
6. 保留旧快照用于回滚；不得直接让固定 runtime 静默升级。

## 完成报告

用中文报告：固定版本和 commit、项目根、执行的命令族与授权风险、创建/修改/保留的文件、manifest/registry 状态、测试结果、外部组件来源、未解决风险和下一步。若仅执行只读命令，要明确说明没有写入。
