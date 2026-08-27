#!/usr/bin/env python3
"""不可由模板、审批、Hook 或流程顺序绕过的 Brownfield 回归测试。"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets/project"
RESOLVER = ASSETS / ".specify/scripts/python/resolve_template.py"


class BrownfieldGuardTests(unittest.TestCase):
    def test_replace_overrides_cannot_remove_safety_gates(self) -> None:
        expected = {
            "spec-template": ("不可覆盖的存量安全约束", "PB-###", "本次不会改变", "RC-###", "因果链"),
            "plan-template": ("不可覆盖的存量实施关卡", "NM-###", "RC-###", "变更前基线", "回归验证矩阵"),
            "tasks-template": ("不可覆盖的任务安全关卡", "PB-###", "NM-###", "RC-###", "项目标准 lint/typecheck/build/test"),
            "checklist-template": ("不可覆盖的存量兼容性审查", "PB-###"),
            "constitution-template": ("不可覆盖原则：复用优先与零回归", "Bug 修复不得引入新 Bug"),
        }
        for template_name, markers in expected.items():
            with self.subTest(template=template_name), tempfile.TemporaryDirectory(
                prefix="sdd-replace-override-"
            ) as temp:
                project = Path(temp)
                overrides = project / ".specify/templates/overrides"
                overrides.mkdir(parents=True)
                (overrides / f"{template_name}.md").write_text(
                    "# 旧版 replace 模板\n\n测试可以跳过，也不需要复用证据。\n",
                    encoding="utf-8",
                )
                environment = os.environ.copy()
                environment["PYTHONDONTWRITEBYTECODE"] = "1"
                environment["SPECIFY_INIT_DIR"] = str(project)
                result = subprocess.run(
                    [sys.executable, "-B", str(RESOLVER), template_name, "--json"],
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                content = json.loads(result.stdout)["TEMPLATE_CONTENT"]
                for marker in markers:
                    self.assertIn(marker, content)

    def test_dangerous_greenfield_defaults_are_not_in_templates(self) -> None:
        templates = ASSETS / ".specify/templates"
        tasks = (templates / "tasks-template.md").read_text(encoding="utf-8")
        plan = (templates / "plan-template.md").read_text(encoding="utf-8")

        for forbidden in (
            "如果需求要求测试",
            "创建 Entity",
            "Models → Services → Endpoints",
            "模型先于服务",
            "服务先于端点",
            "清理和重构代码",
        ):
            self.assertNotIn(forbidden, tasks)
        self.assertNotRegex(tasks, r"测试.{0,8}(?:可选|按需|如果.{0,8}要求)")
        self.assertNotIn("Repository pattern", plan)
        self.assertNotRegex(plan, r"src/\s*\n[├└].*(?:models|services)")
        self.assertNotRegex(plan, r"(?:frontend|backend)/\s*#")

    def test_tasks_are_analyzed_before_the_user_approval_gate(self) -> None:
        root = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        strategy = (SKILL_ROOT / "references/sdd-strategies.md").read_text(encoding="utf-8")
        workflow = (ASSETS / ".specify/workflows/speckit/workflow.yml").read_text(encoding="utf-8")

        self.assertRegex(root, r"tasks\s*->\s*analyze\s*->\s*✓tasks")
        self.assertRegex(strategy, r"tasks\s*->\s*analyze\s*->\s*\n?用户批准 tasks \+ analyze")
        step_ids = re.findall(r"^\s*- id:\s*([a-z0-9-]+)\s*$", workflow, re.MULTILINE)
        self.assertEqual(len(step_ids), len(set(step_ids)))
        for earlier, later in (("tasks", "analyze"), ("analyze", "review-tasks"), ("review-tasks", "implement")):
            self.assertLess(step_ids.index(earlier), step_ids.index(later))
        self.assertIn("存在 CRITICAL", workflow)
        self.assertIn("必须拒绝", workflow)

    def test_each_mutating_stage_invalidates_stale_hook_evidence(self) -> None:
        stages = (
            "speckit-specify",
            "speckit-clarify",
            "speckit-plan",
            "speckit-tasks",
            "speckit-analyze",
            "speckit-implement",
            "speckit-converge",
        )
        for stage in stages:
            content = (ASSETS / f".agents/skills/{stage}/SKILL.md").read_text(encoding="utf-8")
            with self.subTest(stage=stage):
                self.assertIn("SHA-256", content)
                self.assertRegex(content, r"before_[a-z]+")
                self.assertRegex(content, r"after_[a-z]+")
                self.assertIn("失效", content)

    def test_behavior_evals_have_fixtures_gates_and_a_safe_new_symbol_case(self) -> None:
        payload = json.loads((SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8"))
        evals = {entry["id"]: entry for entry in payload["evals"]}
        self.assertTrue({5, 6, 7, 8, 9, 10}.issubset(evals))
        self.assertIn("evals/fixtures/phone-project", evals[5]["prompt"])
        self.assertIn("只执行 plan 阶段", evals[5]["prompt"])
        self.assertIn("evals/fixtures/date-range-project", evals[6]["prompt"])
        self.assertIn("强制 analyze", evals[6]["prompt"])
        self.assertNotIn("批准破坏性变化", evals[7]["expected_output"])
        self.assertIn("不能以用户批准豁免", evals[7]["expected_output"])
        self.assertIn("NM-001", evals[9]["expected_output"])
        self.assertIn("不能安全复用", evals[9]["prompt"])
        self.assertIn("写 spec.md 前", evals[10]["prompt"])
        self.assertIn("RC-001", evals[10]["expected_output"])

        for fixture in ("phone-project", "date-range-project", "hidden-caller-project",
                        "renamed-duplicate-project", "red-herring-project"):
            fixture_root = SKILL_ROOT / "evals/fixtures" / fixture
            self.assertTrue((fixture_root / "pyproject.toml").is_file())
            self.assertTrue(any((fixture_root / "src").rglob("*.py")), fixture)
            self.assertTrue(any((fixture_root / "tests").rglob("test_*.py")), fixture)

    def test_bug_root_cause_is_a_pre_spec_hard_gate_across_all_stages(self) -> None:
        root = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        shortcut = (SKILL_ROOT.parent / "sdd/SKILL.md").read_text(encoding="utf-8")
        reference = (SKILL_ROOT / "references/brownfield-compatibility.md").read_text(encoding="utf-8")
        specify = (ASSETS / ".agents/skills/speckit-specify/SKILL.md").read_text(encoding="utf-8")
        plan = (ASSETS / ".agents/skills/speckit-plan/SKILL.md").read_text(encoding="utf-8")
        tasks = (ASSETS / ".agents/skills/speckit-tasks/SKILL.md").read_text(encoding="utf-8")
        analyze = (ASSETS / ".agents/skills/speckit-analyze/SKILL.md").read_text(encoding="utf-8")
        implement = (ASSETS / ".agents/skills/speckit-implement/SKILL.md").read_text(encoding="utf-8")
        spec_template = (ASSETS / ".specify/templates/spec-template.md").read_text(encoding="utf-8")

        for content in (root, shortcut, reference, specify):
            self.assertIn("RC-###", content)
            self.assertRegex(content, r"(?:写|填写|创建).*spec\.md.*前|spec\.md.*写入之前")
        for marker in ("事实时间线", "复现证据", "因果链", "第一个错误", "检测缺口", "证伪"):
            self.assertIn(marker, spec_template)
        self.assertIn("根因未确认", specify)
        self.assertIn("不得请求“批准规格”", specify)
        self.assertIn("根因未确认", plan)
        self.assertIn("检测缺口", tasks)
        self.assertIn("始终为 CRITICAL", analyze)
        self.assertIn("规格、计划和任务批准失效", implement)


if __name__ == "__main__":
    unittest.main(verbosity=2)
