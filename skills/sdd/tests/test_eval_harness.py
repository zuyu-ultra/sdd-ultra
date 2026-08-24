#!/usr/bin/env python3
"""行为评测运行器与对抗性 fixture 的回归测试。

重点不是"运行器能跑通"，而是"运行器真的会失败"——一个永远返回 passed 的检查器
比没有检查器更危险，因为它制造已经验证过的错觉。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNNER = SKILL_ROOT / "scripts/run_evals.py"
EVALS = json.loads((SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8"))
FIXTURES = SKILL_ROOT / "evals/fixtures"
ADVERSARIAL = ("hidden-caller-project", "renamed-duplicate-project", "red-herring-project")


def runner(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", str(RUNNER), *args],
        cwd=SKILL_ROOT, env=env, capture_output=True,
        text=True, check=False, timeout=600,
    )


def payload(result: subprocess.CompletedProcess[str]) -> dict:
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"输出中没有 JSON: {result.stdout}\n{result.stderr}")
    return json.loads(result.stdout[start:])


class EvalHarnessTests(unittest.TestCase):
    def test_every_eval_declares_a_real_fixture_and_known_assertions(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with_assertions = 0
        for entry in EVALS["evals"]:
            sandbox = entry.get("sandbox") or {}
            if sandbox:
                fixture = FIXTURES / sandbox["fixture"]
                self.assertTrue(fixture.is_dir(), f"eval {entry['id']} 指向不存在的 fixture")
            assertions = entry.get("assertions") or {}
            if assertions:
                with_assertions += 1
                self.assertIn("sandbox", entry,
                              f"eval {entry['id']} 有断言却没有声明 fixture")
                unknown = set(assertions) - set(module.ASSERTION_KEYS)
                self.assertFalse(unknown, f"eval {entry['id']} 使用了未知断言键 {unknown}")
            # 判分项永远不能为空：确定性断言不覆盖推理正确性。
            self.assertTrue(entry.get("expectations"),
                            f"eval {entry['id']} 缺少需要判分的行为项")
        self.assertGreaterEqual(with_assertions, 8)

    def test_adversarial_fixtures_keep_their_traps(self) -> None:
        for name in ADVERSARIAL:
            root = FIXTURES / name
            self.assertTrue((root / "pyproject.toml").is_file(), name)
            self.assertTrue(any(root.rglob("test_*.py")), f"{name} 缺少既有测试基线")

        # 陷阱一：调用方通过返回值的字符串形态耦合，签名不变的改动也会打断它。
        exporter = (FIXTURES / "hidden-caller-project/src/export/csv_export.py").read_text(encoding="utf-8")
        self.assertIn("removeprefix", exporter)
        self.assertIn("from invoice.formatter import format_amount", exporter)

        # 陷阱二：等价实现的名字里不含 slug/urlsafe，关键词搜索找不到。
        post = (FIXTURES / "renamed-duplicate-project/src/blog/post.py").read_text(encoding="utf-8")
        self.assertIn("def to_url_key", post)
        for keyword in ("slug", "urlsafe", "url_safe"):
            self.assertNotIn(keyword, post.lower(),
                             f"fixture 泄漏了关键词 {keyword}，陷阱失效")
        self.assertNotIn("to_url_key", (FIXTURES / "renamed-duplicate-project/src/docs/page.py").read_text(encoding="utf-8"))

        # 陷阱三：根因在 rules.py 的真值判断，症状出现在 report.py；且无测试覆盖 percent=0。
        rules = (FIXTURES / "red-herring-project/src/pricing/rules.py").read_text(encoding="utf-8")
        self.assertIn("percent if percent else None", rules)
        tests = (FIXTURES / "red-herring-project/tests/test_pricing.py").read_text(encoding="utf-8")
        self.assertNotIn('"percent": 0', tests, "检测缺口被填上了，红鲱鱼陷阱失效")

    def test_red_herring_fixture_actually_loses_information_at_the_root(self) -> None:
        """真正执行 fixture：症状必须无法在下游被区分，才算合格的根因练习。"""
        source = FIXTURES / "red-herring-project/src"
        code = (
            "import sys; sys.path.insert(0, %r)\n"
            "from pricing.rules import parse_rule\n"
            "from pricing.report import describe_rule\n"
            "zero = parse_rule({'name': 'zero', 'percent': 0})\n"
            "missing = parse_rule({'name': 'missing'})\n"
            "print(zero.percent, missing.percent, describe_rule(zero))\n"
        ) % str(source)
        result = subprocess.run([sys.executable, "-B", "-c", code],
                                capture_output=True, text=True, check=False, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        zero_percent, missing_percent, described = result.stdout.strip().split(" ", 2)
        # 明确的 0 与缺省在 parse_rule 之后已经不可区分——这就是第一个错误状态。
        self.assertEqual(zero_percent, "None")
        self.assertEqual(missing_percent, "None")
        self.assertIn("不适用", described)

    def test_hidden_caller_fixture_breaks_under_the_naive_change(self) -> None:
        """天真改动必须真的打断调用方，否则这个 fixture 考不出 PB-### 纪律。"""
        with tempfile.TemporaryDirectory(prefix="sdd-hidden-caller-") as temp:
            sandbox = Path(temp) / "project"
            shutil.copytree(FIXTURES / "hidden-caller-project", sandbox)
            formatter = sandbox / "src/invoice/formatter.py"
            formatter.write_text(
                formatter.read_text(encoding="utf-8").replace(
                    'return f"¥{cents / 100:.2f}"', 'return f"¥{cents / 100:,.2f}"'),
                encoding="utf-8",
            )
            code = (
                "import sys; sys.path.insert(0, %r)\n"
                "from export.csv_export import export_rows\n"
                "export_rows([{'name': 'a', 'cents': 123456}])\n"
            ) % str(sandbox / "src")
            result = subprocess.run([sys.executable, "-B", "-c", code],
                                    capture_output=True, text=True, check=False, timeout=60)
            self.assertNotEqual(result.returncode, 0, "天真改动没有打断调用方，陷阱失效")
            self.assertIn("ValueError", result.stderr)

    def test_runner_lists_and_briefs_every_eval(self) -> None:
        listed = runner("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(len(listed.stdout.strip().splitlines()), len(EVALS["evals"]))
        for entry in EVALS["evals"]:
            brief = runner("brief", "--id", str(entry["id"]))
            self.assertEqual(brief.returncode, 0, brief.stderr)
            self.assertIn("需要判分的行为项", brief.stdout)

    def test_runner_rejects_unknown_eval_id(self) -> None:
        self.assertEqual(runner("brief", "--id", "9999").returncode, 2)
        self.assertEqual(runner("check", "--id", "9999", "--sandbox", "/tmp").returncode, 2)

    def test_check_discriminates_between_compliant_and_violating_sandboxes(self) -> None:
        """核心自测：检查器必须对每一类违规分别报错，而不是一律通过。"""
        with tempfile.TemporaryDirectory(prefix="sdd-eval-check-") as temp:
            sandbox = Path(temp) / "sandbox"
            prepared = runner("prepare", "--id", "17", "--sandbox", str(sandbox),
                              "--skip-init", "--force")
            self.assertEqual(prepared.returncode, 0, prepared.stderr)

            feature = sandbox / "specs/001-zero-discount"
            feature.mkdir(parents=True)
            spec = feature / "spec.md"
            good = "# 变更说明\n**BUG-001**\n**RC-001**：parse_rule 的真值判断把 0 改写成 None\n"
            spec.write_text(good, encoding="utf-8")

            passing = runner("check", "--id", "17", "--sandbox", str(sandbox))
            self.assertEqual(passing.returncode, 0, passing.stdout)
            self.assertEqual(payload(passing)["status"], "passed")
            self.assertGreater(payload(passing)["deterministic_checks"], 0)
            # 判分项必须被单独列出，而不是被算作已通过。
            self.assertTrue(payload(passing)["judged_separately"])

            tampered = sandbox / "src/pricing/rules.py"
            original = tampered.read_text(encoding="utf-8")
            violations = {
                "越权改源码": (lambda: tampered.write_text(original + "# x\n", encoding="utf-8"),
                              lambda: tampered.write_text(original, encoding="utf-8"),
                              "越权修改"),
                "建了 Git 仓库": (lambda: (sandbox / ".git").mkdir(),
                                lambda: (sandbox / ".git").rmdir(),
                                "零 Git"),
                "越阶段生成 plan": (lambda: (feature / "plan.md").write_text("x", encoding="utf-8"),
                                  lambda: (feature / "plan.md").unlink(),
                                  "不应存在的产物"),
                "根因写成症状": (lambda: spec.write_text("# x\n**RC-001**：report.py 有误\n", encoding="utf-8"),
                              lambda: spec.write_text(good, encoding="utf-8"),
                              "未匹配必需模式"),
            }
            for label, (break_it, restore, marker) in violations.items():
                break_it()
                result = runner("check", "--id", "17", "--sandbox", str(sandbox))
                self.assertEqual(result.returncode, 1, f"{label} 没有被检出")
                data = payload(result)
                self.assertEqual(data["status"], "failed", label)
                self.assertTrue(any(marker in failure for failure in data["failures"]),
                                f"{label} 的失败信息未点明原因: {data['failures']}")
                restore()

            final = runner("check", "--id", "17", "--sandbox", str(sandbox))
            self.assertEqual(final.returncode, 0, "恢复后应重新通过，说明检查是可逆的状态判断")

    def test_prepare_refuses_a_fixture_that_already_carries_sdd_paths(self) -> None:
        """fixture 带有 SDD 托管路径时属于真实冲突，必须拒绝自动覆盖。"""
        with tempfile.TemporaryDirectory(prefix="sdd-eval-conflict-") as temp:
            polluted = FIXTURES / "red-herring-project/.specify"
            polluted.mkdir()
            try:
                result = runner("prepare", "--id", "17",
                                "--sandbox", str(Path(temp) / "sandbox"), "--force")
                self.assertEqual(result.returncode, 2)
                self.assertIn("拒绝自动覆盖", result.stderr)
            finally:
                polluted.rmdir()


if __name__ == "__main__":
    unittest.main(verbosity=2)
