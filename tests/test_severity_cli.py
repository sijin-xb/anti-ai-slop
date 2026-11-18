"""Severity semantics, JSON structure and CLI exit-code behaviour."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import build_parser, main, scan_file  # noqa: E402
from scripts.rules import RULE_IDS, SEVERITY_BY_ID, SEVERITY_RANK  # noqa: E402

LIMITS = {"max_line": 140, "max_sentence": 90, "max_paragraph": 8}

def write_sample(tmp: str, text: str) -> Path:
    path = Path(tmp) / "sample.md"
    path.write_text(text, encoding="utf-8")
    return path

class SeverityAssignmentTests(unittest.TestCase):
    def test_deterministic_budget_violations_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("\n".join(f"第 {n} 段。" for n in range(130)), encoding="utf-8")
            found = scan_file(path, profile="zh-doc",
                              **{"max_line": 120, "max_sentence": 40, "max_paragraph": 4})
        self.assertTrue(found)
        self.assertTrue(all(SEVERITY_BY_ID[f.category] == "error"
                            for f in found if f.category.startswith(("readme-", "parity-"))))

    def test_length_measurements_are_warnings(self):
        text = "汉" * 60 + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, text)
            found = scan_file(path, profile="zh-doc", **{"max_line": 120, "max_sentence": 40, "max_paragraph": 4})
        self.assertTrue(found)
        self.assertEqual({f.severity for f in found}, {"warning"})

    def test_pattern_hits_are_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            found = scan_file(path, profile="general", **LIMITS)
        self.assertEqual([(f.category, f.severity) for f in found], [("filler", "advisory")])

    def test_every_registered_severity_is_valid(self):
        for rule_id, severity in SEVERITY_BY_ID.items():
            self.assertIn(severity, SEVERITY_RANK, rule_id)
            self.assertIn(rule_id, RULE_IDS)

class JsonOutputTests(unittest.TestCase):
    def test_json_contains_stable_rule_id_and_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n" + "汉" * 145 + "\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main(["--json", str(path)])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            self.assertIn("severity_counts", payload)
            self.assertEqual(
                payload["severity_counts"],
                {name: sum(1 for f in payload["findings"] if f["severity"] == name)
                 for name in ("error", "warning", "advisory")},
            )
            for finding in payload["findings"]:
                self.assertIn(finding["category"], RULE_IDS)
                self.assertIn(finding["severity"], SEVERITY_RANK)
            categories = {f["category"] for f in payload["findings"]}
            self.assertIn("filler", categories)
            self.assertIn("long-line", categories)

    def test_json_key_order_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main(["--json", str(path)])
            payload = json.loads(buf.getvalue())
            self.assertEqual(list(payload["findings"][0].keys()),
                             ["path", "line", "column", "category", "excerpt", "hint", "severity"])

class ExitCodeTests(unittest.TestCase):
    def test_strict_fails_on_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            self.assertEqual(main(["--strict", str(path)]), 1)

    def test_fail_on_error_ignores_advisory_and_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n" + "汉" * 95 + "\n")
            self.assertEqual(main(["--fail-on", "error", str(path)]), 0)

    def test_fail_on_warning_ignores_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n" + "汉" * 95 + "\n")
            self.assertEqual(main(["--fail-on", "warning", str(path)]), 1)

    def test_fail_on_error_fails_on_budget_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("\n".join(f"第 {n} 段。" for n in range(130)), encoding="utf-8")
            self.assertEqual(main(["--profile", "zh-doc", "--fail-on", "error", str(path)]), 1)

    def test_fail_on_none_is_the_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            self.assertEqual(main([str(path)]), 0)
            self.assertEqual(main(["--fail-on", "none", str(path)]), 0)

    def test_strict_and_fail_on_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "正文\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
                main(["--strict", "--fail-on", "error", str(path)])
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("not allowed with", err.getvalue())

    def test_strict_still_returns_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "该命令读取配置文件，并在校验失败时返回非零状态。\n")
            self.assertEqual(main(["--strict", str(path)]), 0)

    def test_error_exit_code_is_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main([str(Path(tmp) / "missing.md")]), 2)

class CliCompatTests(unittest.TestCase):
    def test_every_documented_flag_is_known_to_the_parser(self):
        documented = {"--profile", "--lang", "--json", "--strict", "--fail-on",
                      "--max-line", "--max-sentence", "--max-paragraph",
                      "--ignore-regex", "--pair"}
        known = {action.option_strings[0] for action in build_parser()._actions
                 if action.option_strings}
        self.assertTrue(documented <= known, documented - known)

    def test_documented_commands_parse(self):
        commands = [
            ["README.md"],
            ["--profile", "zh-doc", "README.md"],
            ["README.md", "--pair", "README.zh-CN.md"],
            ["--json", "docs/"],
            ["--lang", "de", "docs/"],
            ["--strict", "README.md"],
            ["--fail-on", "warning", "README.md"],
            ["--ignore-regex", "^> ", "README.md"],
        ]
        for argv in commands:
            with self.subTest(argv=argv):
                build_parser().parse_args(argv)

    def test_cli_help_mentions_profiles_and_severities(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit):
            build_parser().parse_args(["--help"])
        help_text = buf.getvalue()
        for needle in ("general", "zh-doc", "advisory", "warning", "error"):
            self.assertIn(needle, help_text)

    def test_human_output_includes_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main([str(path)])
            self.assertIn("[filler/advisory]", buf.getvalue())
            self.assertIn("advisory 1", buf.getvalue())

    def test_script_runs_as_plain_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sample(tmp, "值得注意的是这一句。\n")
            result = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "scripts" / "anti_slop_lint.py"), "--json", str(path)],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["finding_count"], 1)
            self.assertEqual(payload["findings"][0]["severity"], "advisory")
