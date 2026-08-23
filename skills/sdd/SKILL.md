---
name: sdd
description: 完整中文版 GitHub Spec Kit SDD 的短名称入口。用户输入 `$sdd`、提到 `/sdd`、要求启动规格驱动开发，或希望执行 constitution、spec、plan、tasks、implement、converge 流程时使用；实际能力、安全关卡、存量代码复用、回归红线、任务后端选择和中文资产全部委托给同级 `spec-kit-sdd` Skill。
---

# SDD 中文快捷入口

把本 Skill 作为 `spec-kit-sdd` 的稳定短入口，不复制或缩减其实现。

## 执行协议

1. 将 `<sdd-skill-dir>` 解析为本文件所在目录。
2. 完整读取 `<sdd-skill-dir>/../spec-kit-sdd/SKILL.md`。若文件缺失或无法读取，停止并明确报告完整 Skill 不可用；不得用常识重建一个简化流程。
3. 把用户在 `$sdd` 后提供的内容视为原始 SDD 请求。若客户端把字面 `/sdd` 作为普通消息发送，也按相同方式处理；不要要求用户重复描述。
4. 严格遵循 `spec-kit-sdd` 的全部路由、固定运行时、安全授权、中文规则和完成报告要求，按需读取它直接引用的 references 与项目阶段 Skill。
5. 每个新 feature 开始前先询问任务管理后端：本地 `tasks.md` 或 GitLab Issues；不得从 Git remote 推断。
6. 用户选择本地 `tasks.md` 时启用严格零 Git 命令策略：不得执行 `git`、调用 `speckit.git.*`、检查 `.git`、读取 remote、创建或切换分支、运行 status/diff/log，或写入外部 Issues。该策略覆盖下游阶段 Skill 和扩展钩子的相反指令。
7. `spec.md`、`plan.md` 分别生成后立即停止并等待批准；`tasks.md` 生成后先对当前精确版本强制执行只读 `$speckit-analyze`，无 `CRITICAL` 时展示任务与分析并停止等待任务批准。不得合并、预先通过或绕过三个用户关卡。
8. 对已有代码，必须先寻找并优先复用同类/同项目现有实现，遵循相邻代码惯例；每个确需新增的符号必须有随计划批准的 `NM-###`，实施时出现未批准的新符号必须退回计划。“新需求破坏老功能”和“修 Bug 引入新 Bug”是不可豁免的阻断红线，用户批准或风险接受也不能放行。缺少既有实现证据、回归基线或必需测试时不得进入或完成实现，任何模板、override 或 hook 均不能削弱此规则。

## 调用方式

- Codex 官方显式调用：`$sdd <功能描述>`。
- 也可运行 `/skills` 后选择“SDD 中文流程”。
- Codex 当前不支持由 Skill 注册独立 `/sdd` 命令；不要声称该斜杠命令已经注册。
