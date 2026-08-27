# SDD 策略、Brownfield 与 Monorepo

## 先选择规格演化策略

对已有项目，不默认把整个历史系统一次性反向规格化。根据目标选择：

| 策略 | 适用场景 | 做法 |
|---|---|---|
| Flow-forward spec | 新功能或局部改变 | 为变化新建 feature spec，按标准周期向前推进 |
| Living spec | 需要长期维护当前意图 | 规格随实现同步更新，审查 spec 与 code 的双向漂移 |
| Flow-back spec | 遗留模块缺文档且即将高风险修改 | 先从代码/测试提炼现状规格，再明确新旧差异 |

规格描述用户可观察行为、约束、成功标准和边界，不把现有 bug 无条件写成需求。反向整理时标记“observed behavior”“intended behavior”“unknown”，不要凭实现猜产品意图。

所有已有项目策略都同时读取 `brownfield-compatibility.md`。Flow-forward 也不是 greenfield：新 feature spec 必须列出 `PB-###` 受保护行为；Living spec 必须校验既有契约；Flow-back 在改变代码前必须建立 characterization/regression baseline。

## 继承项目传统，而不是另起一套

- 实现方案先从同一个类/组件的相邻方法中找扩展点，再查同模块和同项目的同类实现。
- `plan.md` 必须引用真实符号、路径、相邻测试和项目配置，不能用通用目录骨架代替代码库证据。
- 如果项目已有命名、错误处理、依赖注入、日志、数据访问、测试夹具或 API 版本策略，默认沿用；与宪章/安全要求冲突时才提出偏离并等待用户批准。
- 计划新增抽象时必须记录搜索范围、最近候选、不能复用的具体原因和将遵循的既有样例。没有这些证据时不得生成实现任务。
- Bug 修复只允许目标问题所需的最小改动，不夹带重构、改名、搬目录或风格清理。

## 项目与 Feature 状态

- 项目根由显式 target、`SPECIFY_INIT_DIR` 或 `.specify/` 向上发现确定。
- 活动 feature 由项目 helper/feature state 决定，不只看 Git 分支名；Git 不是 core 必需。
- 一个 feature 目录通常包含 `discovery.md`、`spec.md`、`plan.md`、`tasks.md`，并按需包含 `research.md`、`data-model.md`、`contracts/`、`quickstart.md`、`checklists/`。
- Constitution 是项目治理层，不为每个小功能重写；原则改变时才修订并传播模板/文档影响。

## 推荐质量周期

```text
共同前段：
任务后端选择 -> constitution -> 需求规模判定 -> 需求成熟度评估 -> 需求共创讨论? -> specify

XS / S（精简模式，1 个关卡）：
  ... -> specify（变更说明含内联任务与回归） -> 用户批准变更说明 -> implement

M / L（完整模式，3 个关卡）：
  ... -> 用户批准 spec -> clarify? -> 技术方案共创? -> plan -> 用户批准 plan ->
  checklist? -> tasks -> analyze -> 用户批准 tasks + analyze 报告 ->
  GitLab Issues? -> implement -> converge -> implement? -> converge
```

- **仪式感随规模缩放，安全性不缩放。** 规模判定先于成熟度评估，依据必须是可核实的影响面（文件数、模块数、是否触及公开契约/数据格式/依赖、命中的 `PB-###`），不是需求描述的字面篇幅。任一条件无法确认时往上取一档。
- `XS`/`S` 只产出一份精简 `spec.md`（变更说明），内联任务清单与回归验证，跳过 `plan`/`tasks`/`converge`，`analyze` 转为可选，只有一个批准关卡。
- **红线在 `XS` 上照常全量执行**：`PB-###` 与前后同一基线回归、Bug 根因前置关卡、复用优先与 `NM-###`、破坏性变更禁止、成熟度评估，以及至少一个人工批准。
- **升档单向**：实施中触到档位边界（第二个模块、公开契约、新依赖、未识别的 `PB-###`）立即停止并升档，已有批准失效；不得把超出部分拆成“后续需求”保住低档位。

- 需求成熟度评估在写入任何文件之前执行：目标价值、范围边界、成功判据任一不明确时，必须先逐个展示带推荐项的决策选项与用户共创，把结论以 `DD-###` 落盘 `discovery.md`，然后才写 `spec.md`。用户说“你看着办”只能让你代为选择，不能跳过展示选项。
- `discovery.md` 是需求与技术决策的唯一台账。`clarify` 与 `plan` 的新决策都追加到同一文件，`DD-###` 只增不减，改变主意时追加“取代 DD-00X”。
- `clarify` 只处理高价值歧义，不追求把所有问题都问完；已由 `DD-###` 决定的内容不得重复提问，`discovery.md` 的延后决策是它的最高优先候选问题。
- `checklist` 审查需求写作质量，不是实现测试清单。
- `analyze` 在任务批准前强制执行：它独立核对真实源码、调用方、相邻测试、`PB-###`、`NM-###` 与回归矩阵，而不只信任 spec/plan/tasks 的声明。存在 `CRITICAL` 时不得请求任务批准；修正 tasks 后必须重新分析。
- `plan` 在写入设计产物前识别技术分歧点：存在多条可行路径、需要新依赖或会改变公开契约/`PB-###` 时，先展示方案对比表（含工作量、风险、影响的 `PB-###`/`NM-###`、可逆性）并逐个确认；破坏既有行为、不可逆或需数据迁移的方案不得作为推荐项。
- `converge` 在有 gap 时只追加任务；无 gap 时必须逐字节保持 `tasks.md` 不变。
- 三个批准分别针对用户实际看到的当前 `spec.md`、`plan.md`、以及通过强制 analyze 的 `tasks.md` + 分析报告；不得预批准或合并。上游产物实质变化会使下游批准失效。
- 每个新 feature 开始前明确选择 `local` 或 `gitlab`，不得从 Git remote 猜测。选择写入 `.specify/task-management.json`，不保存凭据。
- `local` 模式以 `tasks.md` 管理执行状态，不创建外部 Issue。
- `gitlab` 模式仍生成 `tasks.md` 作为可审计设计产物；任务获批后才可同步到用户指定的精确 GitLab 项目，并以 Issues 作为日常执行入口。
- `taskstoissues` 是外部写入。GitHub 或 GitLab provider 都只有在任务获批、目标精确且用户明确授权后才执行。
- 新功能和 Bug 修复都必须维护兼容回归关卡：先记录基线，再实现，最后运行相同基线和项目标准验证；任何旧通过项变失败都阻断完成。

## Monorepo

先解析哪个子目录拥有 `.specify`、feature state、constitution 和 agent commands。不要在 monorepo 顶层与 package 子项目间混用根。

- 用 `SPECIFY_INIT_DIR` 或明确 `--target` 固定项目根。
- Contracts/paths/tasks 必须写出 package/service 的真实相对路径。
- 跨包功能在 plan 中明确 owner、接口、迁移顺序和独立验证边界。
- 只初始化用户指定的 project scope；不要因为发现多个 package 就批量写入。

## 产物语言

正文默认简体中文；identifier、代码、协议字段、文件路径、需求/任务编号保持稳定英文。第三方 preset/extension/workflow 的原始 prompt 不声称已翻译，但由本 Skill 生成的项目产物仍遵循中文要求，除非用户指定其他语言。
