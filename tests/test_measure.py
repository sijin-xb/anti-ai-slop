"""Tests for the length counting standard (docs/linter.md).

The standard: East Asian chars (han/kana/hangul) weigh 2 half-width units,
CJK punctuation weighs 0 (inherited: a 40-han sentence ending in 。 passes),
everything else (Latin letters, digits, spaces, halfwidth punctuation)
weighs 1. Pure Latin text keeps the historic len() count; pure Chinese
keeps the historic han-only count. Mixed text counts both parts; the budget
follows the dominant script.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import (  # noqa: E402
    count_cjk, count_wide, measure, scan_file,
)

def scan_text(text: str, profile: str = "general", **overrides):
    limits = {"max_line": 140, "max_sentence": 90, "max_paragraph": 8}
    if profile == "zh-doc":
        limits = {"max_line": 120, "max_sentence": 40, "max_paragraph": 4}
    limits.update(overrides)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.md"
        path.write_text(text, encoding="utf-8")
        return scan_file(path, profile=profile, **limits)

def categories(text: str, profile: str = "general", **overrides) -> set[str]:
    return {f.category for f in scan_text(text, profile, **overrides)}

class PureTextBoundaryTests(unittest.TestCase):
    def test_pure_chinese_keeps_han_only_budget(self):
        self.assertEqual(measure("汉" * 40 + "。", 40, 90), (80, 80))
        self.assertNotIn("long-sentence", categories("汉" * 40 + "。\n", "zh-doc"))
        self.assertIn("long-sentence", categories("汉" * 41 + "。\n", "zh-doc"))
        self.assertNotIn("long-sentence", categories("汉" * 40 + "，。\n", "zh-doc"))

    def test_pure_chinese_line_budget(self):
        self.assertEqual(measure("汉" * 120, 120, 140), (240, 240))
        self.assertNotIn("long-line", categories("汉" * 120 + "\n", "zh-doc"))
        self.assertIn("long-line", categories("汉" * 121 + "\n", "zh-doc"))

    def test_pure_latin_keeps_len_budget(self):
        self.assertEqual(measure("a" * 90, 40, 90), (90, 90))
        self.assertEqual(measure("a" * 89 + " b.", 40, 90), (92, 90))
        self.assertNotIn("long-sentence", categories("a" * 87 + " b.\n", "zh-doc"))
        self.assertIn("long-sentence", categories("a" * 88 + " b.\n", "zh-doc"))

    def test_pure_japanese_keeps_wide_budget(self):
        sentence = "こ" * 90 + "。"
        self.assertEqual(measure(sentence, 40, 90), (180, 180))
        self.assertNotIn("long-sentence", categories(sentence + "\n", "zh-doc"))
        self.assertIn("long-sentence", categories("こ" * 91 + "。\n", "zh-doc"))

    def test_pure_korean_keeps_wide_budget(self):
        sentence = "한" * 90 + "."
        self.assertEqual(measure(sentence, 40, 90), (181, 180))
        self.assertNotIn("long-sentence", categories("한" * 90 + "\n", "zh-doc"))
        self.assertIn("long-sentence", categories("한" * 91 + "\n", "zh-doc"))

    def test_general_profile_chinese_budget_is_90_han(self):
        self.assertNotIn("long-sentence", categories("汉" * 90 + "。\n", "general"))
        self.assertIn("long-sentence", categories("汉" * 91 + "。\n", "general"))

    def test_empty_and_punct_only_measured_as_zero(self):
        self.assertEqual(measure("", 40, 90), (0, 90))
        self.assertEqual(measure("。，！", 40, 90), (0, 80))

class MixedScriptTests(unittest.TestCase):
    BUG_CASE = ("The loader validates the configuration file and every required field "
                "before it starts the service 配置。")

    def test_mostly_english_with_one_han_word_is_measured_by_latin_budget(self):
        count, limit = measure(self.BUG_CASE, 40, 90)
        self.assertEqual(limit, 90)
        self.assertEqual(count, 2 * count_cjk(self.BUG_CASE) + len(self.BUG_CASE) - count_wide(self.BUG_CASE))
        self.assertGreater(count, limit)
        self.assertIn("long-sentence", categories(self.BUG_CASE + "\n", "zh-doc"))

    def test_mostly_english_line_with_stray_han_is_measured_by_latin_budget(self):
        text = "x" * 137 + " 配置"
        count, limit = measure(text, 120, 140)
        self.assertEqual(limit, 140)
        self.assertIn("long-line", categories(text + "\n", "zh-doc"))

    def test_long_english_in_zh_doc_uses_latin_limit_not_cjk(self):
        text = "The pool opens connections lazily and closes them after a bounded timeout window."
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_chinese_sentence_with_identifiers_counts_both_parts(self):
        text = "配置 configLoader 后重启校验模块。"
        count, limit = measure(text, 40, 90)
        self.assertEqual(limit, 80)
        self.assertEqual(count, 2 * count_cjk(text) + (len(text) - count_wide(text)))
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_mixed_sentence_over_wide_budget_is_flagged(self):
        text = "配置加载失败时立即退出进程并输出诊断日志 " + "extra" * 30
        self.assertIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_numbers_and_terms_in_chinese_sentence(self):
        text = "峰值每秒 12 万条时，P99 从 40ms 涨到 900ms。"
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))
        text = "监控按「对象存储最新块时间 - PostgreSQL 最新分区时间」告警，超过 10 分钟触发。"
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_digits_count_toward_latin_budget(self):
        self.assertIn("long-line", categories("8" * 141 + "\n", "zh-doc"))
        self.assertNotIn("long-line", categories("8" * 140 + "\n", "zh-doc"))

    def test_japanese_with_embedded_english_uses_doubled_latin_budget(self):
        text = "このツールは seamless に動作し、設定ファイルを読み込んでから値を検証します。"
        count, limit = measure(text, 40, 90)
        self.assertEqual(limit, 180)
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_korean_with_embedded_english_uses_doubled_latin_budget(self):
        text = "이 도구는 seamless 하게 동작하며 설정 파일을 읽어 값 검증 후 종료됩니다."
        count, limit = measure(text, 40, 90)
        self.assertEqual(limit, 180)
        self.assertNotIn("long-sentence", categories(text + "\n", "zh-doc"))

    def test_kana_light_japanese_falls_back_to_dominance(self):
        text = "設定読込処理失敗時終了返停止 very long english tail here to tilt dominance"
        count, limit = measure(text, 40, 90)
        self.assertEqual(limit, 90)

    def test_halfwidth_punctuation_counts_but_cjk_punct_does_not(self):
        self.assertEqual(measure("汉" * 40 + "，。！？", 40, 90), (80, 80))
        self.assertEqual(measure("汉" * 38 + "....", 40, 90), (80, 80))

class CountHelperTests(unittest.TestCase):
    def test_count_wide_ranges(self):
        self.assertEqual(count_wide("汉字カナ한글。！＂～"), 10)
        self.assertEqual(count_wide("abc 123 .,;!?"), 0)
        self.assertEqual(count_wide(""), 0)
        self.assertEqual(count_wide("——…·"), 0)

    def test_measure_matches_documented_formula(self):
        for text in ("汉" * 30, "abc def", "汉" * 10 + "abc def", "設定" * 20,
                     "こ" * 20, "한글 " * 10, "汉" * 5 + "a" * 30):
            han = count_cjk(text)
            kana = sum(1 for ch in text if "぀" <= ch <= "ヿ")
            hangul = sum(1 for ch in text if "가" <= ch <= "힯")
            ea = han + kana + hangul
            wide = count_wide(text)
            narrow = len(text) - wide
            count = 2 * ea + narrow
            if ea == 0 and wide == 0:
                expected = (len(text), 90)
            elif (hangul and hangul >= han) or (kana and kana * 5 >= han + kana):
                expected = (count, 180)
            elif 2 * ea >= narrow:
                expected = (count, 80)
            else:
                expected = (count, 90)
            self.assertEqual(measure(text, 40, 90), expected, text)
