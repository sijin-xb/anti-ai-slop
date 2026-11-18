"""Line-classification regression tests: fences, HTML comments, RST,
blockquotes and structural rows must never leak into prose scanning."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.anti_slop_lint import classify_lines, collect_files, prose_text  # noqa: E402

SLOP = "值得注意的是这句话命中 filler 规则"

def write_scan(text: str, suffix: str = ".md", profile: str = "general"):
    from scripts.anti_slop_lint import scan_file
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"sample{suffix}"
        path.write_text(text, encoding="utf-8")
        limits = {"max_line": 140, "max_sentence": 90, "max_paragraph": 8}
        if profile == "zh-doc":
            limits = {"max_line": 120, "max_sentence": 40, "max_paragraph": 4}
        return scan_file(path, profile=profile, **limits)

class FenceTests(unittest.TestCase):
    def test_four_backtick_fence_hides_inner_triple_fence(self):
        text = "````markdown\n```bash\n" + SLOP + "\n```\n正文结束。\n````\n"
        self.assertEqual([f.category for f in write_scan(text)], [])

    def test_shorter_close_does_not_end_four_tick_fence(self):
        text = "````\n" + SLOP + "\n```\nstill inside " + SLOP + "\n````\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text)], [])

    def test_longer_close_ends_fence(self):
        text = "```py\n" + SLOP + "\n`````\n正文值得注意的是。\n"
        found = [f.category for f in write_scan(text)]
        self.assertEqual(found, ["filler"])
        self.assertEqual({f.line for f in write_scan(text) if f.category == "filler"}, {4})

    def test_tilde_fence_hides_backtick_lines(self):
        text = "~~~\n" + SLOP + "\n```\n还在围栏里 " + SLOP + "\n```\n~~~\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text)], [])

    def test_backtick_fence_not_closed_by_tilde(self):
        text = "```py\n" + SLOP + "\n~~~\n仍inside " + SLOP + "\n```\n正文值得注意的是。\n"
        found = write_scan(text)
        self.assertEqual({f.category for f in found}, {"filler"})
        self.assertEqual({f.line for f in found}, {6})

    def test_close_fence_with_info_string_does_not_close(self):
        text = "````\n" + SLOP + "\n````text\n仍在围栏 " + SLOP + "\n````\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text)], [])

    def test_unclosed_fence_extends_to_eof(self):
        text = "```bash\ncode\n```\n```\n" + SLOP + "\nmore " + SLOP + "\n"
        self.assertEqual([f.category for f in write_scan(text)], [])

    def test_fence_info_string_with_backtick_is_not_a_fence(self):
        text = "```ba`ck`tick\n" + SLOP + "\n```\n正文值得注意的是。\n"
        found = write_scan(text)
        self.assertEqual({f.category for f in found}, {"filler"})
        self.assertEqual({f.line for f in found}, {2})

    def test_fence_in_list_item_is_respected(self):
        text = "- 步骤：\n\n  ```bash\n  " + SLOP + "\n  ```\n\n正文值得注意的是。\n"
        found = write_scan(text)
        self.assertEqual({f.category for f in found}, {"filler"})
        self.assertEqual({f.line for f in found}, {7})

    def test_fenced_slop_does_not_decide_language_or_repeat(self):
        text = "说明。\n\n```text\n" + ("值得注意的是 " * 30) + "\n```\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

class HtmlCommentTests(unittest.TestCase):
    def test_multiline_comment_is_skipped(self):
        text = "<!--\n" + SLOP + "\n部署完成！\n-->\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

    def test_single_line_comment_with_prose_still_scans_prose(self):
        text = "前文 <!-- " + SLOP + " --> 后文值得注意的是。\n"
        self.assertIn("filler", {f.category for f in write_scan(text)})

    def test_comment_close_on_same_line_ends_state(self):
        text = "<!-- x --> 正文值得注意的是。\n<!-- y -->\n更多正文值得注意的是。\n"
        found = write_scan(text)
        self.assertEqual({f.line for f in found if f.category == "filler"}, {1, 3})

    def test_inline_code_containing_comment_marker_does_not_start_comment(self):
        text = "用 `<!--` 开启注释。\n\n值得注意的是这句是正文。\n"
        self.assertIn("filler", {f.category for f in write_scan(text)})

class RstTests(unittest.TestCase):
    def test_tilde_underline_does_not_swallow_next_paragraph(self):
        text = "小节标题\n~~~~~~\n\n" + SLOP + "。\n"
        self.assertIn("filler", {f.category for f in write_scan(text, suffix=".rst")})

    def test_comment_block_is_skipped(self):
        text = ".. 注意\n   " + SLOP + "\n\n正文值得注意的是。\n"
        found = write_scan(text, suffix=".rst")
        self.assertEqual({f.line for f in found if f.category == "filler"}, {4})

    def test_directive_content_is_skipped(self):
        text = ".. code-block:: python\n\n    value = '值得注意的是'\n\n正文值得注意的是。\n"
        found = write_scan(text, suffix=".rst")
        self.assertEqual({f.line for f in found if f.category == "filler"}, {5})

    def test_literal_block_is_skipped(self):
        text = "用法::\n\n    run --force 值得注意的是\n\n正文值得注意的是。\n"
        found = write_scan(text, suffix=".rst")
        self.assertEqual({f.line for f in found if f.category == "filler"}, {5})

    def test_literal_block_ends_at_unindented_line(self):
        text = "用法::\n\n    run --force\n\n" + SLOP + "。\n"
        self.assertIn("filler", {f.category for f in write_scan(text, suffix=".rst")})

class BlockquoteTests(unittest.TestCase):
    def test_quoted_slop_is_not_scanned(self):
        text = "> 引用反例：" + SLOP + "！\n\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

    def test_github_alert_callout_is_clean_in_zh_doc(self):
        text = "> [!WARNING]\n> 此操作不可逆，执行前备份配置。\n\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

    def test_quoted_length_is_not_measured(self):
        text = "> " + ("字" * 60) + "\n\n正文。\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

class StructuralRowTests(unittest.TestCase):
    def test_hr_closes_paragraph(self):
        text = "\n".join(f"第 {n} 行正文，内容各不相同。" for n in range(4)) + "\n---\n" \
            + "\n".join(f"第 {n} 行正文，内容各不相同。" for n in range(4)) + "\n"
        self.assertEqual([f.category for f in write_scan(text, profile="zh-doc")], [])

    def test_setext_underline_does_not_count_as_prose(self):
        text = "标题行\n======\n\n值得注意的是这句是套话。\n"
        found = write_scan(text)
        self.assertEqual({f.category for f in found}, {"filler"})
        self.assertEqual({f.line for f in found}, {4})

class CollectFilesTests(unittest.TestCase):
    def test_hidden_directories_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("可见正文\n", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "hidden.md").write_text("隐藏正文\n", encoding="utf-8")
            (root / ".hidden").mkdir()
            (root / ".hidden" / "b.md").write_text("隐藏正文\n", encoding="utf-8")
            found = collect_files([str(root)])
            self.assertEqual([p.name for p in found], ["a.md"])

    def test_explicit_hidden_file_is_still_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            hidden = Path(tmp) / ".note.md"
            hidden.write_text("正文\n", encoding="utf-8")
            self.assertEqual([p.name for p in collect_files([str(hidden)])], [".note.md"])

class ClassifyLinesTests(unittest.TestCase):
    def test_classify_reports_fence_and_interior_lines(self):
        lines = ["正文", "```py", "code", "```", "更多正文"]
        self.assertEqual(classify_lines(lines), {2, 3, 4})

    def test_prose_text_skips_fences_and_ref_defs(self):
        text = "正文值得注意的是。\n\n[link]: https://example.com/a\n\n```py\nslop\n```\n"
        self.assertEqual(prose_text(text.splitlines()), "正文值得注意的是。\n\n")
