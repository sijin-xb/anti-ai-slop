# anti-ai-slop

A cross-domain quality skill. Five review dimensions plus hard discipline for technical documents.

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Ten principles, task routing, hard rules for Chinese documents, fact audit, pre-delivery checklist |
| `references/` | Per-task rules: anti-generic, anti-overengineering, anti-hallucination, anti-visual-slop, quality verification |
| `scripts/anti_slop_lint.py` | Text linter with `general` / `zh-doc` profiles and `--pair` language-pair parity |
| `tests/` | 129 tests with positive and negative samples for zh / en / ja / ko / de / fr / es |

Document-writing details live in `references/documentation.md`, skeletons in `readme-skeleton.md` and `doc-skeletons.md`, engineering conventions in `references/software-engineering.md`.

## Install

```bash
mkdir -p ~/.agents/skills ~/.claude/skills
git clone https://github.com/sijin-xb/anti-ai-slop ~/.agents/skills/anti-ai-slop
ln -s ~/.agents/skills/anti-ai-slop ~/.claude/skills/anti-ai-slop
```

Claude Code, ZCode and compatible agents discover the skill from their skills directories.
If you clone elsewhere, adjust the source path in the third command.

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
```

The default profile flags filler, hallucinated claims and overclaiming across languages.
`--profile zh-doc` adds the Chinese discipline: length budgets, the blacklist and exclamation checks.
`--pair` compares two language versions of one document: headings, table rows and prose numbers.
Fenced blocks and inline code are excluded. All options are documented in `SKILL.md`, section 7.

## The two profiles

| Rule | general | zh-doc |
|---|---|---|
| Language packs | universal + zh / en / ja / ko / de / fr / es | universal + zh + en |
| Cross-domain filler and overclaiming | yes | yes |
| Conversational tone, rhetorical pairing, buzzwords | no | yes |
| Decorative exclamation marks (minimal style) | no | yes |
| Line / sentence / paragraph length | 140 / 90 / 8 | 120 / 40 / 4 |
| README line and Chinese-character budget | no | yes |

The language pack follows the document's dominant language.
Chinese sentences are measured in Chinese characters, Latin text in total length.

## Known limits

- The linter only matches patterns; it cannot judge factual truth, code design or visual quality.
- Commands documented but absent from the code, and factual divergence inside fenced blocks, belong to the claim audit in `SKILL.md` section 5. The script cannot replace it.
- Quoted counter-examples get flagged; mask them with `--ignore-regex` or backticks.

## License

MIT
