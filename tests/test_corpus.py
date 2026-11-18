"""Manifest-driven corpus tests and metric floors.

The manifest (tests/corpus/manifest.json) holds human-assigned labels:
good files must stay at zero findings, bad files must hit their required
rule IDs. Metrics are computed by scripts/corpus_metrics.py from the same
labels; the floor tests keep regressions visible in CI.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import scan_file  # noqa: E402

CORPUS = Path(__file__).resolve().parent / "corpus"
LIMITS = {
    "general": {"max_line": 140, "max_sentence": 90, "max_paragraph": 8},
    "zh-doc": {"max_line": 120, "max_sentence": 40, "max_paragraph": 4},
}

def scan_path(path: Path, profile: str):
    return scan_file(path, profile=profile, **LIMITS[profile])

def load_manifest() -> dict:
    return json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))

class GoodCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_good_corpus_zero_findings_general(self):
        for path in sorted((CORPUS / "good").glob("*.md")):
            with self.subTest(path=path.name):
                self.assertEqual([f.category for f in scan_path(path, "general")], [], path.name)

    def test_good_corpus_zero_findings_zh_doc(self):
        for path in sorted((CORPUS / "good").glob("*.md")):
            with self.subTest(path=path.name):
                self.assertEqual([f.category for f in scan_path(path, "zh-doc")], [], path.name)

    def test_allowed_exceptions_are_declared_and_real(self):
        for name, entry in self.manifest["good"].items():
            self.assertIsInstance(entry.get("allowed", []), list, name)
            for rule_id in entry.get("allowed", []):
                self.assertIn(rule_id, entry, rule_id)

class BadCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_bad_files_hit_required_rules_general(self):
        for path in sorted((CORPUS / "bad").glob("*.md")):
            required = set(self.manifest["bad"][path.name]["expected"])
            found = {f.category for f in scan_path(path, "general")}
            with self.subTest(path=path.name):
                self.assertTrue(required <= found,
                                f"{path.name}: missing {sorted(required - found)}")

    def test_bad_files_hit_required_rules_zh_doc(self):
        for name, entry in self.manifest["bad"].items():
            required = set(entry.get("zh_doc_expected", []))
            if not required:
                continue
            found = {f.category for f in scan_path(CORPUS / "bad" / name, "zh-doc")}
            with self.subTest(path=name):
                self.assertTrue(required <= found,
                                f"{name}: missing {sorted(required - found)}")

    def test_required_rules_are_registered(self):
        from scripts.rules import LINTER_RULE_IDS
        for name, entry in self.manifest["bad"].items():
            for rule_id in entry["expected"] + entry.get("zh_doc_expected", []):
                self.assertIn(rule_id, LINTER_RULE_IDS, f"{name}: {rule_id}")

    def test_required_rules_are_realistic_for_profile(self):
        """zh-doc deliberately loads no de/fr/es/ja/ko packs, so those files
        must not carry a zh_doc_expected set."""
        for name, entry in self.manifest["bad"].items():
            if name.startswith(("de-", "fr-", "es-", "ja-", "ko-")):
                self.assertNotIn("zh_doc_expected", entry, name)

class MetricsFloorTests(unittest.TestCase):
    """Floors for the labeled corpus. 1.0 floors are honest for a curated
    corpus: any regression shows up here first. Style problems that no regex
    can judge objectively are outside these labels (see manifest)."""
    FLOOR = 1.0

    @classmethod
    def setUpClass(cls):
        from scripts.corpus_metrics import compute_report
        cls.reports = {profile: compute_report(profile) for profile in ("general", "zh-doc")}

    def test_precision_at_floor(self):
        for profile, report in self.reports.items():
            self.assertGreaterEqual(report["precision"], self.FLOOR, profile)

    def test_recall_at_floor(self):
        for profile, report in self.reports.items():
            self.assertGreaterEqual(report["recall"], self.FLOOR, profile)

    def test_file_fpr_at_floor(self):
        for profile, report in self.reports.items():
            self.assertLessEqual(report["file_fpr"], 1.0 - self.FLOOR, profile)

    def test_report_is_reproducible_and_json_serializable(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "corpus_metrics.py"),
             "--all-profiles", "--json"],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload), 2)
        for report in payload:
            self.assertIn("precision", report)
            self.assertIn("per_language", report)
            self.assertIn("per_rule", report)
