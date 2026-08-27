# SDD Ultra

一个面向中文开发者的规格驱动开发（Specification-Driven Development）项目，包含：

- 可交互的中文 SDD 介绍网站；
- 唯一的 `$sdd` 中文 Codex Skill；
- 固定版本、可离线验证的官方 Spec Kit 运行时与完整仓库镜像。

## 核心能力

`skills/sdd` 内置并固定到 GitHub Spec Kit：

- 版本：`0.16.4.dev0`
- 提交：`83883a2ebad7e7de667fd00381b100d597faf846`
- 84 个 CLI 叶子命令
- 38 个 AI integration
- 10 个完整中文 SDD 阶段
- 539 个上游仓库文件与 28 个离线 wheels

中文版流程覆盖 constitution、specify、clarify、plan、checklist、tasks、analyze、implement、converge 和 task-to-issues，并保留 extension、preset、workflow、bundle、catalog、认证与集成管理等官方能力。

## 仪式感随规模缩放，安全性不缩放

改一行文案和重构支付模块不该走同一条流程。`$sdd` 在评估需求之前先按**可核实的影响面**（文件数、模块数、是否触及公开契约/数据格式/依赖、命中的受保护行为）判定规模档位，判定条件有任何一条无法用项目证据确认时就往上取一档。

| | XS | S | M | L |
|---|---|---|---|---|
| 产物 | 一份变更说明 | 一份变更说明 | spec + plan 分立 | 全套设计产物 |
| 批准关卡 | 1 | 1 | 3 | 3 + checklist |
| 任务清单 | 内联 | 内联 | 独立 `tasks.md` | 独立 `tasks.md` |
| `plan`/`tasks`/`converge` | 跳过 | 跳过 | 强制 | 强制 |

**缩放的只是产物数量和关卡数量。** 受保护行为识别、变更前后同一基线回归、Bug 根因前置关卡、复用优先、破坏性变更禁止、需求成熟度评估，以及至少一个人工批准，在 XS 上一样全量执行。

实施中一旦触到档位边界——要改第二个模块、要动公开契约、要加依赖、碰到没识别出的既有行为——会**立即停止并升档**，原批准失效。不能靠把超出部分拆成"后续需求"来保住低档位。

## 需求模糊时先讨论，再写规格

需求不清楚时，`$sdd` 不会替你假定后直接生成 `spec.md`。写入任何文件之前，它先对目标与价值、用户与角色、范围边界、关键流程、数据与状态、异常与边界、成功判据、约束与非功能、与既有系统的关系、优先级与节奏这十个维度做成熟度评估。

只要目标价值、范围边界、成功判据中任意一项不明确，就进入共创讨论：先复述它对需求的理解请你纠正，然后**每次只提一个决策点**，每个决策点都给出完整问题、为什么重要、带理由的推荐项，以及若干互斥可行方案的对比表（带来什么 / 代价与风险 / 对既有行为的影响），并始终提供自定义和跳过。你可以回复选项字母、`推荐`、`你定`、自己的方案或 `跳过`。

讨论结论以 `DD-###` 落盘到需求目录下的 `discovery.md`，记录问题、选项、推荐和你的最终决定。由 Agent 代选和延后的决策会在 `spec.md` 中显式标出，让你在批准时一眼看到。`clarify` 与 `plan` 阶段的新决策追加到同一份台账，`analyze` 负责检查产物是否和你的决定一致。

`plan` 阶段同样如此：存在多条代价不同的技术路径、需要引入新依赖，或会改变公开契约与既有行为时，先展示方案对比表并逐个确认，再写设计产物。

## 行为评测与对抗性 fixture

静态校验只能确认"规则写在文件里"，不能确认"agent 真的照做"。行为层验收在 `skills/sdd/evals/`：

```bash
python3 scripts/run_evals.py list                             # 列出评测
python3 scripts/run_evals.py brief   --id 17                  # prompt、期望产出、判分项
python3 scripts/run_evals.py prepare --id 17 --sandbox <dir>  # 建隔离沙箱并完成初始化
python3 scripts/run_evals.py check   --id 17 --sandbox <dir>  # 对最终状态执行确定性断言
```

`check` 判断的是可确定的产物状态：该在的文件、不该在的文件、规格里的必需标识、fixture 源码有没有被越权改动、本地模式有没有偷偷建 Git 仓库。**它不判断推理是否正确**——那部分由 `brief` 单独列出，交给人工或 LLM 判分。

三个对抗性 fixture 专门针对最容易被糊弄过去的环节：

| fixture | 陷阱 | 考察 |
|---|---|---|
| `hidden-caller-project` | 调用方通过返回值的**字符串形态**耦合，签名不变的改动照样打断它 | 定档前是否真的搜过调用方 |
| `renamed-duplicate-project` | 等价实现叫 `to_url_key`，名字里没有 `slug` | 检索是否止于关键词匹配 |
| `red-herring-project` | 症状在 `report.py`，根因是 `rules.py` 把 `0` 当成假值吞掉 | 根因是否指向第一个错误状态 |

这些陷阱本身也有测试：天真改动必须真的失败，否则视为陷阱失效。

## Brownfield 安全规则

已有项目默认遵循：

1. 同一个类/组件 → 同模块 → 同业务域 → 同项目的证据顺序；
2. 直接复用 → 兼容扩展 → 提炼共享实现 → 经批准的 `NM-###` 新符号；
3. 使用 `PB-###` 追踪所有不得回退的既有行为；
4. 新需求不得破坏老功能；
5. Bug 必须在写 `spec.md` 前先分析根因，并用 `BUG-###`/`RC-###` 记录完整来龙去脉；
6. Bug 修复不得引入新 Bug。

两条红线不能由用户批准、风险接受、模板、override、workflow 或 hook 豁免。Spec、Plan、Tasks 分别需要用户批准；Tasks 在批准前还必须通过只读 analyze。

## 安装 Codex Skills

只需复制唯一的 `sdd` 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/sdd ~/.codex/skills/
```

在 Codex CLI 中使用：

```text
$sdd 为现有项目增加……
```

每个新 Feature 开始时会先询问使用本地 `tasks.md` 还是 GitLab Issues。本地模式为零 Git 命令模式。

## Obsidian / 自定义目录存储

SDD 产物默认仍保存在项目的 `specs/`。也可以为项目指定一个已存在的 Obsidian 目录或其他绝对路径；选择会保存在项目的 `.specify/sdd-storage.json`，后续需求自动复用该根目录。

外置模式采用“一项需求一个文件夹”：

```text
Obsidian/SDD历史/
├── 2026年08月24日-订单超时修复/
│   ├── discovery.md
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── contracts/
│   ├── tasks.md
│   └── checklists/
└── 2026年08月24日-支付回调优化/
```

项目中只保留活动需求指针和存储配置，不复制这些文档。`clarify`、`plan`、`tasks`、`implement` 等后续阶段会从当前外置需求目录继续读取；历史需求必须通过精确目录或明确选择恢复，不会擅自选择“最新”记录。需要临时恢复项目内存储时，可以明确要求 `$sdd` 使用项目内 `specs/`。

## 运行介绍网站

```bash
npm install
npm run dev
```

生产构建：

```bash
npm run build
```

构建产物位于 `dist/`，可以发布到 Cloudflare Pages：

```bash
npx wrangler pages deploy dist
```

## 验证 Skill

```bash
python3 -B skills/sdd/scripts/verify_skill.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s skills/sdd/tests -p 'test_*.py' -v
```

## 目录结构

```text
.
├── src/                    # SDD 介绍网站
├── design/concepts/        # 网站视觉概念稿
├── skills/
│   └── sdd/                # 唯一的完整中文版 $sdd Skill
├── package.json
└── vite.config.js
```

## 上游与许可

`skills/sdd/vendor/spec-kit/` 是固定提交的 GitHub Spec Kit 完整镜像；其 MIT License 保留在 vendored 源码中。第三方 Python wheels 保留各自的原始许可与元数据。
