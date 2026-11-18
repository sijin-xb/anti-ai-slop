"""Project-consistency tests: rule registry integrity, SKILL.md frontmatter,
reference routing, and documented CLI commands staying in sync with the code.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import (  # noqa: E402
    LANG_PACKS, PROFILES, build_parser, scan_file,
)
from scripts.rules import LINTER_RULE_IDS, RULES, SEVERITY_BY_ID  # noqa: E402

SKILL_MD = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
README_MD = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")

def categories_of(text: str, profile: str = "general", suffix: str = ".md") -> set[str]:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"sample{suffix}"
        path.write_text(text, encoding="utf-8")
        limits = {"max_line": 140, "max_sentence": 90, "max_paragraph": 8}
        if profile == "zh-doc":
            limits = {"max_line": 120, "max_sentence": 40, "max_paragraph": 4}
        return {f.category for f in scan_file(path, profile=profile, **limits)}

class RuleRegistryTests(unittest.TestCase):
    def test_every_linter_rule_can_fire(self):
        triggers = {
            "filler": "值得注意的是这一句。\n",
            "meta": "本文档旨在介绍安装流程。\n",
            "thinking-leak": "让我先检查一下配置。\n",
            "overclaim": "这个方案可以百分之百保证稳定。\n",
            "closer": "希望本文对你有所帮助，如有疑问欢迎随时交流。\n",
            "conversational": "其实，这个方案更适合。\n",
            "buzzword": "这套方案助力团队提效。\n",
            "contrast": "这不是终点，而是起点。\n",
            "exclamation": "部署完成！\n",
            "long-line": "x" * 141 + "\n",
            "long-sentence": "汉" * 145 + "。\n",
            "long-paragraph": "\n".join(f"第 {n} 行。" for n in range(5)) + "\n",
            "repeated-line": "这是足够长的重复内容用来验证检测是否生效第一段。\n\n"
                             "这是足够长的重复内容用来验证检测是否生效第一段。\n",
            "readme-line-budget": None,
            "readme-char-budget": None,
            "parity-heading": None,
            "parity-table": None,
            "parity-number": None,
        }
        import tempfile
        for rule_id in sorted(LINTER_RULE_IDS):
            with self.subTest(rule_id=rule_id):
                if rule_id.startswith("readme-"):
                    path = Path(tempfile.mkdtemp()) / "README.md"
                    path.write_text("\n".join(f"第 {n} 段中文说明文字。" for n in range(130)), encoding="utf-8")
                    found = scan_file(path, profile="zh-doc",
                                      **{"max_line": 120, "max_sentence": 40, "max_paragraph": 4})
                    self.assertIn(rule_id, {f.category for f in found}, rule_id)
                elif rule_id.startswith("parity-"):
                    with tempfile.TemporaryDirectory() as tmp:
                        main_p = Path(tmp) / "README.md"
                        pair_p = Path(tmp) / "README.zh-CN.md"
                        main_p.write_text("keep 30 snapshots\n\n# A\n\n## B\n", encoding="utf-8")
                        pair_p.write_text("保留 45 份快照\n", encoding="utf-8")
                        from scripts.anti_slop_lint import parity_findings
                        found = {f.category for f in parity_findings(main_p, pair_p)}
                    self.assertTrue({"parity-heading", "parity-number"} & found, rule_id)
                else:
                    profile = "zh-doc" if rule_id in ("conversational", "buzzword", "contrast",
                                                      "exclamation", "long-sentence", "long-paragraph") else "general"
                    self.assertIn(rule_id, categories_of(triggers[rule_id], profile), rule_id)

    def test_severities_follow_the_documented_model(self):
        for rule in RULES:
            if rule.rule_id.startswith(("parity-", "readme-")):
                self.assertEqual(rule.severity, "error", rule.rule_id)
            elif rule.detectable == "auto":
                self.assertEqual(rule.severity, "warning", rule.rule_id)
            else:
                self.assertEqual(rule.severity, "advisory", rule.rule_id)

    def test_every_language_pack_category_is_registered(self):
        for lang, pack in LANG_PACKS.items():
            for category, _pattern, _hint in pack:
                self.assertIn(category, SEVERITY_BY_ID, f"{lang}/{category}")

    def test_registry_test_anchors_exist(self):
        test_sources = "\n".join(
            p.read_text(encoding="utf-8") for p in sorted((SKILL_ROOT / "tests").glob("test_*.py"))
        )
        for rule in RULES:
            for test_name in rule.tests:
                self.assertIn(f"def {test_name}", test_sources, f"{rule.rule_id}: {test_name}")

    def test_registry_reference_anchors_exist(self):
        for rule in RULES:
            for reference in rule.references:
                self.assertTrue((SKILL_ROOT / "references" / reference).is_file(),
                                f"{rule.rule_id}: {reference}")

    def test_registry_skill_anchors_exist(self):
        for rule in RULES:
            match = re.match(r"§(\d+(?:\.\d+)?)", rule.skill)
            self.assertIsNotNone(match, f"{rule.rule_id}: {rule.skill}")
            number = match.group(1)
            self.assertTrue(re.search(rf"^#+\s*{re.escape(number)}[\.\s]", SKILL_MD, re.MULTILINE),
                            f"{rule.rule_id}: SKILL.md 缺少 {number} 节")

class SkillFrontmatterTests(unittest.TestCase):
    def _field(self, key: str) -> str:
        match = re.search(rf"^\s*{key}: ?(.*)$", SKILL_MD, re.MULTILINE)
        return match.group(1).strip().strip('"') if match else ""

    def test_frontmatter_has_required_fields(self):
        self.assertEqual(self._field("name"), "anti-ai-slop")
        self.assertTrue(self._field("description"))
        self.assertTrue(self._field("version"))

    def test_description_mentions_exclusions(self):
        description = self._field("description")
        for needle in ("不用于纯翻译", "简单事实查询"):
            self.assertIn(needle, description)

    def test_description_is_within_limit(self):
        self.assertLessEqual(len(self._field("description")), 1024)

class ReferenceRoutingTests(unittest.TestCase):
    def test_every_reference_file_is_routed_from_skill(self):
        for path in sorted((SKILL_ROOT / "references").glob("*.md")):
            self.assertIn(f"references/{path.name}", SKILL_MD, path.name)

    def test_routed_references_exist(self):
        for match in re.findall(r"references/([a-z-]+\.md)", SKILL_MD):
            self.assertTrue((SKILL_ROOT / "references" / match).is_file(), match)

    def test_profiles_are_documented_consistently(self):
        self.assertEqual(set(PROFILES), {"general", "zh-doc"})
        self.assertIn("zh-doc", SKILL_MD)
        self.assertIn("zh-doc", README_MD)

    def test_zh_doc_pack_documentation_matches_code(self):
        self.assertEqual(PROFILES["zh-doc"]["langs"], ("zh",))
        self.assertIn("en 包", SKILL_MD)

class DocumentedCommandTests(unittest.TestCase):
    KNOWN_FLAGS = {action.option_strings[0] for action in build_parser()._actions
                   if action.option_strings}

    def _bash_commands(self, text: str) -> list[str]:
        commands = []
        for block in re.findall(r"```(?:bash|sh)?\n(.*?)```", text, re.DOTALL):
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("python scripts/anti_slop_lint.py"):
                    commands.append(line)
        return commands

    def test_readme_and_skill_commands_only_use_known_flags(self):
        for source, text in (("README.md", README_MD), ("SKILL.md", SKILL_MD)):
            for command in self._bash_commands(text):
                with self.subTest(source=source, command=command):
                    for token in command.split():
                        if token.startswith("--"):
                            self.assertIn(token, self.KNOWN_FLAGS, f"{source}: {token}")

    def test_documented_language_choices_exist(self):
        parser = build_parser()
        lang_option = next(a for a in parser._actions if "--lang" in a.option_strings)
        documented = set(re.findall(r"`--lang (de|[a-z]{2})`", README_MD + SKILL_MD))
        self.assertTrue(documented <= set(lang_option.choices), documented - set(lang_option.choices))

class CorpusFilePresenceTests(unittest.TestCase):
    def test_corpus_manifest_covers_all_files(self):
        import json
        manifest = json.loads((SKILL_ROOT / "tests" / "corpus" / "manifest.json").read_text(encoding="utf-8"))
        for sub in ("good", "bad"):
            on_disk = {p.name for p in (SKILL_ROOT / "tests" / "corpus" / sub).glob("*.md")}
            self.assertEqual(on_disk, set(manifest[sub]), sub)

    def test_bad_manifest_entries_have_expected_rules(self):
        import json
        manifest = json.loads((SKILL_ROOT / "tests" / "corpus" / "manifest.json").read_text(encoding="utf-8"))
        for name, entry in manifest["bad"].items():
            self.assertTrue(entry["expected"], name)
            self.assertTrue(set(entry["expected"]) <= LINTER_RULE_IDS | set(entry.get("zh_doc_expected", [])),
                            name)
