# Catalog、认证、下载安全与离线策略

## 默认离线

固定 runtime、核心 `init`、38 个 built-in integration 的包内逻辑、10 个核心 commands、三类 helper、4 个 bundled extension、2 个 bundled preset 和 `speckit` workflow 都随 Skill vendoring。默认先从本地 wheelhouse 建 runtime，不因命令失败而静默联网。

Catalog 的 bundled snapshot 和已安装组件可离线读取；远端独有项应报告 `unavailable_offline`/无法验证，而不是暗中下载。

## 网络命令

`search`、远端 `info`、catalog add/fetch、URL/package add/update、`self check/upgrade` 等需先 `classify`，用户请求涵盖网络时才给网关 `--allow-network`。涉及 extension/preset/workflow/bundle/custom step 的下载后执行，还需 `--allow-code-execution`。

只接受 HTTPS；loopback HTTP 仅限用户明确的本地开发。重定向后重新核对 scheme、host 和授权范围。拒绝 `file:`、非 loopback 明文 HTTP、localhost SSRF 到任意本机服务、路径穿越、symlink archive entry、zip bomb 和超限响应。

## Catalog 不等于信任

- official/bundled 表示随固定快照交付，可由 manifest 校验。
- `verified` 是 catalog 元数据，不等于本 Skill 做过全面代码审计。
- community 与自定义 catalog 默认视为第三方内容。
- `install_allowed` 只是目录政策。

安装前核对 ID、author、repository、license、version、artifact URL、digest/signature（若提供）、manifest、hooks、scripts、workflow shell 和预计写路径。Catalog 未提供 hash 时明确标记 `unverified`。

## 认证

官方 CLI 的认证是 opt-in：只有用户创建 `~/.specify/auth.json` 才会按 host 发送凭据。Provider 支持 GitHub/GHES bearer、Azure DevOps PAT/basic、Azure CLI 和 Azure AD 等，精确字段以 `vendor/spec-kit/docs/reference/authentication.md` 为准。

安全规则：

- 只有用户授权精确 provider、host 和动作时才使用 `--allow-credentials`。
- 网关默认剥离 `GH_TOKEN`、`GITHUB_TOKEN`、`AZURE_DEVOPS_PAT`、`AZURE_CLIENT_SECRET` 等常见环境凭据。
- `auth.json` 应为用户私有文件并使用 `0600`；token 建议引用环境或安全文件，不写入项目、argv、日志、plan 或回答。
- Host pattern 必须最小化；重定向跨 host 时移除 Authorization 并重新匹配。
- 认证失败不要打印 token 或完整 header；也不要把匿名 fallback 误报为已认证成功。

注意：固定上游会自行读取用户已有的 `~/.specify/auth.json`。当用户要求“绝不使用任何已配置凭据”时，不执行联网命令，或在隔离 HOME 的临时进程环境中运行并明确这会屏蔽 user-scope catalogs。

## 路径与写入

- 项目 target 必须是明确、已存在、非根目录、非 HOME、非 symlink 的目录。
- 中文叠加层逐组件拒绝 symlink/dangling link，使用同目录临时文件、fsync 和 `os.replace`。
- 官方 integration manifests 会跟踪 SHA-256 并保留 modified files；仍需在运行前检查 `.specify` 和目标 agent 根的 symlink/containment。
- `--force`、remove/uninstall/switch/update-all 都必须先展示精确目标与恢复策略。
- workflow shell、event、custom step、extension script 没有沙箱；批准只表示用户知情，不代表安全。

## Runtime 完整性

```bash
python3 <skill-dir>/scripts/build_vendored_manifest.py
python3 <skill-dir>/scripts/specify_runtime.py status
python3 <skill-dir>/scripts/generate_capability_manifest.py --check
```

任一 source/wheel hash、commit、version 或 CLI schema 漂移都 fail closed。不要回退到 PATH `specify`，也不要让 `self upgrade` 修改固定 runtime。
