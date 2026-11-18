from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import (
    ALL_LANGS, LANG_PACKS, PROFILES, count_east_asian, count_hangul, count_kana,
    detect_language, main, measure, parity_findings, prose_text, read_lines,
    scan_file, split_sentences,
)

CORPUS = Path(__file__).resolve().parent / "corpus"
LIMITS = {
    "general": {"max_line": 140, "max_sentence": 90, "max_paragraph": 8},
    "zh-doc": {"max_line": 120, "max_sentence": 40, "max_paragraph": 4},
}

def scan_text(text: str, profile: str = "general", **overrides):
    limits = dict(LIMITS[profile])
    limits.update(overrides)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        path.write_text(text, encoding="utf-8")
        return scan_file(path, profile=profile, **limits)

def categories(text: str, profile: str = "general", **overrides) -> set[str]:
    return {f.category for f in scan_text(text, profile, **overrides)}

def scan_path(path: Path, profile: str = "general"):
    return scan_file(path, profile=profile, **LIMITS[profile])

class GeneralDetectionTests(unittest.TestCase):
    def test_thinking_leak(self):
        self.assertIn("thinking-leak", categories("让我先检查项目结构。\n"))
        self.assertIn("thinking-leak", categories("用户想要的是快速响应。\n"))
        self.assertNotIn("thinking-leak", categories("需求分析：用户要求的是导出 CSV 格式。\n"))

    def test_meta_commentary(self):
        self.assertIn("meta", categories("本文档旨在介绍安装流程。\n"))
        self.assertIn("meta", categories("本文将带你探索底层机制。\n"))

    def test_filler(self):
        self.assertIn("filler", categories("值得注意的是，这个选项会覆盖默认配置。\n"))
        self.assertIn("filler", categories("显而易见，此处的参数必须为正数。\n"))
        self.assertIn("filler", categories("保证数据一致性至关重要。\n"))

    def test_chinese_filler_expansion(self):
        for phrase in (
            "需要注意的是，这个选项会覆盖默认配置。\n",
            "正如文档所说，这个参数可选。\n",
            "更重要的是，这会增加延迟。\n",
            "不仅如此，它还支持热更新。\n",
            "这项改动焕发出新的活力。\n",
            "毋庸置疑，这是最高效的实现。\n",
        ):
            with self.subTest(phrase=phrase.strip()):
                self.assertIn("filler", categories(phrase))

    def test_english_filler_blacklist(self):
        for phrase in (
            "Let us delve into the kernel scheduler.\n",
            "This is a cutting-edge solution.\n",
            "It provides seamless integration.\n",
            "The robust platform handles traffic.\n",
            "Needless to say, caching helps.\n",
            "You will find that this works.\n",
            "It is important to note that caching helps.\n",
            "At its core, it is a cache.\n",
            "This is a testament to good design.\n",
            "As technology continues to evolve, we adapt.\n",
            "In today's fast-paced digital world, speed matters.\n",
        ):
            with self.subTest(phrase=phrase.strip()):
                self.assertIn("filler", categories(phrase))

    def test_robust_with_statistical_bounds_is_allowed(self):
        for phrase in (
            "Use a robust estimator with bounded variance.\n",
            "The test checks robust error bounds.\n",
            "Provide robust outlier handling.\n",
        ):
            with self.subTest(phrase=phrase.strip()):
                self.assertNotIn("filler", categories(phrase))

    def test_ai_persona_is_meta(self):
        for phrase in (
            "As an AI language model, I suggest checking logs.\n",
            "作为一个AI助手，建议先重启服务。\n",
            "本文将带你探索底层机制。\n",
        ):
            with self.subTest(phrase=phrase.strip()):
                self.assertIn("meta", categories(phrase))

    def test_overclaim(self):
        self.assertIn("overclaim", categories("这个方案可以百分之百保证稳定。\n"))

    def test_closer(self):
        self.assertIn("closer", categories("希望本文对你有所帮助，如有疑问欢迎随时交流。\n"))
        self.assertIn("closer", categories("相信你已经掌握了核心原理。\n"))

    def test_long_line(self):
        self.assertIn("long-line", categories("A" * 160 + "\n"))

    def test_long_sentence(self):
        self.assertIn("long-sentence", categories("A" * 100 + " b.\n"))

    def test_long_paragraph(self):
        body = "\n".join(f"第 {n} 行正文，内容各不相同。" for n in range(10))
        self.assertIn("long-paragraph", categories(body + "\n"))

    def test_repeated_line(self):
        phrase = "这是足够长的重复内容用来验证检测是否生效第一段文字在这里"
        self.assertIn("repeated-line", categories(f"{phrase}\n\n{phrase}\n"))

    def test_short_chinese_repeated_line(self):
        phrase = "配置加载失败时立即退出进程。"
        self.assertIn("repeated-line", categories(f"{phrase}\n\n{phrase}\n"))

    def test_repeated_line_ignores_inline_code_difference(self):
        line = "这是足够长的重复内容用来验证检测是否生效第一段 {} 在这里"
        text = line.format("`a`") + "\n\n" + line.format("`b`") + "\n"
        self.assertIn("repeated-line", categories(text))

class ZhDocDetectionTests(unittest.TestCase):
    def test_conversational(self):
        self.assertIn("conversational", categories("其实，这个方案更适合当前项目。\n", "zh-doc"))
        self.assertIn("conversational", categories("你会发现这个选项很有用。\n", "zh-doc"))
        self.assertIn("conversational", categories("说白了，就是缓存。\n", "zh-doc"))

    def test_contrast(self):
        self.assertIn("contrast", categories("这不是终点，而是起点。\n", "zh-doc"))
        self.assertIn("contrast", categories("它并非替代品而是升级版。\n", "zh-doc"))

    def test_contrast_allows_diagnostic_root_cause(self):
        for text in (
            "这不是网络故障，而是权限配置错误。\n",
            "这不是性能问题，而是设计缺陷。\n",
        ):
            with self.subTest(text=text.strip()):
                self.assertNotIn("contrast", categories(text, "zh-doc"))

    def test_buzzword(self):
        self.assertIn("buzzword", categories("开箱即用，无需配置。\n", "zh-doc"))
        self.assertIn("buzzword", categories("这套方案助力团队提效。\n", "zh-doc"))

    def test_buzzword_allows_factual_zero_config(self):
        self.assertNotIn("buzzword", categories("系统提供了开箱即用的默认配置。\n", "zh-doc"))

    def test_exclamation_flagged_in_zh_doc(self):
        text = "部署完成，直接开始使用吧！\nRun the setup script!\n"
        lines = {f.line for f in scan_text(text, "zh-doc") if f.category == "exclamation"}
        self.assertEqual(lines, {1, 2})

    def test_exclamation_not_flagged_in_code_span(self):
        self.assertNotIn("exclamation", categories("判断不等用 `a != b` 表示。\n", "zh-doc"))

    def test_exclamation_not_flagged_in_image_alt(self):
        self.assertNotIn("exclamation", categories("![Logo](https://example.com/logo.png)\n", "zh-doc"))

    def test_exclamation_only_in_zh_doc_profile(self):
        self.assertNotIn("exclamation", categories("部署完成，直接开始使用吧！\n", "general"))

    def test_sentence_budget_is_40_cjk(self):
        sentence = "这是一个包含超过四十个中文字符的句子用来验证中文文档模式的单句预算是否真的生效而不是默认的九十个字符测试用例"
        self.assertIn("long-sentence", categories(sentence + "\n", "zh-doc"))

    def test_paragraph_budget_is_4_lines(self):
        body = "\n".join(f"第 {n} 行正文，内容各不相同。" for n in range(5))
        self.assertIn("long-paragraph", categories(body + "\n", "zh-doc"))

class ProfileIsolationTests(unittest.TestCase):

    PROBE = "其实，说白了就是打造一套开箱即用的方案，助力团队提效。这不是终点，而是起点。\n"

    def test_general_has_no_zh_only_categories(self):
        found = categories(self.PROBE, "general")
        for category in ("conversational", "contrast", "buzzword"):
            self.assertNotIn(category, found, f"{category} 不应在 general 下启用")

    def test_zh_doc_enables_all_zh_only_categories(self):
        found = categories(self.PROBE, "zh-doc")
        for category in ("conversational", "contrast", "buzzword"):
            self.assertIn(category, found, f"{category} 应在 zh-doc 下启用")

    def test_general_has_no_readme_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("\n".join(f"第 {n} 段说明文字，用于验证预算检查。" for n in range(140)), encoding="utf-8")
            found = {f.category for f in scan_path(path, "general")}
            self.assertNotIn("readme-line-budget", found)

    def test_zh_doc_enforces_readme_line_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("\n".join(f"第 {n} 段。" for n in range(130)), encoding="utf-8")
            found = {f.category for f in scan_path(path, "zh-doc")}
            self.assertIn("readme-line-budget", found)

    def test_zh_doc_enforces_readme_char_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("\n".join(["中文说明文字" * 3 for _ in range(80)]), encoding="utf-8")
            found = {f.category for f in scan_path(path, "zh-doc")}
            self.assertIn("readme-char-budget", found)

    def test_budget_does_not_apply_to_usage_guide_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "USAGE.md"
            path.write_text("\n".join(f"第 {n} 段。" for n in range(130)), encoding="utf-8")
            self.assertNotIn("readme-line-budget", {f.category for f in scan_path(path, "zh-doc")})

    def test_budget_does_not_apply_to_other_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "architecture.md"
            path.write_text("\n".join(f"第 {n} 段。" for n in range(130)), encoding="utf-8")
            self.assertNotIn("readme-line-budget", {f.category for f in scan_path(path, "zh-doc")})

class LengthFalsePositiveTests(unittest.TestCase):
    def test_inline_code_embedded_in_prose_is_excluded(self):
        self.assertNotIn("long-line", categories(f"普通文字 `{'x' * 200}` 后文\n", max_line=80))

    def test_whole_line_inline_code_is_excluded(self):
        self.assertNotIn("long-line", categories(f"`{'x' * 220}`\n", max_line=80))

    def test_multiple_inline_code_spans_are_excluded(self):
        text = f"`{'a' * 100}` 和 `{'b' * 100}` 中间\n"
        self.assertNotIn("long-line", categories(text, max_line=80))

    def test_multi_backtick_span_with_inner_backtick_is_excluded(self):
        text = "示例 ``" + "x" * 100 + "`" + "y" * 100 + "`` 结束\n"
        self.assertNotIn("long-line", categories(text, max_line=80))

    def test_reference_link_definition_is_not_measured(self):
        url = "https://example.com/" + "segment/" * 25
        self.assertNotIn("long-line", categories(f"[cfg]: {url}\n", max_line=80))
        self.assertNotIn("long-sentence", categories(f"[cfg]: {url}\n", max_line=80))

    def test_inline_code_does_not_inflate_sentence(self):
        self.assertNotIn("long-sentence", categories(f"前缀 `{'y' * 200}`。\n", max_sentence=40))

    def test_table_rows_are_not_measured(self):
        self.assertNotIn("long-line", categories(f"| {'x' * 200} | b |\n", max_line=80))

    def test_headings_are_not_measured(self):
        self.assertNotIn("long-line", categories(f"# {'x' * 200}\n", max_line=80))

    def test_list_items_are_not_measured(self):
        self.assertNotIn("long-sentence", categories(f"- {'工' * 60}\n", "zh-doc"))
        self.assertNotIn("long-line", categories(f"- {'x' * 200}\n", max_line=80))

    def test_paragraphs_are_still_measured(self):
        self.assertIn("long-sentence", categories(f"{'工' * 60}\n", "zh-doc"))

    def test_english_period_splits(self):
        line = "Alpha beta gamma delta epsilon zeta eta theta. Iota kappa lambda mu nu xi omicron pi rho tau.\n"
        self.assertNotIn("long-sentence", categories(line, max_sentence=60))

    def test_abbreviations_do_not_split(self):
        for text in (
            "Dr. Smith reviewed the API. It passed the local check.\n",
            "Use e.g. this one. Then stop.\n",
            "The cutoff is i.e. midnight. Then restart.\n",
        ):
            self.assertNotIn("long-sentence", categories(text, max_sentence=45), text)

    def test_versions_do_not_split(self):
        self.assertNotIn("long-sentence", categories("Upgrade from 1.9.8 to 2.1.0 then verify.\n", max_sentence=45))

    def test_latin_sentence_is_not_measured_by_cjk_budget(self):
        text = "The pool opens connections lazily and closes them after a timeout.\n"
        self.assertNotIn("long-sentence", categories(text, "zh-doc"))

class IgnoreRegexTests(unittest.TestCase):
    def test_skips_length_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("IGNORE " + "长" * 200 + "\n", encoding="utf-8")
            self.assertEqual(main(["--max-line", "40", "--max-sentence", "40",
                                   "--ignore-regex", "^IGNORE", str(path)]), 0)

    def test_skips_pattern_checks(self):
        text = "SKIP 值得注意的是这一句。\n"
        found = scan_file(self._write(text), profile="general",
                          extra_ignore=re.compile(r"^SKIP"), **LIMITS["general"])
        self.assertEqual(found, [])

    def _write(self, text: str) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        path = Path(self._tmp.name) / "sample.md"
        path.write_text(text, encoding="utf-8")
        return path

class WeRuleTests(unittest.TestCase):

    ALLOWED = (
        "我们建议在生产环境关闭该选项。\n",
        "我们可以从日志中看到请求被拒绝。\n",
        "我们的实现依赖标准库。\n",
        "如果我们禁用校验，性能会提升。\n",
        "我们使用这个方案。\n",
        "我们可以看到效果。\n",
        "我们还需进一步验证。\n",
        "我们不仅要快，还要稳。\n",
        "假如我们改变设计，接口会变。\n",
        "我们不建议这样做。\n",
    )

    FLAGGED = (
        "我们相信这套方案是最佳选择。\n",
        "我们认为这是正确的做法。\n",
        "我们打造了一套优雅的方案。\n",
    )

    def test_normal_usage_is_not_flagged(self):
        for text in self.ALLOWED:
            with self.subTest(text=text.strip()):
                self.assertNotIn("conversational", categories(text, "zh-doc"))

    def test_unsupported_assertions_are_flagged(self):
        for text in self.FLAGGED:
            with self.subTest(text=text.strip()):
                self.assertIn("conversational", categories(text, "zh-doc"))

class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))

    def test_good_corpus_present(self):
        self.assertEqual({p.name for p in (CORPUS / "good").glob("*.md")},
                         set(self.manifest["good"]))

    def test_bad_corpus_present(self):
        self.assertEqual({p.name for p in (CORPUS / "bad").glob("*.md")},
                         set(self.manifest["bad"]))

    def test_good_corpus_zero_findings_general(self):
        for path in sorted((CORPUS / "good").glob("*.md")):
            with self.subTest(path=path.name):
                self.assertEqual([f.category for f in scan_path(path, "general")], [], path.name)

    def test_good_corpus_zero_findings_zh_doc(self):
        for path in sorted((CORPUS / "good").glob("*.md")):
            with self.subTest(path=path.name):
                self.assertEqual([f.category for f in scan_path(path, "zh-doc")], [], path.name)

    def test_bad_corpus_flagged_general(self):
        for path in sorted((CORPUS / "bad").glob("*.md")):
            with self.subTest(path=path.name):
                self.assertTrue(scan_path(path, "general"), path.name)

    def test_bad_corpus_flagged_zh_doc(self):
        for path in sorted((CORPUS / "bad").glob("*.md")):
            if path.name.startswith(("zh-", "README")):
                with self.subTest(path=path.name):
                    self.assertTrue(scan_path(path, "zh-doc"), path.name)

    def test_zh_doc_loads_english_beside_chinese(self):
        for name in ("en-filler.md", "en-meta-closer.md"):
            path = CORPUS / "bad" / name
            with self.subTest(path=name):
                found = {f.category for f in scan_path(path, "zh-doc")}
                self.assertTrue({"filler", "closer", "meta"} & found, name)

    def test_zh_doc_does_not_load_non_english_packs(self):
        for name in ("ja-filler.md", "ko-filler.md", "de-filler.md", "fr-filler.md", "es-filler.md"):
            path = CORPUS / "bad" / name
            with self.subTest(path=name):
                found = {f.category for f in scan_path(path, "zh-doc")}
                self.assertFalse({"filler", "closer"} & found, name)

class BudgetTests(unittest.TestCase):
    def test_readme_name_variants_match(self):
        from scripts.anti_slop_lint import is_readme
        for name in ("README.md", "readme.md", "README-zh.md", "README_ja.md"):
            self.assertTrue(is_readme(Path(name)), name)

    def test_non_readme_names_do_not_match(self):
        from scripts.anti_slop_lint import is_readme
        for name in ("architecture.md", "notes.md", "CHANGELOG.md", "guidetest.md",
                     "USAGE.md", "INSTALL.md", "getting-started.md", "quickstart.md"):
            self.assertFalse(is_readme(Path(name)), name)

class FrontmatterTests(unittest.TestCase):
    def test_yaml_frontmatter_is_skipped(self):
        text = (
            "---\n"
            "name: demo\n"
            f"description: {'很长的描述' * 40}\n"
            "---\n"
            "\n"
            "正文第一段。\n"
        )
        self.assertEqual([f.category for f in scan_text(text, "zh-doc")], [])

    def test_body_after_frontmatter_is_still_scanned(self):
        text = "---\nname: demo\n---\n\n值得注意的是这一句。\n"
        self.assertIn("filler", categories(text, "general"))

    def test_unterminated_frontmatter_is_not_treated_as_frontmatter(self):
        text = "---\nname: demo\n\n值得注意的是这一句。\n"
        self.assertIn("filler", categories(text, "general"))

class CliTests(unittest.TestCase):
    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("值得注意的是这一句。\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "scripts" / "anti_slop_lint.py"), "--json", str(path)],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["files_scanned"], 1)
            self.assertEqual(payload["profile"], "general")
            self.assertGreaterEqual(payload["finding_count"], 1)

    def test_strict_returns_one_on_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("值得注意的是这一句。\n", encoding="utf-8")
            self.assertEqual(main(["--strict", str(path)]), 1)

    def test_strict_returns_zero_on_clean_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("该命令读取配置文件，并在校验失败时返回非零状态。\n", encoding="utf-8")
            self.assertEqual(main(["--strict", str(path)]), 0)

    def test_profiles_registered(self):
        self.assertEqual(set(PROFILES), {"general", "zh-doc"})

    def test_zh_doc_profile_changes_defaults(self):
        self.assertEqual(PROFILES["zh-doc"]["max_sentence"], 40)
        self.assertEqual(PROFILES["zh-doc"]["max_paragraph"], 4)
        self.assertEqual(PROFILES["general"]["max_sentence"], 90)
        self.assertEqual(PROFILES["general"]["max_paragraph"], 8)

def categories_lang(text: str, lang: str, profile: str = "general") -> set[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        path.write_text(text, encoding="utf-8")
        return {f.category for f in scan_file(path, profile=profile, lang=lang, **LIMITS[profile])}

def detect(text: str) -> str:
    return detect_language(prose_text(text.splitlines()))

class LanguagePackTests(unittest.TestCase):
    HITS = {
        "zh": (
            ("filler", "值得注意的是，这个选项会覆盖默认配置。\n"),
            ("meta", "本文档旨在介绍安装流程。\n"),
            ("closer", "感谢阅读，如有疑问欢迎随时交流。\n"),
            ("overclaim", "这个方案可以百分之百保证稳定。\n"),
        ),
        "en": (
            ("filler", "It is important to note that caching helps.\n"),
            ("meta", "This document aims to describe the cache.\n"),
            ("closer", "Hope this helps, and let me know if it fails.\n"),
            ("overclaim", "The retry logic is guaranteed to never lose a job.\n"),
            ("thinking-leak", "Let me first inspect the project layout.\n"),
        ),
        "ja": (
            ("filler", "言うまでもなく、設定の確認は重要です。\n"),
            ("meta", "AI言語モデルとして、確認をお勧めします。\n"),
            ("closer", "お役に立てれば幸いです。\n"),
            ("overclaim", "この方法なら完全に防げます。\n"),
        ),
        "ko": (
            ("filler", "말할 필요도 없이 설정 확인이 중요합니다.\n"),
            ("meta", "AI 언어 모델로서 확인을 권장합니다.\n"),
            ("closer", "도움이 되셨기를 바랍니다.\n"),
            ("overclaim", "이 방법은 완벽하게 방지합니다.\n"),
        ),
        "de": (
            ("filler", "Es ist wichtig zu beachten, dass der Port frei sein muss.\n"),
            ("meta", "Als KI-Sprachmodell empfehle ich einen Neustart.\n"),
            ("closer", "Ich hoffe, das hilft. Vielen Dank fürs Lesen.\n"),
            ("overclaim", "Das Verfahren ist garantiert fehlerfrei und risikofrei.\n"),
        ),
        "fr": (
            ("filler", "Il est important de noter que le port doit être libre.\n"),
            ("meta", "En tant que modèle de langage, je conseille un redémarrage.\n"),
            ("closer", "J'espère que cela vous aide. N'hésitez pas à me contacter.\n"),
            ("overclaim", "La méthode est infaillible et sans aucun risque.\n"),
        ),
        "es": (
            ("filler", "Es importante señalar que el puerto debe estar libre.\n"),
            ("meta", "Como modelo de lenguaje, recomiendo reiniciar.\n"),
            ("closer", "Espero que esto te ayude. No dudes en contactar con nosotros.\n"),
            ("overclaim", "El método es infalible y tiene riesgo cero.\n"),
        ),
    }

    LEGITIMATE = {
        "zh": ("该函数保证返回值按插入顺序排列。\n",),
        "en": ("The function guarantees insertion order for the returned items.\n",),
        "ja": (
            "設定ファイルを読み込みます。\n",
            "注意すべき点は、再起動が必要なことです。\n",
            "完全に一致する場合だけ置換します。\n",
        ),
        "ko": (
            "결론은 아래 표에 있습니다.\n",
            "이 문서는 설정 파일 형식을 정의합니다.\n",
        ),
        "de": (
            "Die Funktion garantiert die Reihenfolge der Einträge.\n",
            "Es ist wichtig, dass der Port frei ist.\n",
            "Der Schätzer ist robust gegenüber Ausreißern.\n",
        ),
        "fr": (
            "Les heures de pointe sont exclues du calcul.\n",
            "Il est important que le port soit libre.\n",
            "N'hésitez pas à utiliser l'option --force pour écraser le fichier.\n",
        ),
        "es": (
            "La función garantiza el orden de los elementos.\n",
            "Es importante que el puerto esté libre.\n",
            "Para profundizar en el tema, vea la sección 3.\n",
        ),
    }

    def test_every_covered_language_has_every_core_category(self):
        for lang, cases in self.HITS.items():
            self.assertTrue({"filler", "meta", "closer", "overclaim"} <= {c for c, _ in cases}, lang)

    def test_each_language_hits_its_own_patterns(self):
        for lang, cases in self.HITS.items():
            for category, text in cases:
                with self.subTest(lang=lang, category=category):
                    self.assertIn(category, categories(text, "general"))
                    self.assertIn(category, categories_lang(text, lang))

    def test_each_language_spares_legitimate_expressions(self):
        for lang, texts in self.LEGITIMATE.items():
            for text in texts:
                with self.subTest(lang=lang, text=text.strip()):
                    self.assertEqual(categories(text, "general") & {"filler", "meta", "closer", "overclaim"}, set())

    def test_every_covered_language_has_a_pack(self):
        for lang in ("zh", "en", "ja", "ko", "de", "fr", "es"):
            self.assertTrue(LANG_PACKS[lang], lang)

    def test_uncovered_languages_have_empty_packs(self):
        self.assertEqual(LANG_PACKS["ru"], ())
        self.assertEqual(LANG_PACKS["pt"], ())
        self.assertEqual(categories_lang("Гарантия 100% на все случаи.\n", "ru"), {"overclaim"})

    def test_universal_pack_applies_in_every_language(self):
        for lang in ALL_LANGS:
            with self.subTest(lang=lang):
                self.assertIn("overclaim", categories_lang("Uptime 100% over the whole year.\n", lang))

    def test_profiles_expose_language_sets(self):
        self.assertEqual(PROFILES["zh-doc"]["langs"], ("zh",))
        self.assertEqual(set(PROFILES["general"]["langs"]), set(LANG_PACKS) - {"universal"})

class LanguageDetectionTests(unittest.TestCase):
    SAMPLES = {
        "zh": "程序从配置文件读取设置。缺少必填字段时返回非零状态码。\n",
        "ja": "プログラムは設定ファイルから値を読み込みます。必須項目がない場合は停止します。\n",
        "ko": "프로그램은 설정 파일에서 값을 읽습니다. 필수 항목이 없으면 멈춥니다.\n",
        "ru": "Программа читает настройки из файла. Если поле отсутствует, она завершается с ошибкой.\n",
        "en": "The program reads its settings from a file and stops when a required field is missing.\n",
        "de": "Das Programm liest die Einstellungen aus einer Datei und endet, wenn ein Pflichtfeld fehlt.\n",
        "fr": "Le programme lit ses réglages dans un fichier et s'arrête quand un champ obligatoire manque.\n",
        "es": "El programa lee su configuración desde un archivo y termina si falta un campo obligatorio.\n",
        "pt": "O programa lê as configurações de um arquivo e você também pode alterar o valor se quiser.\n",
    }

    def test_each_language_is_detected(self):
        for lang, text in self.SAMPLES.items():
            with self.subTest(lang=lang):
                self.assertEqual(detect(text), lang)

    def test_japanese_with_kanji_is_not_chinese(self):
        self.assertEqual(detect("設定の読み込みに失敗したら終了する。\n"), "ja")

    def test_chinese_with_one_kana_word_stays_chinese(self):
        self.assertEqual(detect("配置文件由 カタカナ 工具生成，程序启动时读取并校验全部字段内容。\n"), "zh")

    def test_spanish_marks_decide_short_text(self):
        self.assertEqual(detect("¿Qué hace? ¡Nada!\n"), "es")

    def test_empty_and_symbol_only_default_to_english(self):
        self.assertEqual(detect(""), "en")
        self.assertEqual(detect("---\n12345\n"), "en")

    def test_corpus_files_detect_as_their_filename_language(self):
        for sub in ("good", "bad"):
            for path in sorted((CORPUS / sub).glob("*.md")):
                lang = path.name.split("-")[0]
                if lang in ALL_LANGS:
                    with self.subTest(path=f"{sub}/{path.name}"):
                        self.assertEqual(detect_language(prose_text(read_lines(path))), lang)

    def test_code_blocks_and_inline_code_do_not_decide_language(self):
        text = "说明。\n\n```python\n" + "def load_configuration_from_file(path): return open(path).read()\n" * 20 + "```\n"
        self.assertEqual(detect(text), "zh")
        text = "配置 `load_configuration_from_file_with_a_long_name_and_many_english_words` 后重启。\n"
        self.assertEqual(detect(text), "zh")

    def test_frontmatter_and_urls_do_not_decide_language(self):
        text = "---\ndescription: use this skill when writing documentation for the project\n---\n\n配置见 https://example.com/docs/configuration/reference/page 页面。\n"
        self.assertEqual(detect(text), "zh")

class ForcedLanguageTests(unittest.TestCase):
    ENGLISH_IN_CHINESE = "该工具读取配置并校验字段，校验失败时返回非零状态码。\n\nThe loader is seamless and at its core a parser.\n"

    def test_auto_follows_dominant_language(self):
        self.assertIn("filler", categories(self.ENGLISH_IN_CHINESE, "general"))

    def test_english_pack_does_not_apply_to_pure_english_zh_doc_target(self):
        self.assertNotIn(
            "conversational",
            categories("The tool reads config and validates fields.\n", "general"),
        )

    def test_forced_language_overrides_detection(self):
        self.assertIn("filler", categories_lang(self.ENGLISH_IN_CHINESE, "en"))

    def test_forced_language_ignores_other_packs(self):
        self.assertNotIn("filler", categories_lang("值得注意的是，这个选项会覆盖默认配置。\n", "en"))

    def test_forced_language_can_be_zh_doc_zh(self):
        self.assertIn("conversational", categories_lang("其实，这个方案更适合当前项目。\n", "zh", "zh-doc"))

    def test_zh_doc_rejects_other_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("設定を読み込みます。\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                scan_file(path, profile="zh-doc", lang="ja", **LIMITS["zh-doc"])
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main(["--profile", "zh-doc", "--lang", "ja", str(path)]), 2)
            self.assertIn("zh-doc", err.getvalue())

    def test_unknown_language_is_rejected_by_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("text\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                main(["--lang", "xx", str(path)])
            self.assertEqual(ctx.exception.code, 2)

    def test_zh_doc_auto_on_other_language_loads_universal_only(self):
        german = "Es ist wichtig zu beachten, dass der Port frei sein muss. Das Verfahren ist 100% sicher.\n"
        found = categories(german, "zh-doc")
        self.assertNotIn("filler", found)
        self.assertIn("overclaim", found)

    def test_cli_json_reports_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("設定を読み込みます。失敗したら終了します。\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main(["--json", str(path)])
            self.assertEqual(json.loads(out.getvalue())["languages"], {str(path): "ja"})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main(["--json", "--lang", "de", str(path)])
            self.assertEqual(json.loads(out.getvalue())["languages"], {str(path): "de"})

class MixedLanguageTests(unittest.TestCase):
    def test_chinese_readme_with_english_terms_and_code_is_clean(self):
        text = (
            "# cursor-tool\n\n"
            "命令行光标主题管理器，支持 Wayland 与 X11。\n\n"
            "```bash\ncursor-tool apply Bibata --seamless --robust\n```\n\n"
            "配置项 `seamless_mode` 与 `robust` 默认关闭，见 [docs](https://example.com/seamless/robust)。\n"
        )
        self.assertEqual(scan_text(text, "zh-doc"), [])
        self.assertEqual(scan_text(text, "general"), [])

    def test_english_doc_quoting_chinese_is_not_judged_by_chinese_rules(self):
        text = "The Chinese opener 值得注意的是 is a common filler in translated text.\n"
        self.assertEqual(detect(text), "en")
        self.assertNotIn("filler", categories(text, "general"))

    def test_french_doc_with_english_terms_stays_french(self):
        text = "Le pool utilise un cache seamless et un robust parser pour les requêtes dans la file.\n"
        self.assertEqual(detect(text), "fr")
        self.assertNotIn("filler", categories(text, "general"))

    def test_chinese_doc_with_english_slop_is_flagged(self):
        text = "# 部署\n\n本项目提供 seamless 集成，delve into 细节见下。\n"
        self.assertIn("filler", categories(text, "general"))
        self.assertIn("filler", categories(text, "zh-doc"))

class ExemptPhraseTests(unittest.TestCase):

    def test_adjective_with_concrete_noun_is_clean(self):
        for text in (
            "最先端の技術を使って実装しています。\n",
            "シームレスな統合を実現します。\n",
            "Die nahtlose Migration verläuft ohne Ausfall.\n",
            "Eine hochmoderne Anlage wurde installiert.\n",
            "Un assemblage sans couture de deux pièces.\n",
            "Tecnología de vanguardia en el sector.\n",
            "최첨단 기술을 사용합니다.\n",
        ):
            with self.subTest(text=text.strip()):
                self.assertNotIn("filler", categories(text, "general"))

    def test_bare_adjective_is_still_flagged(self):
        for text in (
            "最先端のアプローチ。\n",
            "シームレスに動作します。\n",
            "Die Verbindung erfolgt nahtlos.\n",
            "Eine hochmoderne Lösung.\n",
            "La transition est sans couture.\n",
            "Una solución de vanguardia.\n",
            "혁신적인 접근 방식을 사용합니다.\n",
        ):
            with self.subTest(text=text.strip()):
                self.assertIn("filler", categories(text, "general"))

    def test_japanese_support_closing_is_not_a_closer(self):
        self.assertNotIn(
            "closer",
            categories("ご不明な点があれば、お気軽にお問い合わせください。\n", "general"),
        )

    def test_japanese_marketing_closing_is_a_closer(self):
        self.assertIn(
            "closer",
            categories("ご不明な点がございましたら、お気軽にお問い合わせください。\n", "general"),
        )

class UrlExemptionTests(unittest.TestCase):
    def test_link_target_is_not_scanned(self):
        self.assertEqual(categories("见 [docs](https://example.com/seamless/robust)。\n"), set())

    def test_bare_url_is_not_scanned(self):
        self.assertEqual(categories("见 https://example.com/seamless 这个链接。\n"), set())

    def test_link_anchor_text_is_still_scanned(self):
        self.assertIn("filler", categories("[seamless integration](https://a.com/x) 是卖点。\n"))

    def test_english_sentence_inside_chinese_doc_uses_latin_budget(self):
        text = "该模块负责连接管理。\n\nThe pool opens connections lazily and closes them after a timeout.\n"
        self.assertNotIn("long-sentence", categories(text, "zh-doc"))

class SentenceAndCountTests(unittest.TestCase):
    def test_japanese_period(self):
        self.assertEqual(split_sentences("設定を読み込む。失敗したら終了する。"), ["設定を読み込む。", "失敗したら終了する。"])

    def test_korean_period(self):
        self.assertEqual(split_sentences("설정을 읽습니다. 실패하면 종료합니다."), ["설정을 읽습니다.", "실패하면 종료합니다."])

    def test_french_guillemets_protect_inner_periods(self):
        self.assertEqual(
            split_sentences("Il écrit « Non. Jamais. » puis il part. Elle reste."),
            ["Il écrit « Non. Jamais. » puis il part.", "Elle reste."],
        )

    def test_spanish_opening_marks_start_sentences(self):
        parts = split_sentences("¿Qué hace el pool? ¡Cierra las conexiones! Luego espera.")
        self.assertEqual(parts, ["¿Qué hace el pool?", "¡Cierra las conexiones!", "Luego espera."])

    def test_spanish_mid_sentence_marks_do_not_split(self):
        self.assertEqual(len(split_sentences("Pregunta: ¿cómo se reinicia el servicio en producción")), 1)

    def test_german_abbreviations(self):
        parts = split_sentences("Das gilt z. B. für Logs, d. h. für alle. Es gilt u. a. auch hier. Danach endet es.")
        self.assertEqual(len(parts), 3)

    def test_german_ordinals(self):
        self.assertEqual(len(split_sentences("Am 3. Mai startet es. Danach endet es.")), 2)
        self.assertEqual(len(split_sentences("Es läuft vom 3. bis 5. Mai. Danach endet es.")), 2)

    def test_english_sentence_after_number_still_splits(self):
        self.assertEqual(len(split_sentences("Run step 3. Next, verify the output.")), 2)

    def test_russian_ellipsis_ends_sentence(self):
        self.assertEqual(
            split_sentences("Сервис не отвечает… Попробуйте позже. Всё."),
            ["Сервис не отвечает…", "Попробуйте позже.", "Всё."],
        )
        self.assertEqual(len(split_sentences("Подождите… и повторите запрос.")), 1)

    def test_script_counts(self):
        self.assertEqual(count_kana("設定ファイルは読む"), 6)
        self.assertEqual(count_hangul("설정 abc 읽기"), 4)
        self.assertEqual(count_east_asian("設定ファイル 설정 abc"), 8)

    def test_japanese_and_korean_use_wide_limits(self):
        japanese = "これは設定ファイルを読み込んでから値を検証し、失敗した場合は終了コードを返して停止する処理です。"
        self.assertGreater(count_east_asian(japanese), 40)
        self.assertNotIn("long-sentence", categories(japanese + "\n", "zh-doc"))
        chinese = "这是一个包含超过四十个中文字符的句子用来验证中文文档模式的单句预算是否真的生效而不是默认的九十个字符测试用例"
        self.assertIn("long-sentence", categories(chinese + "\n", "zh-doc"))
        self.assertEqual(measure(japanese, 40, 90), (2 * count_east_asian(japanese), 180))
        self.assertEqual(measure("설정" * 50 + "입니다.", 40, 90), (207, 180))
        self.assertIn("long-sentence", categories("설정" * 50 + "입니다.\n", "general"))

    def test_short_japanese_and_korean_repeats_are_flagged(self):
        for phrase in ("設定の読み込みに失敗したら終了する。", "설정 불러오기에 실패하면 종료합니다."):
            with self.subTest(phrase=phrase):
                self.assertIn("repeated-line", categories(f"{phrase}\n\n{phrase}\n"))

class LanguageCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))

    def test_every_required_language_has_two_good_and_two_bad_samples(self):
        for lang in ("zh", "en", "ja", "ko", "de", "fr", "es"):
            with self.subTest(lang=lang):
                self.assertGreaterEqual(len(list((CORPUS / "good").glob(f"{lang}-*.md"))), 2)
                self.assertGreaterEqual(len(list((CORPUS / "bad").glob(f"{lang}-*.md"))), 2)

    def test_bad_samples_hit_their_own_language_pack(self):
        pack_categories = {"filler", "meta", "closer", "overclaim", "thinking-leak"}
        for lang in ("zh", "en", "ja", "ko", "de", "fr", "es"):
            for path in sorted((CORPUS / "bad").glob(f"{lang}-*.md")):
                expected = set(self.manifest["bad"][path.name]["expected"]) & pack_categories
                if not expected:
                    continue
                with self.subTest(path=path.name):
                    found = {f.category for f in scan_path(path, "general")}
                    self.assertTrue(expected <= found, path.name)

    def test_good_samples_are_clean_with_forced_language(self):
        for lang in ("ja", "ko", "de", "fr", "es"):
            for path in sorted((CORPUS / "good").glob(f"{lang}-*.md")):
                with self.subTest(path=path.name):
                    with tempfile.TemporaryDirectory():
                        found = scan_file(path, profile="general", lang=lang, **LIMITS["general"])
                    self.assertEqual(found, [], path.name)

class ParityTests(unittest.TestCase):

    def parity(self, main_text: str, pair_text: str) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            main_path = Path(tmp) / "README.md"
            pair_path = Path(tmp) / "README.zh-CN.md"
            main_path.write_text(main_text, encoding="utf-8")
            pair_path.write_text(pair_text, encoding="utf-8")
            return parity_findings(main_path, pair_path)

    def parity_categories(self, main_text: str, pair_text: str) -> set[str]:
        return {f.category for f in self.parity(main_text, pair_text)}

    def test_prose_number_mismatch_flagged(self):
        main = "# Plugins\n\nThe repo ships 13 plugins, plus 15 more packages-only ones.\n"
        pair = "# 插件\n\n仓库自带 13 个插件，另有 18 款仅包声明插件。\n"
        self.assertIn("parity-number", self.parity_categories(main, pair))

    def test_matching_numbers_pass(self):
        main = "13 plugins, 30 rolling snapshots, 90% and 75% opacity.\n"
        pair = "13 个插件，30 份滚动快照，90% 与 75% 透明度。\n"
        self.assertEqual(self.parity(main, pair), [])

    def test_code_spans_and_fences_are_not_facts(self):
        main = "Run `slot 3 axis`:\n\n```bash\nnyxuri use kitty 42\n```\n"
        pair = "运行 `槽位 3 轴`：\n\n```bash\nnyxuri use kitty 7\n```\n"
        self.assertEqual(self.parity(main, pair), [])

    def test_heading_structure_mismatch_flagged(self):
        main = "# Install\n\n## AUR\n\n## Git\n"
        pair = "# 安装\n\n## AUR\n"
        self.assertIn("parity-heading", self.parity_categories(main, pair))

    def test_table_row_mismatch_flagged(self):
        main = "| c | d |\n| :--- | :--- |\n| `on` | enable |\n| `off` | disable |\n"
        pair = "| 指 | 用 |\n| :--- | :--- |\n| `on` | 启用 |\n"
        self.assertIn("parity-table", self.parity_categories(main, pair))

    def test_hint_names_the_pair_file(self):
        finding = self.parity("keep 30 snapshots\n", "保留 45 份快照\n")[0]
        self.assertIn("README.zh-CN.md", finding.hint)

    def test_cli_pair_end_to_end_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            main_path = Path(tmp) / "README.md"
            pair_path = Path(tmp) / "README.zh-CN.md"
            main_path.write_text("ships 13 plugins\n", encoding="utf-8")
            pair_path.write_text("共 13 个插件\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main([str(main_path), "--pair", str(pair_path), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(
                [f for f in payload["findings"] if f["category"].startswith("parity-")], [])

    def test_cli_pair_mismatch_is_strict_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            main_path = Path(tmp) / "README.md"
            pair_path = Path(tmp) / "README.zh-CN.md"
            main_path.write_text("ships 13 plugins\n", encoding="utf-8")
            pair_path.write_text("共 13 个插件，另有 18 款\n", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main([str(main_path), "--pair", str(pair_path), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            parity = [f for f in payload["findings"] if f["category"].startswith("parity-")]
            self.assertEqual({f["category"] for f in parity}, {"parity-number"})
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([str(main_path), "--pair", str(pair_path), "--strict"])
            self.assertEqual(code, 1)

    def test_cli_pair_rejects_missing_and_multi_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            main_path = Path(tmp) / "README.md"
            main_path.write_text("content\n", encoding="utf-8")
            other = Path(tmp) / "other.md"
            other.write_text("more content\n", encoding="utf-8")
            code = main([str(main_path), str(other), "--pair", str(main_path)])
            self.assertEqual(code, 2)
            code = main([str(main_path), "--pair", str(Path(tmp) / "missing.md")])
            self.assertEqual(code, 2)

if __name__ == "__main__":
    unittest.main()
