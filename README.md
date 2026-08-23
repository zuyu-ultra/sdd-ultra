# SDD Ultra

一个面向中文开发者的规格驱动开发（Specification-Driven Development）项目，包含：

- 可交互的中文 SDD 介绍网站；
- 完整中文版 GitHub Spec Kit Codex Skill；
- `$sdd` 快捷入口；
- 固定版本、可离线验证的官方 Spec Kit 运行时与完整仓库镜像。

## 核心能力

`skills/spec-kit-sdd` 固定到 GitHub Spec Kit：

- 版本：`0.16.4.dev0`
- 提交：`83883a2ebad7e7de667fd00381b100d597faf846`
- 84 个 CLI 叶子命令
- 38 个 AI integration
- 10 个完整中文 SDD 阶段
- 539 个上游仓库文件与 28 个离线 wheels

中文版流程覆盖 constitution、specify、clarify、plan、checklist、tasks、analyze、implement、converge 和 task-to-issues，并保留 extension、preset、workflow、bundle、catalog、认证与集成管理等官方能力。

## Brownfield 安全规则

已有项目默认遵循：

1. 同一个类/组件 → 同模块 → 同业务域 → 同项目的证据顺序；
2. 直接复用 → 兼容扩展 → 提炼共享实现 → 经批准的 `NM-###` 新符号；
3. 使用 `PB-###` 追踪所有不得回退的既有行为；
4. 新需求不得破坏老功能；
5. Bug 修复不得引入新 Bug。

两条红线不能由用户批准、风险接受、模板、override、workflow 或 hook 豁免。Spec、Plan、Tasks 分别需要用户批准；Tasks 在批准前还必须通过只读 analyze。

## 安装 Codex Skills

将两个目录复制到 Codex Skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/spec-kit-sdd ~/.codex/skills/
cp -R skills/sdd ~/.codex/skills/
```

在 Codex CLI 中使用：

```text
$sdd 为现有项目增加……
```

每个新 Feature 开始时会先询问使用本地 `tasks.md` 还是 GitLab Issues。本地模式为零 Git 命令模式。

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
python3 -B skills/spec-kit-sdd/scripts/verify_skill.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s skills/spec-kit-sdd/tests -p 'test_*.py' -v
```

## 目录结构

```text
.
├── src/                    # SDD 介绍网站
├── design/concepts/        # 网站视觉概念稿
├── skills/
│   ├── sdd/                # $sdd 快捷入口
│   └── spec-kit-sdd/       # 完整中文版 Spec Kit Skill
├── package.json
└── vite.config.js
```

## 上游与许可

`skills/spec-kit-sdd/vendor/spec-kit/` 是固定提交的 GitHub Spec Kit 完整镜像；其 MIT License 保留在 vendored 源码中。第三方 Python wheels 保留各自的原始许可与元数据。
