#!/usr/bin/env python3
"""中文 Skill 网关、初始化器与安全边界回归测试。"""

from __future__ import annotations

import json
import hashlib
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = SKILL_ROOT / "scripts/specify_runtime.py"
INSTALLER = SKILL_ROOT / "scripts/install_project.py"
VERIFY = SKILL_ROOT / "scripts/verify_skill.py"
PREDECESSOR_MANIFEST = SKILL_ROOT / "manifests/managed-predecessors.json"

REVISION_2_CONSTITUTION_TEMPLATE = """# [PROJECT_NAME] 项目宪章

<!-- 本文件定义项目不可妥协的工程原则。请用明确、可测试的规则替换所有占位符。 -->

## 核心原则

### [PRINCIPLE_1_NAME]

[PRINCIPLE_1_BODY]

### [PRINCIPLE_2_NAME]

[PRINCIPLE_2_BODY]

### [PRINCIPLE_3_NAME]

[PRINCIPLE_3_BODY]

### [PRINCIPLE_4_NAME]

[PRINCIPLE_4_BODY]

### [PRINCIPLE_5_NAME]

[PRINCIPLE_5_BODY]

## [SECTION_2_NAME]

[SECTION_2_CONTENT]

## [SECTION_3_NAME]

[SECTION_3_CONTENT]

## 治理

[GOVERNANCE_RULES]

**版本**：[CONSTITUTION_VERSION] | **批准日期**：[RATIFICATION_DATE] | **最后修订**：[LAST_AMENDED_DATE]
"""


def command(*args: str, cwd: Path | None = None, path: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if path is not None:
        environment["PATH"] = path
    return subprocess.run(
        [sys.executable, "-B", *args],
        cwd=cwd or SKILL_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def json_output(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"JSON not found in output: {result.stdout}\n{result.stderr}")
    return json.loads(result.stdout[start:])


class SkillBundleTests(unittest.TestCase):
    def test_static_and_runtime_parity_verifier(self) -> None:
        result = command(str(VERIFY))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json_output(result)
        self.assertEqual(payload["status"], "passed")
        self.assertGreaterEqual(payload["checks"], 2900)

    def test_human_gates_and_task_backend_are_managed_assets(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        specify = (SKILL_ROOT / "assets/project/.agents/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
        plan = (SKILL_ROOT / "assets/project/.agents/skills/speckit-plan/SKILL.md").read_text(encoding="utf-8")
        tasks = (SKILL_ROOT / "assets/project/.agents/skills/speckit-tasks/SKILL.md").read_text(encoding="utf-8")
        implement = (SKILL_ROOT / "assets/project/.agents/skills/speckit-implement/SKILL.md").read_text(encoding="utf-8")
        issues = (SKILL_ROOT / "assets/project/.agents/skills/speckit-taskstoissues/SKILL.md").read_text(encoding="utf-8")
        workflow = (SKILL_ROOT / "assets/project/.specify/workflows/speckit/workflow.yml").read_text(encoding="utf-8")

        self.assertIn("本地 `tasks.md` 管理，还是同步到 GitLab Issues", root_skill)
        self.assertIn("task-management.json", specify)
        self.assertIn("批准规格", specify)
        self.assertIn("批准规格", plan)
        self.assertIn("批准计划", plan)
        self.assertIn("批准计划", tasks)
        self.assertIn("批准任务", tasks)
        self.assertIn("批准任务", implement)
        self.assertIn("glab issue list", issues)
        self.assertIn("glab issue create", issues)
        self.assertIn("task_backend", workflow)
        self.assertIn("review-tasks", workflow)
        self.assertIn("inputs.task_backend == 'gitlab'", workflow)

    def test_brownfield_policy_is_routed_to_all_mutating_stages(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        shortcut = (SKILL_ROOT.parent / "sdd/SKILL.md").read_text(encoding="utf-8")
        reference = (SKILL_ROOT / "references/brownfield-compatibility.md").read_text(encoding="utf-8")
        self.assertIn("红线 1", root_skill)
        self.assertIn("红线 2", root_skill)
        self.assertIn("NM-###", root_skill)
        self.assertIn("模板、replace override", root_skill)
        self.assertIn("NM-###", shortcut)
        self.assertIn("直接调用现有实现", reference)

        required = {
            "speckit-specify": ("PB-###", "项目证据优先"),
            "speckit-clarify": ("PB-###", "兼容边界"),
            "speckit-plan": ("PB-###", "NM-###", "变更前基线"),
            "speckit-tasks": ("PB-###", "NM-###", "存量验证不可选"),
            "speckit-analyze": ("PB-###", "NM-###", "CRITICAL"),
            "speckit-implement": ("PB-###", "NM-###", "变更前基线"),
            "speckit-converge": ("PB-###", "NM-###", "regression"),
        }
        for stage, markers in required.items():
            content = (SKILL_ROOT / f"assets/project/.agents/skills/{stage}/SKILL.md").read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, content, f"{stage} lacks {marker}")

    def test_templates_preserve_brownfield_contract(self) -> None:
        templates = SKILL_ROOT / "assets/project/.specify/templates"
        spec = (templates / "spec-template.md").read_text(encoding="utf-8")
        plan = (templates / "plan-template.md").read_text(encoding="utf-8")
        tasks = (templates / "tasks-template.md").read_text(encoding="utf-8")
        constitution = (templates / "constitution-template.md").read_text(encoding="utf-8")

        for marker in ("存量行为与兼容性", "PB-###", "本次不会改变"):
            self.assertIn(marker, spec)
        for marker in ("现有实现与项目惯例", "复用决策", "NM-###", "回归验证矩阵", "变更前基线"):
            self.assertIn(marker, plan)
        for marker in ("存量基线与复用确认", "PB-###", "NM-###", "Bug 修复", "项目标准 lint/typecheck/build/test"):
            self.assertIn(marker, tasks)
        self.assertNotIn("测试是可选的", tasks)
        self.assertNotIn("每项功能都从独立库开始", constitution)

    def test_new_symbols_and_regressions_are_hard_gates(self) -> None:
        tasks = (SKILL_ROOT / "assets/project/.agents/skills/speckit-tasks/SKILL.md").read_text(encoding="utf-8")
        implement = (SKILL_ROOT / "assets/project/.agents/skills/speckit-implement/SKILL.md").read_text(encoding="utf-8")
        analyze = (SKILL_ROOT / "assets/project/.agents/skills/speckit-analyze/SKILL.md").read_text(encoding="utf-8")
        converge = (SKILL_ROOT / "assets/project/.agents/skills/speckit-converge/SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("测试是可选的", tasks)
        self.assertNotIn("Models → Services → Endpoints", tasks)
        self.assertIn("原 plan/tasks 批准失效", implement)
        self.assertIn("未经批准的新符号", implement)
        self.assertIn("不得出现基线之外的新失败", implement)
        self.assertIn("Bug 修复先运行复现测试", implement)
        self.assertIn("始终为 CRITICAL", analyze)
        self.assertIn("旧任务批准已失效", converge)

    def test_workflow_analyzes_reuse_and_regression_before_task_approval(self) -> None:
        workflow = (SKILL_ROOT / "assets/project/.specify/workflows/speckit/workflow.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("- id: tasks"), workflow.index("- id: analyze"))
        self.assertLess(workflow.index("- id: analyze"), workflow.index("- id: review-tasks"))
        self.assertLess(workflow.index("- id: review-tasks"), workflow.index("- id: implement"))
        self.assertIn("PB-###", workflow)
        self.assertIn("NM-###", workflow)

    def test_local_backend_is_explicitly_git_command_free(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cli_core = (SKILL_ROOT / "references/cli-core.md").read_text(encoding="utf-8")
        specify = (SKILL_ROOT / "assets/project/.agents/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
        implement = (SKILL_ROOT / "assets/project/.agents/skills/speckit-implement/SKILL.md").read_text(encoding="utf-8")

        self.assertIn('{"backend":"local","vcs":"none"}', root_skill)
        self.assertIn("严格零 Git 命令模式", root_skill)
        self.assertIn("`--force` 也不是 Git", root_skill)
        self.assertIn("非空不等于冲突", cli_core)
        self.assertIn("本地模式必须完全跳过本步骤", specify)
        self.assertIn("不得运行上面的命令", implement)
        self.assertIn("local 模式强制 vcs=none", (SKILL_ROOT / "assets/project/.specify/workflows/speckit/workflow.yml").read_text(encoding="utf-8"))
        for stage in (SKILL_ROOT / "assets/project/.agents/skills").glob("speckit-*/SKILL.md"):
            content = stage.read_text(encoding="utf-8")
            if stage.parent.name == "speckit-taskstoissues":
                self.assertIn("本地后端禁止外部同步", content)
            else:
                self.assertIn("本地零 Git 命令策略", content)

    def test_full_official_init_then_chinese_overlay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-e2e-") as temp:
            project = Path(temp)
            initialized = command(
                str(RUNTIME), "run", "--target", str(project),
                "--allow-project-write", "--", "init", "--here",
                "--integration", "codex", "--integration-options=--skills",
                "--script", "py", "--ignore-agent-tools",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)

            localized = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(localized.returncode, 0, localized.stdout + localized.stderr)
            self.assertEqual(json_output(localized)["status"], "ready")

            checked = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(json_output(checked)["status"], "ready")

            status = command(str(RUNTIME), "run", "--target", str(project), "--", "integration", "status", "--json")
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            integration = json_output(status)
            self.assertEqual(integration["status"], "ok")
            self.assertEqual(integration["modified_managed_files"], 0)
            self.assertEqual(len(list((project / ".agents/skills").glob("speckit-*/SKILL.md"))), 10)
            constitution_skill = (project / ".agents/skills/speckit-constitution/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("项目宪章", constitution_skill)

    @unittest.skipIf(os.name == "nt", "fake executable fixture is POSIX-specific")
    def test_nonempty_force_init_does_not_invoke_git(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-no-git-") as temp:
            project = Path(temp)
            (project / "existing-project-file.txt").write_text("keep\n", encoding="utf-8")
            fake_bin = project / "fake-bin"
            fake_bin.mkdir()
            canary = project / "git-was-invoked"
            fake_git = fake_bin / "git"
            fake_git.write_text(
                f"#!/bin/sh\ntouch '{canary}'\nexit 97\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)

            initialized = command(
                str(RUNTIME), "run", "--target", str(project),
                "--allow-project-write", "--allow-destructive", "--",
                "init", "--here", "--force", "--integration", "codex",
                "--integration-options=--skills", "--script", "py",
                "--ignore-agent-tools", path=str(fake_bin),
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
            self.assertFalse(canary.exists(), "official init invoked git in local-safe configuration")
            self.assertEqual(
                (project / "existing-project-file.txt").read_text(encoding="utf-8"),
                "keep\n",
            )

    def test_idempotence_drift_metadata_and_force(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-drift-") as temp:
            project = Path(temp)
            first = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertFalse(json_output(second)["updated"])

            managed = project / ".agents/skills/speckit-plan/SKILL.md"
            managed.write_text(managed.read_text(encoding="utf-8") + "\n用户改动\n", encoding="utf-8")
            drift = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(drift.returncode, 1)
            self.assertIn(".agents/skills/speckit-plan/SKILL.md", json_output(drift)["modified"])

            preserved = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(preserved.returncode, 1)
            self.assertIn("用户改动", managed.read_text(encoding="utf-8"))

            forced = command(str(INSTALLER), "--target", str(project), "--force")
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertNotIn("用户改动", managed.read_text(encoding="utf-8"))

            metadata = project / ".specify/spec-kit-sdd-locale.json"
            metadata.write_text('{"language":"en"}\n', encoding="utf-8")
            bad_meta = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(bad_meta.returncode, 1)
            self.assertIn(".specify/spec-kit-sdd-locale.json", json_output(bad_meta)["invalid_metadata"])
            repaired = command(str(INSTALLER), "--target", str(project), "--force")
            self.assertEqual(repaired.returncode, 0, repaired.stdout + repaired.stderr)

    def test_skill_owned_predecessor_manifest_integrity(self) -> None:
        loader = runpy.run_path(str(INSTALLER))["load_managed_predecessors"]
        loaded = loader(PREDECESSOR_MANIFEST)

        expected_paths = {
            path.relative_to(SKILL_ROOT / "assets/project").as_posix()
            for path in (SKILL_ROOT / "assets/project").rglob("*")
            if path.is_file()
            and path.relative_to(SKILL_ROOT / "assets/project").as_posix()
            != ".specify/memory/constitution.md"
        }
        self.assertEqual(set(loaded["official_init"]), expected_paths)
        self.assertEqual(set(loaded["bundle_revisions"]), {2})
        self.assertEqual(set(loaded["bundle_revisions"][2]), expected_paths)
        self.assertEqual(
            hashlib.sha256(REVISION_2_CONSTITUTION_TEMPLATE.encode("utf-8")).hexdigest(),
            loaded["bundle_revisions"][2][
                ".specify/templates/constitution-template.md"
            ],
        )

        original = json.loads(PREDECESSOR_MANIFEST.read_text(encoding="utf-8"))

        def assert_rejected(name: str, mutate: object) -> None:
            candidate = json.loads(json.dumps(original))
            mutate(candidate)
            candidate_path = Path(temp) / f"{name}.json"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError, msg=name):
                loader(candidate_path)

        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-manifest-") as temp:
            assert_rejected(
                "repository",
                lambda candidate: candidate.__setitem__("repository", "https://example.invalid/spec-kit"),
            )
            assert_rejected(
                "version",
                lambda candidate: candidate.__setitem__("upstream_version", "0.0.0"),
            )
            assert_rejected(
                "commit",
                lambda candidate: candidate.__setitem__("upstream_commit", "0" * 40),
            )

            def unsafe_path(candidate: dict[str, object]) -> None:
                hashes = candidate["official_init"]
                value = hashes.pop(".specify/.gitignore")
                hashes["../escape"] = value

            assert_rejected("unsafe-path", unsafe_path)
            assert_rejected(
                "invalid-hash",
                lambda candidate: candidate["bundle_revisions"]["2"].__setitem__(
                    ".specify/.gitignore", "0" * 63
                ),
            )
            assert_rejected(
                "incomplete",
                lambda candidate: candidate["bundle_revisions"]["2"].pop(
                    ".specify/.gitignore"
                ),
            )

    def test_fixed_predecessor_hash_upgrades_without_force(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-fixed-upgrade-") as temp:
            project = Path(temp)
            first = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            locale_path = project / ".specify/spec-kit-sdd-locale.json"
            locale = json.loads(locale_path.read_text(encoding="utf-8"))
            locale["bundle_revision"] = 2
            locale_path.write_text(
                json.dumps(locale, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            managed = project / ".specify/templates/constitution-template.md"
            managed.write_text(REVISION_2_CONSTITUTION_TEMPLATE, encoding="utf-8")

            upgraded = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(upgraded.returncode, 0, upgraded.stdout + upgraded.stderr)
            payload = json_output(upgraded)
            self.assertEqual(payload["status"], "ready")
            self.assertIn(".specify/spec-kit-sdd-locale.json", payload["updated"])
            self.assertIn(".specify/templates/constitution-template.md", payload["updated"])
            self.assertEqual(
                managed.read_bytes(),
                (
                    SKILL_ROOT
                    / "assets/project/.specify/templates/constitution-template.md"
                ).read_bytes(),
            )
            self.assertEqual(
                json.loads(locale_path.read_text(encoding="utf-8"))["bundle_revision"],
                4,
            )
            checked = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(json_output(checked)["status"], "ready")

    def test_project_manifest_cannot_authorize_unknown_revision_asset(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-forged-manifest-") as temp:
            project = Path(temp)
            first = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            locale_path = project / ".specify/spec-kit-sdd-locale.json"
            locale = json.loads(locale_path.read_text(encoding="utf-8"))
            locale["bundle_revision"] = 3
            locale_path.write_text(
                json.dumps(locale, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            managed = project / ".agents/skills/speckit-plan/SKILL.md"
            custom_managed = "unknown revision or user-modified plan asset\n"
            managed.write_text(custom_managed, encoding="utf-8")
            manifest = project / ".specify/integrations/codex.manifest.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                json.dumps(
                    {
                        "version": "0.16.4.dev0",
                        "files": {
                            ".agents/skills/speckit-plan/SKILL.md": hashlib.sha256(
                                custom_managed.encode("utf-8")
                            ).hexdigest()
                        },
                    }
                ),
                encoding="utf-8",
            )

            refused = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(refused.returncode, 1, refused.stdout + refused.stderr)
            payload = json_output(refused)
            self.assertEqual(payload["status"], "attention_required")
            self.assertEqual(managed.read_text(encoding="utf-8"), custom_managed)
            self.assertEqual(
                json.loads(locale_path.read_text(encoding="utf-8"))["bundle_revision"],
                3,
            )
            self.assertIn(".agents/skills/speckit-plan/SKILL.md", payload["preserved"])
            self.assertIn(".specify/spec-kit-sdd-locale.json", payload["preserved"])
            self.assertNotIn(".agents/skills/speckit-plan/SKILL.md", payload["updated"])

    def test_single_byte_predecessor_change_is_preserved_without_revision_bump(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-byte-drift-") as temp:
            project = Path(temp)
            first = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            locale_path = project / ".specify/spec-kit-sdd-locale.json"
            locale = json.loads(locale_path.read_text(encoding="utf-8"))
            locale["bundle_revision"] = 2
            locale_path.write_text(
                json.dumps(locale, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            managed = project / ".specify/templates/constitution-template.md"
            changed = REVISION_2_CONSTITUTION_TEMPLATE.replace("PROJECT_NAME", "PROJECT_NAMF", 1)
            self.assertEqual(
                len(changed.encode("utf-8")),
                len(REVISION_2_CONSTITUTION_TEMPLATE.encode("utf-8")),
            )
            self.assertEqual(
                sum(
                    left != right
                    for left, right in zip(
                        changed.encode(), REVISION_2_CONSTITUTION_TEMPLATE.encode()
                    )
                ),
                1,
            )
            managed.write_text(changed, encoding="utf-8")

            refused = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(refused.returncode, 1, refused.stdout + refused.stderr)
            payload = json_output(refused)
            self.assertEqual(payload["status"], "attention_required")
            self.assertEqual(managed.read_text(encoding="utf-8"), changed)
            self.assertEqual(
                json.loads(locale_path.read_text(encoding="utf-8"))["bundle_revision"],
                2,
            )
            self.assertIn(
                ".specify/templates/constitution-template.md", payload["preserved"]
            )
            self.assertIn(".specify/spec-kit-sdd-locale.json", payload["preserved"])

            checked = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
            check_payload = json_output(checked)
            self.assertEqual(check_payload["status"], "changes_required")
            self.assertIn(
                ".specify/templates/constitution-template.md",
                check_payload["modified"],
            )
            self.assertIn(
                ".specify/spec-kit-sdd-locale.json",
                check_payload["upgradable_metadata"],
            )

    def test_custom_constitution_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-constitution-") as temp:
            project = Path(temp)
            self.assertEqual(command(str(INSTALLER), "--target", str(project)).returncode, 0)
            constitution = project / ".specify/memory/constitution.md"
            custom = "# 我们的宪章\n\n不可覆盖的团队原则。\n"
            constitution.write_text(custom, encoding="utf-8")

            checked = command(str(INSTALLER), "--target", str(project), "--check")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertIn(".specify/memory/constitution.md", json_output(checked)["protected_customizations"])
            forced = command(str(INSTALLER), "--target", str(project), "--force")
            self.assertEqual(forced.returncode, 1)
            self.assertEqual(constitution.read_text(encoding="utf-8"), custom)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs platform privileges")
    def test_symlink_destinations_fail_before_outside_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-link-") as temp:
            base = Path(temp)
            project = base / "project"
            outside = base / "outside"
            project.mkdir()
            outside.mkdir()
            (project / ".agents").symlink_to(outside, target_is_directory=True)

            result = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((project / ".specify").exists())

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs platform privileges")
    def test_dangling_parent_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-dangling-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            (project / ".specify").symlink_to(Path(temp) / "missing", target_is_directory=True)
            result = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("unsafe", str(json_output(result)["message"]))

    def test_non_codex_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-other-agent-") as temp:
            project = Path(temp)
            state = project / ".specify/integration.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"default_integration": "claude"}), encoding="utf-8")
            result = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Codex skills layout", str(json_output(result)["message"]))
            self.assertFalse((project / ".agents").exists())

    def test_gateway_risk_authorization_and_path_isolation(self) -> None:
        classification = command(str(RUNTIME), "classify", "--", "workflow", "run", "speckit")
        self.assertEqual(classification.returncode, 0)
        self.assertEqual(set(json_output(classification)["risks"]), {"code-execution", "project-write"})

        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-policy-") as temp:
            project = Path(temp)
            denied = command(str(RUNTIME), "run", "--target", str(project), "--", "init", "--here", "--integration", "codex")
            self.assertEqual(denied.returncode, 3, denied.stdout + denied.stderr)
            self.assertFalse((project / ".specify").exists())

            fake_bin = project / "fake-bin"
            fake_bin.mkdir()
            canary = project / "path-specify-ran"
            fake = fake_bin / "specify"
            fake.write_text(f"#!/bin/sh\ntouch '{canary}'\nexit 99\n", encoding="utf-8")
            fake.chmod(0o755)
            version = command(str(RUNTIME), "run", "--target", str(project), "--", "version", path=str(fake_bin))
            self.assertEqual(version.returncode, 0, version.stdout + version.stderr)
            self.assertFalse(canary.exists(), "wrapper executed PATH specify instead of fixed runtime")

    def test_broad_targets_are_rejected(self) -> None:
        root = Path(Path.cwd().anchor)
        result = command(str(INSTALLER), "--target", str(root), "--check")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("broad target", str(json_output(result)["message"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
