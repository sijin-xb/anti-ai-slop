"""Compute precision / recall metrics of the linter against the labeled corpus.

Labeling standard (human-assigned, see tests/corpus/manifest.json):
- Good files must produce zero findings. Any finding is a false positive,
  except rule IDs listed in the file's ``allowed`` field (documented
  exceptions; none in the current corpus).
- Bad files carry ``expected`` rule IDs (required under profile general) and
  ``zh_doc_expected``: the FULL required set under profile zh-doc, listed
  only for files whose rules zh-doc can enforce (zh, en, README and
  language-independent checks — zh-doc deliberately loads no de/fr/es/ja/ko
  packs). A required rule that does not fire is a false negative. Additional
  hits on bad files are true positives: the text genuinely violates those
  rules too.

Reported metrics (all computed per profile):
- precision  = TP / (TP + FP), at finding level, where FP are findings on
  good files (rule-level breakdown included) and TP are findings on bad files.
- recall     = required labels covered / required labels, aggregated and
  per rule.
- file FPR   = good files with at least one non-allowed finding / good files.
- file FNR   = bad files missing at least one required rule / bad files.
- breakdowns per language (filename prefix, README counts as zh) and per rule.

Style problems that no regex can objectively judge (unmeasured performance
claims, fabricated verification stories without slop wording) are deliberately
NOT part of the labeled ground truth; they belong to the manual fact audit in
SKILL.md section 5. This report never claims to measure those.

Usage: python scripts/corpus_metrics.py [--profile general|zh-doc] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    from .anti_slop_lint import scan_file
    from .rules import LINTER_RULE_IDS
except ImportError:
    from anti_slop_lint import scan_file
    from rules import LINTER_RULE_IDS

CORPUS = Path(__file__).resolve().parent.parent / "tests" / "corpus"
LIMITS = {
    "general": {"max_line": 140, "max_sentence": 90, "max_paragraph": 8},
    "zh-doc": {"max_line": 120, "max_sentence": 40, "max_paragraph": 4},
}
PROFILES = ("general", "zh-doc")


def load_manifest() -> dict:
    return json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))


def language_of(name: str) -> str:
    prefix = name.split("-")[0]
    return prefix if prefix in {"zh", "en", "ja", "ko", "de", "fr", "es", "ru", "pt"} else "zh"


def scan_corpus(profile: str) -> dict[str, list]:
    findings: dict[str, list] = {}
    for sub in ("good", "bad"):
        for path in sorted((CORPUS / sub).glob("*.md")):
            found = scan_file(path, profile=profile, **LIMITS[profile])
            findings[f"{sub}/{path.name}"] = found
    return findings


def compute_report(profile: str) -> dict:
    manifest = load_manifest()
    findings = scan_corpus(profile)
    labels = manifest["bad"]

    tp = fp = 0
    tp_by_rule: Counter = Counter()
    fp_by_rule: Counter = Counter()
    good_files_with_fp = 0
    per_language: dict[str, dict[str, int]] = {}

    for key, found in findings.items():
        sub, name = key.split("/", 1)
        lang = language_of(name)
        stats = per_language.setdefault(lang, {"tp": 0, "fp": 0, "files": 0})
        stats["files"] += 1
        if sub == "good":
            entry = manifest["good"][name]
            allowed = set(entry.get("allowed", []))
            bad = [f for f in found if f.category not in allowed]
            if bad:
                good_files_with_fp += 1
            for f in bad:
                fp += 1
                fp_by_rule[f.category] += 1
                stats["fp"] += 1
        else:
            entry = labels[name]
            required = set(entry["expected"])
            if profile == "zh-doc":
                required = set(entry.get("zh_doc_expected", []))
            found_rules = {f.category for f in found}
            for f in found:
                tp += 1
                tp_by_rule[f.category] += 1
                stats["tp"] += 1
            entry["_missing"] = sorted(required - found_rules)
            entry["_required_count"] = len(required)

    required_total = sum(v["_required_count"] for v in labels.values())
    missing_total = sum(len(v["_missing"]) for v in labels.values())

    per_rule = {}
    for rule_id in sorted(LINTER_RULE_IDS):
        per_rule[rule_id] = {
            "tp": tp_by_rule.get(rule_id, 0),
            "fp": fp_by_rule.get(rule_id, 0),
        }

    bad_files = [v for v in labels.values()]
    bad_files_with_fn = sum(1 for v in bad_files if v["_missing"])
    good_files = len(manifest["good"])

    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = (required_total - missing_total) / required_total if required_total else 1.0
    file_fpr = good_files_with_fp / good_files if good_files else 0.0
    file_fnr = bad_files_with_fn / len(bad_files) if bad_files else 0.0

    report = {
        "profile": profile,
        "precision": precision,
        "recall": recall,
        "file_fpr": file_fpr,
        "file_fnr": file_fnr,
        "tp": tp,
        "fp": fp,
        "fp_by_rule": dict(fp_by_rule),
        "required_labels": required_total,
        "missing_labels": missing_total,
        "missing_detail": {name: v["_missing"] for name, v in labels.items() if v["_missing"]},
        "per_rule": per_rule,
        "per_language": {
            lang: {
                "files": s["files"],
                "precision": (s["tp"] / (s["tp"] + s["fp"])) if s["tp"] + s["fp"] else 1.0,
                "tp": s["tp"],
                "fp": s["fp"],
            }
            for lang, s in sorted(per_language.items())
        },
        "labeling": "human-assigned labels; see tests/corpus/manifest.json and docs/linter.md",
    }
    for entry in labels.values():
        entry.pop("_missing", None)
        entry.pop("_required_count", None)
    return report


def render(report: dict) -> str:
    lines = [
        f"Profile: {report['profile']}  (labels: {report['labeling']})",
        f"precision  {report['precision']:.3f}   TP {report['tp']}  FP {report['fp']}",
        f"recall     {report['recall']:.3f}   required {report['required_labels']}  missing {report['missing_labels']}",
        f"file FPR   {report['file_fpr']:.3f}   file FNR {report['file_fnr']:.3f}",
        "",
        "per rule:",
    ]
    for rule_id, stats in report["per_rule"].items():
        if stats["tp"] or stats["fp"]:
            lines.append(f"  {rule_id:<18} TP {stats['tp']:>3}  FP {stats['fp']:>3}")
    lines.append("")
    lines.append("per language:")
    for lang, stats in report["per_language"].items():
        lines.append(
            f"  {lang}  files {stats['files']:>2}  TP {stats['tp']:>3}  FP {stats['fp']:>3}  precision {stats['precision']:.3f}"
        )
    if report["missing_detail"]:
        lines.append("")
        lines.append("missing required labels:")
        for name, missing in report["missing_detail"].items():
            lines.append(f"  {name}: {', '.join(missing)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus precision/recall report for the anti-slop linter.")
    parser.add_argument("--profile", choices=PROFILES, default="general")
    parser.add_argument("--json", action="store_true", help="output JSON instead of text")
    parser.add_argument("--all-profiles", action="store_true", help="report both profiles")
    args = parser.parse_args(argv)

    profiles = PROFILES if args.all_profiles else (args.profile,)
    reports = [compute_report(profile) for profile in profiles]
    if args.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(render(report) for report in reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
