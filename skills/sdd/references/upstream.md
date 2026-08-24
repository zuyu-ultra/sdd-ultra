# 上游来源与许可证

本 Skill 固定 [github/spec-kit](https://github.com/github/spec-kit) 提交 `83883a2ebad7e7de667fd00381b100d597faf846`、包版本 `0.16.4.dev0`。

- 除 `.git` 对象数据库外原样镜像的全部 539 个上游文件（源码、运行资产、文档、测试、CI、开发容器、媒体和项目元数据）：`vendor/spec-kit/`
- 上游锁：`vendor/upstream-lock.json`
- Source SHA-256：`vendor/MANIFEST.sha256`
- 28 个跨平台 offline wheels 及其 SHA-256：`vendor/WHEELHOUSE.sha256`
- 完整 CLI schema：`references/capability-map.json`
- 更新和开发流程：`references/upstream-development.md`

上游使用 MIT License，原文完整保存在 `vendor/spec-kit/LICENSE`。中文 10 阶段是同一固定 commit 的完整中文重构；官方执行逻辑保持原版，Skill 另加固定 runtime、安全授权和 Codex 项目本地化层。
