#!/usr/bin/env python3
"""中文 Skill 网关、初始化器与安全边界回归测试。"""

from __future__ import annotations

import json
import hashlib
import datetime
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

    def test_ambiguous_requirements_route_to_co_creation_before_any_write(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        stages = SKILL_ROOT / "assets/project/.agents/skills"
        specify = (stages / "speckit-specify/SKILL.md").read_text(encoding="utf-8")
        clarify = (stages / "speckit-clarify/SKILL.md").read_text(encoding="utf-8")
        plan = (stages / "speckit-plan/SKILL.md").read_text(encoding="utf-8")
        analyze = (stages / "speckit-analyze/SKILL.md").read_text(encoding="utf-8")
        spec_template = (
            SKILL_ROOT / "assets/project/.specify/templates/spec-template.md"
        ).read_text(encoding="utf-8")
        workflow = (
            SKILL_ROOT / "assets/project/.specify/workflows/speckit/workflow.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("模糊需求的共创讨论", root_skill)
        self.assertIn("需求成熟度评估", root_skill)
        self.assertIn("discovery.md", root_skill)

        # 评估与讨论必须发生在任何文件写入之前，并落到独立的决策台账。
        self.assertIn("任何文件写入之前", specify)
        self.assertIn("不得**创建功能目录、复制模板或写入任何文件", specify)
        self.assertIn("每次严格只展示一个", specify)
        self.assertIn("discovery.md", specify)
        self.assertIn("DD-###", specify)
        self.assertIn("由 Agent 代选", specify)
        self.assertIn("延后决策", specify)

        # 用户交回决定权不等于可以跳过展示选项，提前终止也不解除硬底线。
        self.assertIn("你看着办", specify)
        self.assertIn("不得**询问用户是否批准进入规划", specify)

        # 单一决策台账：clarify 与 plan 追加而不是另起炉灶。
        self.assertIn("discovery.md", clarify)
        self.assertIn("取代 DD-00X", clarify)
        self.assertIn("技术分歧点", plan)
        self.assertIn("DD-###", plan)
        self.assertIn("可逆性", plan)

        # 决策台账必须贯穿到下游执行阶段，而不是只停在 spec/plan。
        downstream = {
            "speckit-tasks": "任务范围与每个 `DD-###`",
            "speckit-implement": "实现与每个 `DD-###`",
            "speckit-converge": "决策图",
            "speckit-checklist": "由 Agent 代选",
        }
        for stage, marker in downstream.items():
            body = (stages / stage / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("DD-###", body, f"{stage} 不知道 DD-### 决策台账")
            self.assertIn(marker, body, f"{stage} 缺少决策一致性约束")

        # 每个改动产物的阶段都要把 discovery.md 纳入 hook 快照集合。
        for stage in ("speckit-specify", "speckit-clarify", "speckit-plan",
                      "speckit-tasks", "speckit-implement"):
            body = (stages / stage / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("discovery.md", body, f"{stage} 未把 discovery.md 纳入快照")

        # 一致性由 analyze 独立复核，规格模板保留追溯入口。
        self.assertIn("需求共创决策一致性", analyze)
        self.assertIn("需求共创决策", spec_template)
        self.assertIn("DD-001", spec_template)
        self.assertIn("discovery.md", workflow)

    def test_size_tiers_scale_ceremony_but_never_the_redlines(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        stages = SKILL_ROOT / "assets/project/.agents/skills"
        specify = (stages / "speckit-specify/SKILL.md").read_text(encoding="utf-8")
        implement = (stages / "speckit-implement/SKILL.md").read_text(encoding="utf-8")
        spec_template = (
            SKILL_ROOT / "assets/project/.specify/templates/spec-template.md"
        ).read_text(encoding="utf-8")

        # 四档存在，且判定必须基于可核实影响面而非主观感觉。
        self.assertIn("需求规模分级", root_skill)
        for tier in ("XS", "S", "M", "L"):
            self.assertIn(f"`{tier}`", root_skill)
        self.assertIn("不确定就往上取", root_skill)
        self.assertIn("规模判定", specify)
        self.assertIn("不得凭需求描述的字面篇幅判断", specify)

        # 缩放的是仪式感：精简模式跳过 plan/tasks/converge，只留一个关卡。
        self.assertIn("精简模式", specify)
        self.assertIn("批准变更说明", specify)
        self.assertIn("批准变更说明", implement)
        for stage in ("speckit-plan", "speckit-tasks"):
            body = (stages / stage / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("规模档位关卡", body, f"{stage} 未识别精简模式")
        converge = (stages / "speckit-converge/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("精简模式无需收敛", converge)

        # 不缩放的是安全性：红线在 XS 上照常全量执行。
        self.assertIn("永不缩放的红线", root_skill)
        for redline in ("PB-###", "RC-###", "NM-###", "兼容适配层"):
            self.assertIn(redline, root_skill)
        self.assertIn("任何档位都不存在零批准", root_skill)
        self.assertIn("精简模式**不缩减**的部分", specify)

        # 升档单向，且不能靠拆需求规避。
        self.assertIn("升档是单向的", root_skill)
        self.assertIn("不得把超出部分拆成“后续需求”", root_skill)
        self.assertIn("升档触发检查", implement)
        self.assertIn("不得**把超出部分拆成“后续需求”", implement)

        # 下游靠 spec.md 的档位字段路由，缺失时必须回落到完整模式。
        self.assertIn("规模档位", spec_template)
        for stage in ("speckit-plan", "speckit-tasks", "speckit-implement",
                      "speckit-analyze", "speckit-converge"):
            body = (stages / stage / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("规模档位", body, f"{stage} 未读取档位字段")
            self.assertIn("缺失", body, f"{stage} 未定义档位缺失时的回落行为")

    def test_obsidian_storage_policy_is_managed(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        specify = (
            SKILL_ROOT
            / "assets/project/.agents/skills/speckit-specify/SKILL.md"
        ).read_text(encoding="utf-8")
        creator = (
            SKILL_ROOT
            / "assets/project/.specify/scripts/python/create_new_feature.py"
        ).read_text(encoding="utf-8")
        common = (
            SKILL_ROOT / "assets/project/.specify/scripts/python/common.py"
        ).read_text(encoding="utf-8")

        for marker in (
            "Obsidian",
            ".specify/sdd-storage.json",
            "YYYY年MM月DD日-中文需求名",
            "不得重新拼接 `<repo-root>/specs/`",
        ):
            self.assertIn(marker, root_skill)
        self.assertIn("--artifact-root", specify)
        self.assertIn("--folder-name", specify)
        self.assertIn("STORAGE_MODE", creator)
        self.assertIn("FEATURE_METADATA_NAME", common)

    def test_brownfield_policy_is_routed_to_all_mutating_stages(self) -> None:
        root_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        shortcut = (SKILL_ROOT.parent / "sdd/SKILL.md").read_text(encoding="utf-8")
        reference = (SKILL_ROOT / "references/brownfield-compatibility.md").read_text(encoding="utf-8")
        self.assertIn("红线 1", root_skill)
        self.assertIn("红线 2", root_skill)
        self.assertIn("NM-###", root_skill)
        self.assertIn("RC-###", root_skill)
        self.assertIn("模板、replace override", root_skill)
        self.assertIn("NM-###", shortcut)
        self.assertIn("RC-###", shortcut)
        self.assertIn("直接调用现有实现", reference)
        self.assertIn("Bug 根因前置协议", reference)

        required = {
            "speckit-specify": ("PB-###", "RC-###", "项目证据优先"),
            "speckit-clarify": ("PB-###", "RC-###", "兼容边界"),
            "speckit-plan": ("PB-###", "NM-###", "RC-###", "变更前基线"),
            "speckit-tasks": ("PB-###", "NM-###", "RC-###", "存量验证不可选"),
            "speckit-analyze": ("PB-###", "NM-###", "RC-###", "CRITICAL"),
            "speckit-implement": ("PB-###", "NM-###", "RC-###", "变更前基线"),
            "speckit-converge": ("PB-###", "NM-###", "RC-###", "regression"),
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

        for marker in ("存量行为与兼容性", "PB-###", "本次不会改变", "Bug 来龙去脉与根因分析", "RC-###", "因果链", "检测缺口"):
            self.assertIn(marker, spec)
        for marker in ("现有实现与项目惯例", "复用决策", "NM-###", "根因到方案追踪", "RC-###", "回归验证矩阵", "变更前基线"):
            self.assertIn(marker, plan)
        for marker in ("存量基线与复用确认", "PB-###", "NM-###", "RC-###", "检测缺口", "Bug 修复", "项目标准 lint/typecheck/build/test"):
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
        self.assertIn("根因被推翻", implement)
        self.assertIn("根因关卡不可协商", analyze)
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

    def test_external_obsidian_requirement_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-obsidian-") as temp:
            base = Path(temp)
            project = base / "应用项目"
            vault_root = base / "Obsidian资料库" / "SDD历史"
            project.mkdir()
            vault_root.mkdir(parents=True)
            installed = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            scripts = project / ".specify/scripts/python"
            created = command(
                str(scripts / "create_new_feature.py"),
                "--json",
                "--artifact-root",
                str(vault_root),
                "--folder-name",
                "订单超时修复",
                "修复订单处理超时",
                cwd=project,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            payload = json_output(created)
            feature_dir = Path(str(payload["FEATURE_DIR"]))
            self.assertRegex(
                feature_dir.name,
                r"^\d{4}年\d{2}月\d{2}日-订单超时修复$",
            )
            self.assertEqual(payload["STORAGE_MODE"], "external")
            self.assertEqual(Path(str(payload["ARTIFACT_ROOT"])), vault_root.resolve())
            self.assertTrue((feature_dir / "spec.md").is_file())
            self.assertFalse((project / "specs").exists())

            active = json.loads(
                (project / ".specify/feature.json").read_text(encoding="utf-8")
            )
            storage = json.loads(
                (project / ".specify/sdd-storage.json").read_text(encoding="utf-8")
            )
            metadata = json.loads(
                (feature_dir / ".sdd-feature.json").read_text(encoding="utf-8")
            )
            self.assertEqual(active["feature_directory"], str(feature_dir))
            self.assertEqual(storage["mode"], "external")
            self.assertEqual(storage["artifact_root"], str(vault_root.resolve()))
            self.assertEqual(storage["active_feature_directory"], str(feature_dir))
            self.assertEqual(metadata["project_root"], str(project.resolve()))

            paths = command(
                str(scripts / "check_prerequisites.py"),
                "--paths-only",
                "--json",
                cwd=project,
            )
            self.assertEqual(paths.returncode, 0, paths.stdout + paths.stderr)
            paths_payload = json_output(paths)
            self.assertEqual(paths_payload["FEATURE_DIR"], str(feature_dir))
            self.assertEqual(paths_payload["STORAGE_MODE"], "external")

            planned = command(
                str(scripts / "setup_plan.py"), "--json", cwd=project
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
            plan_payload = json_output(planned)
            self.assertEqual(plan_payload["STORAGE_MODE"], "external")
            self.assertEqual(Path(str(plan_payload["IMPL_PLAN"])), feature_dir / "plan.md")
            self.assertTrue((feature_dir / "plan.md").is_file())
            self.assertFalse((project / "specs").exists())

            duplicate = command(
                str(scripts / "create_new_feature.py"),
                "--json",
                "--artifact-root",
                str(vault_root),
                "--folder-name",
                "订单超时修复",
                "修复订单处理超时",
                cwd=project,
            )
            self.assertEqual(duplicate.returncode, 0, duplicate.stdout + duplicate.stderr)
            duplicate_dir = Path(str(json_output(duplicate)["FEATURE_DIR"]))
            self.assertEqual(duplicate_dir.name, feature_dir.name + "-02")

            reused_root = command(
                str(scripts / "create_new_feature.py"),
                "--json",
                "--folder-name",
                "支付回调优化",
                "优化支付回调",
                cwd=project,
            )
            self.assertEqual(reused_root.returncode, 0, reused_root.stdout + reused_root.stderr)
            reused_payload = json_output(reused_root)
            self.assertEqual(reused_payload["STORAGE_MODE"], "external")
            self.assertEqual(Path(str(reused_payload["FEATURE_DIR"])).parent, vault_root.resolve())

            local_override = command(
                str(scripts / "create_new_feature.py"),
                "--json",
                "--project-storage",
                "--short-name",
                "local-note",
                "Create local requirement",
                cwd=project,
            )
            self.assertEqual(
                local_override.returncode,
                0,
                local_override.stdout + local_override.stderr,
            )
            self.assertEqual(json_output(local_override)["STORAGE_MODE"], "project")

    def test_external_active_pointer_cannot_escape_approved_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-storage-escape-") as temp:
            base = Path(temp)
            project = base / "project"
            vault_root = base / "vault"
            outside = base / "outside-requirement"
            project.mkdir()
            vault_root.mkdir()
            outside.mkdir()
            self.assertEqual(
                command(str(INSTALLER), "--target", str(project)).returncode,
                0,
            )
            scripts = project / ".specify/scripts/python"
            created = command(
                str(scripts / "create_new_feature.py"),
                "--json",
                "--artifact-root",
                str(vault_root),
                "--folder-name",
                "安全路径",
                "验证路径边界",
                cwd=project,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            (project / ".specify/feature.json").write_text(
                json.dumps({"feature_directory": str(outside)}, ensure_ascii=False),
                encoding="utf-8",
            )
            rejected = command(
                str(scripts / "check_prerequisites.py"),
                "--paths-only",
                "--json",
                cwd=project,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("outside the approved external artifact root", rejected.stderr)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs platform privileges")
    def test_external_existing_requirement_symlink_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-feature-link-") as temp:
            base = Path(temp)
            project = base / "project"
            vault_root = base / "vault"
            outside = base / "outside"
            project.mkdir()
            vault_root.mkdir()
            outside.mkdir()
            self.assertEqual(
                command(str(INSTALLER), "--target", str(project)).returncode,
                0,
            )
            dated_name = datetime.datetime.now().strftime("%Y年%m月%d日-逃逸需求")
            (vault_root / dated_name).symlink_to(outside, target_is_directory=True)
            creator = project / ".specify/scripts/python/create_new_feature.py"
            rejected = command(
                str(creator),
                "--json",
                "--allow-existing-branch",
                "--artifact-root",
                str(vault_root),
                "--folder-name",
                "逃逸需求",
                "验证外置目录安全",
                cwd=project,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("escapes the approved artifact root", rejected.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_project_storage_remains_the_default(self) -> None:
        with tempfile.TemporaryDirectory(prefix="spec-kit-sdd-project-storage-") as temp:
            project = Path(temp)
            installed = command(str(INSTALLER), "--target", str(project))
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            creator = project / ".specify/scripts/python/create_new_feature.py"
            created = command(
                str(creator),
                "--json",
                "--short-name",
                "user-auth",
                "Add user authentication",
                cwd=project,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            payload = json_output(created)
            self.assertEqual(payload["STORAGE_MODE"], "project")
            self.assertEqual(
                Path(str(payload["FEATURE_DIR"])),
                project.resolve() / "specs/001-user-auth",
            )
            self.assertTrue((project / "specs/001-user-auth/spec.md").is_file())
            storage = json.loads(
                (project / ".specify/sdd-storage.json").read_text(encoding="utf-8")
            )
            self.assertEqual(storage["artifact_root"], "specs")
            self.assertEqual(storage["active_feature_directory"], "specs/001-user-auth")

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
        self.assertEqual(set(loaded["bundle_revisions"]), {2, 4, 5, 6})
        self.assertEqual(set(loaded["bundle_revisions"][2]), expected_paths)
        self.assertEqual(set(loaded["bundle_revisions"][4]), expected_paths)
        self.assertEqual(set(loaded["bundle_revisions"][5]), expected_paths)
        self.assertEqual(set(loaded["bundle_revisions"][6]), expected_paths)
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
                7,
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
