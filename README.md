# anti-ai-slop

A cross-domain quality skill. Five review dimensions plus hard discipline for Chinese technical documents.

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Ten principles, task routing, hard rules for Chinese documents, fact audit, pre-delivery checklist |
| `references/` | Per-task rules: anti-generic, anti-overengineering, anti-hallucination, anti-visual-slop, software engineering, documentation, quality verification |
| `scripts/anti_slop_lint.py` | Text linter with `general` / `zh-doc` profiles and `--pair` language-pair parity |
| `scripts/rules.py` | Rule registry: IDs, severities, exceptions, test anchors |
| `scripts/corpus_metrics.py` | Precision / recall report over the labeled corpus |
| `docs/linter.md` | Counting standard, severity model, exit codes, format support |
| `tests/` | 233 tests; labeled corpus with manifest; agent evaluation kit in `tests/evaluation/` |

## Install

Every agent discovers skills from its own directory; no single path is a
standard. Install once into a real directory, then link it into each agent's
skills directory. The commands below are safe to re-run.

```bash
git clone https://github.com/sijin-xb/anti-ai-slop ~/.agents/skills/anti-ai-slop
mkdir -p ~/.claude/skills
ln -sfn ~/.agents/skills/anti-ai-slop ~/.claude/skills/anti-ai-slop
```

- If `~/.agents/skills/anti-ai-slop` already exists, `git clone` fails without touching it. Update with `git -C ~/.agents/skills/anti-ai-slop pull`.
- `ln -sfn` replaces an existing symlink in place. If the target path is a real directory, it silently creates the link inside that directory instead — verify with `ls -la ~/.claude/skills/anti-ai-slop` (expect a symlink) and remove a real directory first if you want the link.
- Claude Code discovers skills in `~/.claude/skills`; ZCode also reads `~/.agents/skills` directly. Other agents differ — check their documentation.

## Verify the install

```bash
python -m unittest discover -s tests
python scripts/anti_slop_lint.py --profile zh-doc README.md SKILL.md
```

Run both inside the clone. Expect every test to pass and the linter to report zero findings.

## Usage

```bash
python scripts/anti_slop_lint.py README.md
python scripts/anti_slop_lint.py --profile zh-doc README.md
python scripts/anti_slop_lint.py README.md --pair README.zh-CN.md
python scripts/anti_slop_lint.py --json docs/
python scripts/anti_slop_lint.py --fail-on warning README.md
```

Every finding carries a severity: `error` for deterministic budget or fact violations, `warning`
for deterministic measurements over a limit, `advisory` for pattern clues that need human judgement.

`--strict` fails on any finding; `--fail-on` picks a threshold.
Exit codes: 0 clean, 1 threshold reached, 2 usage or IO error.

## The two profiles

| Rule | general | zh-doc |
|---|---|---|
| Language packs | universal + dominant-language pack | universal + zh + en |
| Cross-domain filler and overclaiming | yes | yes |
| Conversational tone, rhetorical pairing, buzzwords | no | yes |
| Decorative exclamation marks | no | yes |
| Line / sentence / paragraph length | 140 / 90 / 8 | 120 / 40 / 4 |
| README line and Chinese-character budget | no | yes |

Mixed-language sentences count both scripts (see `docs/linter.md`); the
language pack follows the document's dominant language.

## Quality metrics

```bash
python scripts/corpus_metrics.py --all-profiles
```

Computes precision, recall, file-level FPR/FNR over the labeled corpus
(`tests/corpus/manifest.json`, human-assigned labels). Both profiles currently
report precision 1.000 / recall 1.000.

The agent evaluation kit in `tests/evaluation/` (fixed tasks, rubric, blind
protocol) is ready; no evaluation round has been run yet.

## CI

GitHub Actions runs the test suite on Python 3.11–3.14 and lints this
project's own documentation with both profiles.

## Known limits

- The linter only matches patterns and measures lengths; it cannot judge factual truth, code design or visual quality.
- Commands documented but absent from the code, and factual divergence inside fenced blocks, belong to the claim audit in `SKILL.md` section 5. The script cannot replace it.
- Blockquotes (quotes, counter-examples, `> [!NOTE]` callouts) are skipped entirely; slop hidden inside quotes will not be flagged.
- Free-floating multi-line JSX blocks in MDX, and RST field lists / grid tables, are not modeled; details in `docs/linter.md`.

## License

MIT
