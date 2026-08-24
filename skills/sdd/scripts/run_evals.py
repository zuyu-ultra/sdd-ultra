#!/usr/bin/env python3
"""准备中文 SDD 行为评测沙箱，并对结果执行确定性断言。

本运行器**不**替代 LLM 判分。它只做两件机器能确定的事：

1. `prepare`：从固定 fixture 建立隔离沙箱，完成官方初始化与中文叠加，打印待执行的 prompt。
2. `check`：对沙箱的最终状态执行 `assertions` 中的确定性断言——文件在不在、
   规格里有没有必需标识、fixture 源码有没有被越权改动、本地模式有没有偷偷建 Git 仓库。

`expectations` 中需要判断“推理过程是否正确”的条目属于判分范围，由 `brief` 单独输出，
绝不在这里伪装成通过。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True

SKILL_ROOT = Path(__file__).resolve().parent.parent
EVALS_PATH = SKILL_ROOT / "evals/evals.json"
FIXTURES_ROOT = SKILL_ROOT / "evals/fixtures"

# 断言键 -> 说明。未知键一律报错，避免 evals.json 里写错键却静默跳过。
ASSERTION_KEYS = {
    "no_git_repo": "本地零 Git 模式下沙箱内不得出现 .git",
    "feature_files_present": "需求目录中必须存在这些文件",
    "feature_files_absent": "需求目录中不得存在这些文件",
    "spec_matches": "spec.md 必须匹配这些正则",
    "spec_not_matches": "spec.md 不得匹配这些正则",
    "plan_matches": "plan.md 必须匹配这些正则",
    "discovery_matches": "discovery.md 必须匹配这些正则",
    "fixture_sources_unchanged": "fixture 自带的源码/测试必须逐字节未被修改",
}


def load_evals() -> dict[int, dict]:
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return {int(entry["id"]): entry for entry in payload["evals"]}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fixture_digests(fixture: Path) -> dict[str, str]:
    return {
        path.relative_to(fixture).as_posix(): digest(path)
        for path in sorted(fixture.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command, cwd=SKILL_ROOT, env=env, capture_output=True,
        text=True, check=False, timeout=600,
    )


def resolve_feature_dir(sandbox: Path) -> Path | None:
    """按 Skill 的定位规则解析需求目录：先看活动指针，再回落到 specs/。"""
    pointer = sandbox / ".specify/feature.json"
    if pointer.is_file() and not pointer.is_symlink():
        try:
            data = json.loads(pointer.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            data = {}
        for key in ("feature_dir", "FEATURE_DIR", "path"):
            raw = data.get(key)
            if isinstance(raw, str) and raw:
                candidate = Path(raw)
                if not candidate.is_absolute():
                    candidate = sandbox / candidate
                if candidate.is_dir():
                    return candidate
    specs = sandbox / "specs"
    if specs.is_dir():
        children = sorted(child for child in specs.iterdir() if child.is_dir())
        if len(children) == 1:
            return children[0]
        if children:
            return None  # 多个候选时不猜，交由断言报告为失败
    return None


def cmd_list(args: argparse.Namespace) -> int:
    evals = load_evals()
    for eval_id in sorted(evals):
        entry = evals[eval_id]
        fixture = (entry.get("sandbox") or {}).get("fixture", "—")
        checkable = len(entry.get("assertions") or {})
        judged = len(entry.get("expectations") or [])
        print(f"{eval_id:>3}  fixture={fixture:<26} 确定性断言={checkable:<2} 判分项={judged}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    entry = load_evals().get(args.id)
    if entry is None:
        print(f"未知 eval id: {args.id}", file=sys.stderr)
        return 2
    print(f"# Eval {entry['id']}\n")
    print("## Prompt\n")
    print(entry["prompt"] + "\n")
    print("## 期望产出\n")
    print(entry["expected_output"] + "\n")
    print("## 需要判分的行为项（本运行器无法验证）\n")
    for index, item in enumerate(entry.get("expectations") or [], start=1):
        print(f"{index}. {item}")
    assertions = entry.get("assertions") or {}
    print("\n## 可由 `check` 确定性验证的项\n")
    if not assertions:
        print("（无）")
    for key, value in assertions.items():
        print(f"- {ASSERTION_KEYS.get(key, key)}：{value!r}")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    entry = load_evals().get(args.id)
    if entry is None:
        print(f"未知 eval id: {args.id}", file=sys.stderr)
        return 2
    fixture_name = (entry.get("sandbox") or {}).get("fixture")
    if not fixture_name:
        print(f"eval {args.id} 没有声明 fixture，无法准备沙箱", file=sys.stderr)
        return 2
    fixture = FIXTURES_ROOT / fixture_name
    if not fixture.is_dir():
        print(f"fixture 不存在: {fixture}", file=sys.stderr)
        return 2

    sandbox = Path(args.sandbox).expanduser().resolve()
    if sandbox.exists():
        if any(sandbox.iterdir()) and not args.force:
            print(f"沙箱非空，加 --force 覆盖: {sandbox}", file=sys.stderr)
            return 2
        shutil.rmtree(sandbox)
    shutil.copytree(fixture, sandbox)

    baseline = sandbox / ".sdd-eval-baseline.json"
    baseline.write_text(
        json.dumps(
            {"eval_id": entry["id"], "fixture": fixture_name,
             "digests": fixture_digests(fixture)},
            ensure_ascii=False, indent=2, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    if not args.skip_init:
        # fixture 目录非空，`init --here` 需要 --force 跳过上游的"目录非空"确认。
        # 按 Skill 自身规则，先证明没有任何同名 SDD 托管路径存在，再请求 destructive 授权；
        # fixture 一旦带上这些路径，就是真实冲突，必须由人工处理而不是自动覆盖。
        conflicts = [
            relative for relative in (".specify", ".agents", "specs", "AGENTS.md")
            if (sandbox / relative).exists()
        ]
        if conflicts:
            print(f"fixture 含有 SDD 托管路径，拒绝自动覆盖: {conflicts}", file=sys.stderr)
            return 2
        init = run([
            sys.executable, "-B", str(SKILL_ROOT / "scripts/specify_runtime.py"),
            "run", "--target", str(sandbox), "--allow-project-write",
            "--allow-destructive", "--",
            "init", "--here", "--integration", "codex",
            "--integration-options=--skills", "--script", "py",
            "--ignore-agent-tools", "--force",
        ])
        if init.returncode != 0:
            print(f"官方初始化失败:\n{init.stdout}{init.stderr}", file=sys.stderr)
            return 1
        overlay = run([
            sys.executable, "-B", str(SKILL_ROOT / "scripts/install_project.py"),
            "--target", str(sandbox),
        ])
        if overlay.returncode != 0:
            print(f"中文叠加失败:\n{overlay.stdout}{overlay.stderr}", file=sys.stderr)
            return 1

    print(json.dumps({
        "status": "prepared", "eval_id": entry["id"], "fixture": fixture_name,
        "sandbox": str(sandbox), "initialized": not args.skip_init,
    }, ensure_ascii=False, indent=2))
    print("\n──── 在该沙箱中执行以下 prompt ────\n")
    print(entry["prompt"])
    print(f"\n──── 完成后运行 ────\n")
    print(f"python3 {SKILL_ROOT / 'scripts/run_evals.py'} check --id {entry['id']} "
          f"--sandbox {sandbox}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    entry = load_evals().get(args.id)
    if entry is None:
        print(f"未知 eval id: {args.id}", file=sys.stderr)
        return 2
    sandbox = Path(args.sandbox).expanduser().resolve()
    if not sandbox.is_dir():
        print(f"沙箱不存在: {sandbox}", file=sys.stderr)
        return 2

    assertions = entry.get("assertions") or {}
    unknown = set(assertions) - set(ASSERTION_KEYS)
    if unknown:
        print(f"evals.json 中存在未知断言键: {sorted(unknown)}", file=sys.stderr)
        return 2

    failures: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)

    feature_dir = resolve_feature_dir(sandbox)
    needs_feature = any(
        key in assertions for key in
        ("feature_files_present", "feature_files_absent", "spec_matches",
         "spec_not_matches", "plan_matches", "discovery_matches")
    )
    if needs_feature and feature_dir is None:
        failures.append("无法唯一解析需求目录：缺少 .specify/feature.json 指针，或 specs/ 下有多个候选")

    if assertions.get("no_git_repo"):
        check(not (sandbox / ".git").exists(),
              "本地零 Git 模式被违反：沙箱内出现了 .git")

    if feature_dir is not None:
        for name in assertions.get("feature_files_present", []):
            check((feature_dir / name).is_file(), f"缺少必需产物: {name}")
        for name in assertions.get("feature_files_absent", []):
            check(not (feature_dir / name).exists(),
                  f"生成了本阶段不应存在的产物: {name}")

        for artifact, key_yes, key_no in (
            ("spec.md", "spec_matches", "spec_not_matches"),
            ("plan.md", "plan_matches", None),
            ("discovery.md", "discovery_matches", None),
        ):
            patterns = assertions.get(key_yes, [])
            negatives = assertions.get(key_no, []) if key_no else []
            if not patterns and not negatives:
                continue
            path = feature_dir / artifact
            if not path.is_file():
                failures.append(f"{artifact} 不存在，无法执行内容断言")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in patterns:
                check(re.search(pattern, text) is not None,
                      f"{artifact} 未匹配必需模式: {pattern}")
            for pattern in negatives:
                check(re.search(pattern, text) is None,
                      f"{artifact} 匹配了禁止模式: {pattern}")

    if assertions.get("fixture_sources_unchanged"):
        baseline_path = sandbox / ".sdd-eval-baseline.json"
        if not baseline_path.is_file():
            failures.append("缺少 .sdd-eval-baseline.json，无法验证 fixture 源码未被改动；"
                            "请用 prepare 建立沙箱")
        else:
            recorded = json.loads(baseline_path.read_text(encoding="utf-8"))["digests"]
            for relative, expected in sorted(recorded.items()):
                target = sandbox / relative
                if not target.is_file():
                    check(False, f"fixture 文件被删除: {relative}")
                else:
                    check(digest(target) == expected,
                          f"fixture 源码被越权修改: {relative}")

    result = {
        "eval_id": entry["id"],
        "sandbox": str(sandbox),
        "feature_dir": str(feature_dir) if feature_dir else None,
        "status": "passed" if not failures else "failed",
        "deterministic_checks": checks,
        "failures": failures,
        "judged_separately": entry.get("expectations") or [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出全部评测及其可确定性验证的断言数")

    brief = sub.add_parser("brief", help="输出单条评测的 prompt、期望与判分项")
    brief.add_argument("--id", type=int, required=True)

    prepare = sub.add_parser("prepare", help="从 fixture 建立隔离沙箱并完成初始化")
    prepare.add_argument("--id", type=int, required=True)
    prepare.add_argument("--sandbox", required=True)
    prepare.add_argument("--force", action="store_true", help="覆盖非空沙箱")
    prepare.add_argument("--skip-init", action="store_true",
                         help="只复制 fixture，不运行官方初始化与中文叠加")

    check = sub.add_parser("check", help="对沙箱最终状态执行确定性断言")
    check.add_argument("--id", type=int, required=True)
    check.add_argument("--sandbox", required=True)

    args = parser.parse_args()
    handlers = {"list": cmd_list, "brief": cmd_brief,
                "prepare": cmd_prepare, "check": cmd_check}
    try:
        return handlers[args.command](args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
