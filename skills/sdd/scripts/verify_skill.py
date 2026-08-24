#!/usr/bin/env python3
"""对 Spec Kit 中文全能力 Skill 执行可重复的静态与运行时验收。"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True

SKILL_ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = SKILL_ROOT / "vendor/spec-kit"
PROJECT_ASSETS = SKILL_ROOT / "assets/project"
STAGES_ROOT = PROJECT_ASSETS / ".agents/skills"
LOCK_PATH = SKILL_ROOT / "vendor/upstream-lock.json"
CAPABILITY_PATH = SKILL_ROOT / "references/capability-map.json"
EXPECTED_COMMIT = "83883a2ebad7e7de667fd00381b100d597faf846"
EXPECTED_VERSION = "0.16.4.dev0"
EXPECTED_INTEGRATIONS = {
    "agy", "alquimia", "amp", "auggie", "bob", "claude", "cline",
    "codebuddy", "codex", "command-code", "copilot", "cursor-agent",
    "devin", "droid", "firebender", "forge", "gemini", "generic",
    "goose", "grok", "hermes", "junie", "kilocode", "kimi", "kiro-cli",
    "lingma", "omp", "opencode", "pi", "qodercli", "qwen", "rovodev",
    "shai", "tabnine", "trae", "vibe", "zcode", "zed",
}
EXPECTED_STAGES = {
    "speckit-analyze", "speckit-checklist", "speckit-clarify",
    "speckit-constitution", "speckit-converge", "speckit-implement",
    "speckit-plan", "speckit-specify", "speckit-tasks",
    "speckit-taskstoissues",
}
TEMPLATE_COMMANDS = {
    "checklist-template.md": {
        "__SPECKIT_COMMAND_CHECKLIST__": "$speckit-checklist",
        "__SPECKIT_COMMAND_CLARIFY__": "$speckit-clarify",
        "__SPECKIT_COMMAND_IMPLEMENT__": "$speckit-implement",
        "__SPECKIT_COMMAND_SPECIFY__": "$speckit-specify",
    },
    "constitution-template.md": {},
    "plan-template.md": {
        "__SPECKIT_COMMAND_PLAN__": "$speckit-plan",
        "__SPECKIT_COMMAND_TASKS__": "$speckit-tasks",
    },
    "spec-template.md": {},
    "tasks-template.md": {
        "__SPECKIT_COMMAND_TASKS__": "$speckit-tasks",
    },
}
STAGE_ORIGINS = {
    "speckit-analyze": "analyze.md",
    "speckit-checklist": "checklist.md",
    "speckit-clarify": "clarify.md",
    "speckit-constitution": "constitution.md",
    "speckit-converge": "converge.md",
    "speckit-implement": "implement.md",
    "speckit-plan": "plan.md",
    "speckit-specify": "specify.md",
    "speckit-tasks": "tasks.md",
    "speckit-taskstoissues": "taskstoissues.md",
}
REQUIRED_STAGE_MARKERS = {
    "speckit-analyze": ["50", "CRITICAL", "只读", "constitution", "tasks.md"],
    "speckit-checklist": ["80%", "40", "5", "需求", "checklist"],
    "speckit-clarify": ["5", "FEATURE_SPEC", "检查表", "EXECUTE_COMMAND:", "discovery.md"],
    "speckit-constitution": ["constitution", "版本", "Sync Impact Report", "EXECUTE_COMMAND:"],
    "speckit-converge": ["append-only", "T", "tasks.md", "gap", "逐字节"],
    "speckit-implement": ["checklist", "tasks.md", "EXECUTE_COMMAND:", "gitignore", "批准任务"],
    "speckit-plan": ["research.md", "data-model.md", "contracts", "quickstart.md", "批准规格", "批准计划", "技术分歧点"],
    "speckit-specify": ["spec.md", "成功标准", "检查表", "EXECUTE_COMMAND:", "task-management.json", "批准规格", "需求成熟度评估", "discovery.md"],
    "speckit-tasks": ["[P]", "[US", "T", "tasks.md", "EXECUTE_COMMAND:", "批准计划", "批准任务"],
    "speckit-taskstoissues": ["remote.origin.url", "GitHub", "MCP", "GitLab", "glab", "批准任务"],
}
EXPECTED_FIXTURES = {
    "date-range-project", "hidden-caller-project", "phone-project",
    "red-herring-project", "renamed-duplicate-project",
}
EXPECTED_REFERENCES = {
    "brownfield-compatibility.md", "bundles.md", "capability-map.json", "cli-core.md", "customization.md",
    "extensions.md", "integrations.md", "presets.md", "sdd-strategies.md",
    "security-offline.md", "upstream-development.md", "upstream.md",
    "workflows.md",
}
RISK_KINDS = {
    "network", "project-write", "code-execution", "runtime-write", "destructive"
}
BROWNFIELD_STAGE_MARKERS = {
    "speckit-analyze": ["PB-###", "NM-###", "RC-###", "根因关卡不可协商", "回归", "现有符号"],
    "speckit-checklist": ["PB-###", "NM-###", "RC-###", "检测缺口", "compatibility.md", "存量"],
    "speckit-clarify": ["PB-###", "RC-###", "兼容边界", "根因调查"],
    "speckit-constitution": ["PB-###", "NM-###", "存量兼容"],
    "speckit-converge": ["PB-###", "NM-###", "RC-###", "根因", "regression", "旧任务批准已失效"],
    "speckit-implement": ["PB-###", "NM-###", "RC-###", "根因被推翻", "变更前基线", "立即停止"],
    "speckit-plan": ["PB-###", "NM-###", "RC-###", "根因到方案追踪", "现有符号", "变更前基线"],
    "speckit-specify": ["PB-###", "RC-###", "任何 `spec.md` 写入之前", "因果链", "项目证据优先", "相邻不变场景"],
    "speckit-tasks": ["PB-###", "NM-###", "RC-###", "检测缺口", "存量验证不可选", "变更前基线"],
}
CO_CREATION_STAGE_MARKERS = {
    "speckit-analyze": ["DD-###", "discovery.md"],
    "speckit-checklist": ["DD-###", "由 Agent 代选"],
    "speckit-converge": ["DD-###", "决策图"],
    "speckit-implement": ["DD-###", "discovery.md", "立即停止"],
    "speckit-tasks": ["DD-###", "discovery.md"],
    "speckit-clarify": ["DD-###", "取代 DD-00X"],
    "speckit-plan": ["DD-###", "技术分歧点", "可逆性"],
    "speckit-specify": ["DD-###", "成熟度评估", "由 Agent 代选", "延后决策", "推荐"],
}
CO_CREATION_TEMPLATE_MARKERS = {
    "spec-template.md": ["需求共创决策", "DD-001", "由 Agent 代选", "规模档位", "档位依据"],
}
SIZING_STAGE_MARKERS = {
    "speckit-analyze": ["规模档位", "精简模式"],
    "speckit-converge": ["规模档位", "精简模式"],
    "speckit-implement": ["规模档位", "批准变更说明", "升档"],
    "speckit-plan": ["规模档位关卡", "升档"],
    "speckit-specify": ["规模判定", "精简模式", "XS", "升档触发"],
    "speckit-tasks": ["规模档位关卡", "升档"],
}
ROOT_CAUSE_TEMPLATE_MARKERS = {
    "spec-template.md": ["Bug 来龙去脉与根因分析", "BUG-001", "RC-001", "事实时间线", "复现证据", "因果链", "第一个错误", "检测缺口", "证伪方式"],
    "plan-template.md": ["根因到方案追踪", "RC-###", "因果链阻断点", "检测缺口"],
    "tasks-template.md": ["RC-###", "根因被推翻", "检测缺口"],
    "checklist-template.md": ["RC-###", "因果链", "根因置信度", "检测缺口"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, text[end + 5 :]


def formal_tokens(text: str) -> set[str]:
    """提取必须跨本地化保持不变的方括号占位符。"""
    return set(re.findall(r"\[(?:[A-Z][A-Z0-9_ #./:+<>-]*)\]", text))


def heading_profile(text: str) -> dict[int, int]:
    profile: dict[int, int] = {}
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s", line)
        if match:
            level = len(match.group(1))
            profile[level] = profile.get(level, 0) + 1
    return profile


class Audit:
    def __init__(self) -> None:
        self.checks = 0
        self.failures: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)

    def equal(self, actual: object, expected: object, message: str) -> None:
        self.check(actual == expected, f"{message}: expected={expected!r}, actual={actual!r}")


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        merged.update(env)
    return subprocess.run(
        command,
        cwd=SKILL_ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def verify_static(audit: Audit) -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    audit.equal(lock.get("repository"), "https://github.com/github/spec-kit", "upstream repository")
    audit.equal(lock.get("commit"), EXPECTED_COMMIT, "upstream commit")
    audit.equal(lock.get("version"), EXPECTED_VERSION, "upstream version")
    audit.equal(lock.get("license"), "MIT", "upstream license")
    audit.equal(lock.get("vendored_file_count"), 539, "vendored upstream file count lock")
    audit.equal(lock.get("wheel_count"), 28, "offline wheel count lock")
    audit.equal(lock.get("source_manifest_sha256"), sha256(SKILL_ROOT / "vendor/MANIFEST.sha256"), "source manifest digest")
    audit.equal(lock.get("wheelhouse_manifest_sha256"), sha256(SKILL_ROOT / "vendor/WHEELHOUSE.sha256"), "wheelhouse manifest digest")
    audit.equal(lock.get("capability_map_sha256"), sha256(CAPABILITY_PATH), "capability map digest")
    audit.equal(lock.get("license_sha256"), sha256(VENDOR_ROOT / "LICENSE"), "license digest")
    source_manifest = (SKILL_ROOT / "vendor/MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    wheel_manifest = (SKILL_ROOT / "vendor/WHEELHOUSE.sha256").read_text(encoding="utf-8").splitlines()
    audit.equal(len(source_manifest), lock.get("vendored_file_count"), "vendored manifest entry count")
    audit.equal(len(wheel_manifest), lock.get("wheel_count"), "wheelhouse manifest entry count")

    for path in SKILL_ROOT.rglob("*"):
        relative = path.relative_to(SKILL_ROOT)
        audit.check(not path.is_symlink(), f"symlink is forbidden in Skill bundle: {relative}")
        audit.check(path.name != ".DS_Store", f"Finder metadata present: {relative}")
        audit.check(path.name != "__pycache__", f"bytecode cache present: {relative}")
        audit.check(path.suffix != ".pyc", f"compiled bytecode present: {relative}")

    root_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    root_fields, _ = frontmatter(root_text)
    audit.equal(root_fields.get("name"), "sdd", "root skill name")
    audit.check("Spec Kit" in root_fields.get("description", ""), "root description lacks Spec Kit trigger")
    audit.check(len(root_text.splitlines()) < 500, "root SKILL.md must stay below 500 lines")
    audit.check("全部 539 个文件" in root_text, "root SKILL.md must state full repository mirror scope")
    audit.check("模糊需求的共创讨论" in root_text, "root SKILL.md must define the ambiguous-requirement co-creation gate")
    audit.check("需求规模分级" in root_text, "root SKILL.md must define the request size tiers")
    audit.check("永不缩放的红线" in root_text, "root SKILL.md must state which gates never scale down")
    audit.check("升档是单向的" in root_text, "root SKILL.md must make tier escalation one-way")
    audit.check("discovery.md" in root_text, "root SKILL.md must route co-creation decisions to discovery.md")

    refs = {path.name for path in (SKILL_ROOT / "references").glob("*") if path.is_file()}
    audit.check(EXPECTED_REFERENCES <= refs, f"missing references: {sorted(EXPECTED_REFERENCES - refs)}")

    fixtures_root = SKILL_ROOT / "evals/fixtures"
    fixtures = {path.name for path in fixtures_root.iterdir() if path.is_dir()}
    audit.equal(fixtures, EXPECTED_FIXTURES, "behavior eval fixture set")
    for name in sorted(EXPECTED_FIXTURES):
        fixture = fixtures_root / name
        audit.check((fixture / "pyproject.toml").is_file(), f"{name} missing pyproject.toml")
        audit.check(any(fixture.rglob("test_*.py")), f"{name} missing baseline tests")
        audit.check(
            not any(part in {".specify", ".agents", "specs"} for path in fixture.rglob("*") for part in path.parts),
            f"{name} must not carry SDD-managed paths",
        )
    audit.check((SKILL_ROOT / "scripts/run_evals.py").is_file(), "eval harness is missing")
    evals = json.loads((SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8"))["evals"]
    ids = [entry["id"] for entry in evals]
    audit.equal(len(ids), len(set(ids)), "eval ids must be unique")
    audit.check(all(entry.get("expectations") for entry in evals), "every eval needs judged expectations")
    sandboxed = [entry for entry in evals if entry.get("assertions")]
    audit.check(len(sandboxed) >= 8, f"too few deterministically checkable evals: {len(sandboxed)}")
    audit.check(
        all((fixtures_root / entry["sandbox"]["fixture"]).is_dir() for entry in sandboxed),
        "an eval points at a missing fixture",
    )

    stages = {path.parent.name for path in STAGES_ROOT.glob("*/SKILL.md")}
    audit.equal(stages, EXPECTED_STAGES, "Chinese core stage set")
    chinese_total = 0
    upstream_total = 0
    for stage, origin_name in STAGE_ORIGINS.items():
        path = STAGES_ROOT / stage / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        fields, body = frontmatter(text)
        audit.equal(set(fields), {"name", "description"}, f"{stage} frontmatter keys")
        audit.equal(fields.get("name"), stage, f"{stage} frontmatter name")
        audit.check(bool(re.search(r"[\u4e00-\u9fff]", fields.get("description", ""))), f"{stage} description is not Chinese")
        audit.check(text.count("```") % 2 == 0, f"{stage} has unbalanced code fences")
        audit.check("__SPECKIT_COMMAND_" not in text, f"{stage} has unresolved command placeholder")
        for marker in REQUIRED_STAGE_MARKERS[stage]:
            audit.check(marker in body, f"{stage} missing completeness marker {marker!r}")
        for marker in BROWNFIELD_STAGE_MARKERS.get(stage, []):
            audit.check(marker in body, f"{stage} missing brownfield marker {marker!r}")
        for marker in CO_CREATION_STAGE_MARKERS.get(stage, []):
            audit.check(marker in body, f"{stage} missing co-creation marker {marker!r}")
        for marker in SIZING_STAGE_MARKERS.get(stage, []):
            audit.check(marker in body, f"{stage} missing size-tier marker {marker!r}")
        chinese_lines = len(text.splitlines())
        upstream_lines = len((VENDOR_ROOT / "templates/commands" / origin_name).read_text(encoding="utf-8").splitlines())
        chinese_total += chinese_lines
        upstream_total += upstream_lines
        audit.check(chinese_lines >= upstream_lines * 0.80, f"{stage} is unexpectedly compressed ({chinese_lines}/{upstream_lines})")
    audit.check(chinese_total >= upstream_total, f"Chinese stages unexpectedly shorter overall ({chinese_total}/{upstream_total})")

    templates_root = PROJECT_ASSETS / ".specify/templates"
    templates = {path.name for path in templates_root.glob("*-template.md")}
    audit.equal(templates, set(TEMPLATE_COMMANDS), "localized template set")
    localized_template_lines = 0
    upstream_template_lines = 0
    for name, command_map in TEMPLATE_COMMANDS.items():
        localized = (templates_root / name).read_text(encoding="utf-8")
        upstream = (VENDOR_ROOT / "templates" / name).read_text(encoding="utf-8")
        localized_lines = len(localized.splitlines())
        upstream_lines = len(upstream.splitlines())
        localized_template_lines += localized_lines
        upstream_template_lines += upstream_lines
        audit.check(bool(re.search(r"[\u4e00-\u9fff]", localized)), f"{name} is not localized to Chinese")
        audit.check(localized_lines >= upstream_lines * 0.95, f"{name} is unexpectedly compressed ({localized_lines}/{upstream_lines})")
        audit.check(
            formal_tokens(upstream) <= formal_tokens(localized),
            f"{name} lost upstream formal placeholders: upstream={formal_tokens(upstream)!r}, localized={formal_tokens(localized)!r}",
        )
        localized_headings = heading_profile(localized)
        upstream_headings = heading_profile(upstream)
        audit.check(
            all(localized_headings.get(level, 0) >= count for level, count in upstream_headings.items()),
            f"{name} lost upstream heading structure: upstream={upstream_headings!r}, localized={localized_headings!r}",
        )
        audit.equal(localized.count("```"), upstream.count("```"), f"{name} fenced block structure")
        audit.equal(localized.count("<!--"), localized.count("-->"), f"{name} localized comment balance")
        audit.check(localized.count("<!--") >= upstream.count("<!--"), f"{name} lost upstream comment blocks")
        audit.check("__SPECKIT_COMMAND_" not in localized, f"{name} has unresolved command placeholder")
        for original, rendered in command_map.items():
            audit.equal(localized.count(rendered), upstream.count(original), f"{name} rendered command parity for {original}")
        for marker in ROOT_CAUSE_TEMPLATE_MARKERS.get(name, []):
            audit.check(marker in localized, f"{name} missing Bug root-cause marker {marker!r}")
        for marker in CO_CREATION_TEMPLATE_MARKERS.get(name, []):
            audit.check(marker in localized, f"{name} missing co-creation marker {marker!r}")
    audit.check(localized_template_lines >= upstream_template_lines * 0.99, f"localized templates unexpectedly shorter overall ({localized_template_lines}/{upstream_template_lines})")
    scripts = sorted((PROJECT_ASSETS / ".specify/scripts/python").glob("*.py"))
    audit.equal(len(scripts), 6, "localized Python helper count")
    for script in scripts:
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except SyntaxError as exc:
            audit.check(False, f"invalid Python helper {script.name}: {exc}")

    for kind, suffix in (("bash", ".sh"), ("powershell", ".ps1"), ("python", ".py")):
        count = len(list((VENDOR_ROOT / "scripts" / kind).glob(f"*{suffix}")))
        audit.equal(count, 6, f"official {kind} helper count")
    audit.equal(len(list((VENDOR_ROOT / "tests").rglob("test_*.py"))), 142, "vendored upstream test count")
    audit.equal({p.name for p in (VENDOR_ROOT / "extensions").iterdir() if p.is_dir()} >= {"agent-context", "assess", "bug", "git"}, True, "bundled extensions")
    audit.equal({p.name for p in (VENDOR_ROOT / "presets").iterdir() if p.is_dir()} >= {"lean", "constitution-sync"}, True, "bundled presets")
    audit.check((VENDOR_ROOT / "workflows/speckit/workflow.yml").is_file(), "bundled speckit workflow missing")

    capability = json.loads(CAPABILITY_PATH.read_text(encoding="utf-8"))
    audit.equal(capability.get("commit"), EXPECTED_COMMIT, "capability commit")
    audit.equal(capability.get("version"), EXPECTED_VERSION, "capability version")
    audit.equal(capability.get("leaf_command_count"), 84, "CLI leaf command count")
    commands = capability.get("commands", [])
    paths = [item.get("path") for item in commands]
    audit.equal(len(paths), len(set(paths)), "CLI command paths must be unique")
    audit.check(all(set(item.get("risks", [])) <= RISK_KINDS for item in commands), "unknown risk kind in capability map")
    required_paths = {
        "specify init", "specify integration status", "specify extension add",
        "specify preset resolve", "specify workflow resume",
        "specify workflow overlay set-priority", "specify workflow step add",
        "specify bundle validate", "specify self upgrade", "specify event run",
    }
    audit.check(required_paths <= set(paths), f"CLI families incomplete: {sorted(required_paths - set(paths))}")


def verify_runtime(audit: Audit) -> None:
    manifest = run([sys.executable, "-B", str(SKILL_ROOT / "scripts/build_vendored_manifest.py")])
    audit.check(manifest.returncode == 0, f"vendor manifest verification failed: {manifest.stdout}{manifest.stderr}")
    status = run([sys.executable, "-B", str(SKILL_ROOT / "scripts/specify_runtime.py"), "status"])
    audit.check(status.returncode == 0, f"fixed runtime is not ready: {status.stdout}{status.stderr}")
    try:
        payload = json.loads(status.stdout[status.stdout.find("{"):])
    except (json.JSONDecodeError, ValueError) as exc:
        audit.check(False, f"runtime status JSON invalid: {exc}")
        return
    audit.equal(payload.get("version"), EXPECTED_VERSION, "runtime version")
    audit.equal(payload.get("commit"), EXPECTED_COMMIT, "runtime commit")
    runtime = Path(str(payload.get("runtime_dir", "")))
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    parity = run([str(python), "-B", str(SKILL_ROOT / "scripts/generate_capability_manifest.py"), "--check"])
    audit.check(parity.returncode == 0, f"live CLI parity failed: {parity.stdout}{parity.stderr}")
    registry_code = (
        "import json; from specify_cli.integrations import INTEGRATION_REGISTRY; "
        "print(json.dumps(sorted(INTEGRATION_REGISTRY)))"
    )
    registry = run([str(python), "-B", "-c", registry_code])
    try:
        integrations = set(json.loads(registry.stdout))
    except json.JSONDecodeError as exc:
        audit.check(False, f"integration registry output invalid: {exc}: {registry.stdout}{registry.stderr}")
    else:
        audit.equal(integrations, EXPECTED_INTEGRATIONS, "runtime integration registry")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true", help="跳过 fixed runtime 动态对等检查")
    args = parser.parse_args()
    audit = Audit()
    try:
        verify_static(audit)
        if not args.static_only:
            verify_runtime(audit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        audit.check(False, f"unhandled audit error: {exc}")
    result = {
        "status": "passed" if not audit.failures else "failed",
        "checks": audit.checks,
        "failures": audit.failures,
        "version": EXPECTED_VERSION,
        "commit": EXPECTED_COMMIT,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not audit.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
