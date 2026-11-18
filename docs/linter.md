# Linter 说明

长篇说明集中在本文件。命令速查和 profile 对比见 `SKILL.md` 第 7 节与 `README.md`。

## 计数口径

行长、句长的「长度」按以下单位计算，单位是半角字符：半角字符计 1，东亚字符计 2。

| 字符类别 | 权重 | 例子 |
|---|---|---|
| 东亚字符（汉字、假名、谚文音节与字母） | 2 | 汉、カ、한 |
| CJK 标点与全角形式 | 0 | `。、「」！＂～` |
| 其余字符（拉丁字母、数字、空格、半角标点） | 1 | a、9、空格 |

CJK 标点计 0 是继承行为：旧版按汉字数计数时句号不计入，40 个汉字加句号
的句子一直视为合规。纯英文文本因此保持旧的 `len()` 计数，纯中文保持旧的
汉字计数。

**混合文本两部分都计**。修复前的缺陷：句子只要含一个汉字，就按汉字数计，
英文部分被整体忽略——一段 200 字符的英文句加一个「的」字就能绕过中文预算。
修复后按上表折算成同一单位。

预算随主导文字走：

- 日文或韩文主导：用宽口径（Latin 预算），日韩语素长，历史口径即如此。
- 否则按主导文字：东亚主导（2×东亚字符数 ≥ 其余字符数）用 CJK 预算，
  拉丁主导用 Latin 预算。
- 两个 profile 的阈值不变：行 general 140 / zh-doc 120，句 general 90 /
  zh-doc 40，段行数 general 8 / zh-doc 4。CJK 预算按汉字数生效，与旧版一致。

`README 中文字符预算`独立计口径：只数汉字（U+4E00–U+9FFF），不含标点，
与旧版一致。

## 告警语义

| 严重程度 | 含义 | 规则 |
|---|---|---|
| `error` | 确定性违规：硬预算超标、语言对事实分叉 | `readme-*-budget`、`parity-*` |
| `warning` | 确定性测量超限 | `long-line`、`long-sentence`、`long-paragraph`、`repeated-line`、`exclamation` |
| `advisory` | 正则线索，需人工判断，不构成质量结论 | `filler`、`meta`、`thinking-leak`、`overclaim`、`closer`、`conversational`、`buzzword`、`contrast` |

划分依据是规则性质，不是随意分级：能确定测量的归 error/warning，正则命中
只能当线索的归 advisory。advisory 命中必须逐条人工审查。

规则 ID、名称、领域、语言、严重程度、判断依据、例外、可检测性和对应测试
统一登记在 `scripts/rules.py`。测试保证 linter 输出的每个类别都在登记表内，
登记表引用的测试与参考文件都存在。

## 退出码

| 码 | 条件 |
|---|---|
| 0 | 没有达到失败阈值的告警；或未给 `--strict` / `--fail-on` |
| 1 | 存在严重程度 ≥ 失败阈值的告警 |
| 2 | 用法错误、IO 错误、正则错误、不支持的文件类型 |

`--strict` 等价于 `--fail-on advisory`（任何告警都触发）。两者互斥。不带
这两个参数时 linter 只报告，不改变退出码。

## JSON 输出

顶层字段：`profile`、`languages`、`files_scanned`、`finding_count`、
`severity_counts`、`findings`、`note`。每条 finding 固定字段序：
`path`、`line`、`column`、`category`（即规则 ID）、`excerpt`、`hint`、
`severity`。字段只增不改，旧消费方兼容。

`languages` 报告的是每个文件的检测主语言；zh-doc 下检测为其他语言时，
文件仍只按通用包扫描，这里如实报告检测结果。

## 格式支持

| 格式 | 支持程度 |
|---|---|
| `.md` / `.markdown` | 完整：围栏（含四反引号与波浪线）、HTML 注释、引用块、表格、引用链接定义 |
| `.mdx` | 同 Markdown；行内 JSX 标签按 HTML 标签剔除。段落之间游离的多行 JSX 块未建模，可能误报 |
| `.txt` | 按纯文本处理；内容恰为 Markdown 时围栏同样生效 |
| `.rst` | 注释与指令块（`..` 引导，含缩进内容）、`::` 字面块跳过；`~~~`/`===` 小节下划线按结构行处理，不吞后续段落。域列表、网格表等扩展未建模 |

## 扫描排除的内容

围栏内部、行内代码、链接 URL（锚文本保留）、图片 alt、裸 URL、引用块整行
（含 GitHub `> [!NOTE]` 类告警框）、多行 HTML 注释、frontmatter、引用链接
定义。黑名单短语出现在引用和反例中是合理语境，因此引用块整行不扫描。

## 语料标注口径

`tests/corpus/manifest.json` 的标注为人工标注，随语料 diff 一起评审：

- good 文件零告警；`allowed` 字段登记已论证的例外（当前为空）。
- bad 文件 `expected` 为 general profile 必报规则；`zh_doc_expected` 为
  zh-doc profile 的完整必报集，只标给 zh-doc 能实际执行的语言（zh、en、
  README 与语言无关检查）。zh-doc 不加载 de/fr/es/ja/ko 语言包，这些语言
  的 bad 样本不要求在 zh-doc 下命中。
- bad 文件的超额命中计入真阳性。缺失必报规则计入假阴性。
- 无法客观判定的风格问题（未测量的性能声明、无套话措辞的虚构验证叙事）
  不在标注范围内，归 SKILL.md 第 5 节的人工事实核对。

`scripts/corpus_metrics.py` 从同一标注计算 precision / recall /
file FPR / file FNR，按规则和按语言分解。`tests/test_corpus.py` 的下限
测试保证回归先在 CI 里显形。

## Agent 评估

`tests/evaluation/` 提供固定任务集、九维度评分标准、盲评流程和结果模板。
评估靠人工盲评对比 Baseline 与 Treatment；当前无已执行的评估轮次，结果
状态一律 Not Run。触发语料（`trigger-corpus.json`）只验证结构一致性，
真实模型的触发行为按 `tests/evaluation/README.md` 的流程人工验证。
