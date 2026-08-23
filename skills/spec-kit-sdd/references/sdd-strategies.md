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
- 一个 feature 目录通常包含 `spec.md`、`plan.md`、`tasks.md`，并按需包含 `research.md`、`data-model.md`、`contracts/`、`quickstart.md`、`checklists/`。
- Constitution 是项目治理层，不为每个小功能重写；原则改变时才修订并传播模板/文档影响。

## 推荐质量周期

```text
任务后端选择 -> constitution -> specify -> 用户批准 spec -> clarify? ->
plan -> 用户批准 plan -> checklist? -> tasks -> analyze ->
用户批准 tasks + analyze 报告 -> GitLab Issues? -> implement -> converge -> implement? -> converge
```

- `clarify` 只处理高价值歧义，不追求把所有问题都问完。
- `checklist` 审查需求写作质量，不是实现测试清单。
- `analyze` 在任务批准前强制执行：它独立核对真实源码、调用方、相邻测试、`PB-###`、`NM-###` 与回归矩阵，而不只信任 spec/plan/tasks 的声明。存在 `CRITICAL` 时不得请求任务批准；修正 tasks 后必须重新分析。
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
