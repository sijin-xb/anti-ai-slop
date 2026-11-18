"""Rule registry for anti-ai-slop.

Single source of truth for rule identity and severity. The linter emits
findings whose ``category`` equals one of the ``rule_id`` values below; tests
and CI verify that the linter, SKILL.md, the references and the corpus stay in
sync with this file.

Field conventions:
- rule_id: stable identifier, used verbatim in CLI and JSON output.
- name: short zh-CN label.
- domain: text（通用文本）/ zh-doc / pair（语言对对照）/ budget（篇幅预算）/
  engineering / visual / verification / process.
- languages: ("*",) for language-independent, else language codes.
- severity: "error" = deterministic violation of a hard budget or a fact
  mismatch; "warning" = deterministic measurement over a stated limit;
  "advisory" = pattern clue that requires human judgement and must never be
  presented as proof of bad writing.
- basis: what justifies a finding.
- exceptions: contexts where a hit is legitimate and must be kept.
- detectable: "auto" = deterministic check, "clue" = pattern hit,
  "manual" = agent discipline that no script can verify.
- skill / references / tests: anchors; the integrity tests grep them.
"""
from __future__ import annotations

from dataclasses import dataclass

SEVERITY_RANK = {"advisory": 1, "warning": 2, "error": 3}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    domain: str
    languages: tuple[str, ...]
    severity: str
    basis: str
    exceptions: str
    detectable: str
    skill: str
    references: tuple[str, ...]
    tests: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    # Linter rules — pattern clues.
    Rule(
        "filler", "空泛套话与无依据营销词", "text", ("*",), "advisory",
        "命中语言包中的套话、元叙事开场或无依据营销形容词正则。",
        "引用与反例（引用块整行跳过）、行内代码、绑定具体名词的营销形容词（EXEMPT_PHRASES）、"
        "带误差界或容错模型的 robust 类术语。",
        "clue", "§3.2 / §4", ("anti-generic.md", "documentation.md"),
        ("test_filler", "test_chinese_filler_expansion", "test_english_filler_blacklist",
         "test_robust_with_statistical_bounds_is_allowed", "test_bad_samples_hit_their_own_language_pack"),
    ),
    Rule(
        "meta", "文档元话语与 AI 自指", "text", ("*",), "advisory",
        "命中「本文档旨在」「As an AI」等目的声明或自指正则。",
        "引用与反例、行内代码、骨架文档中对这类句式的说明本身。",
        "clue", "§4", ("anti-generic.md",),
        ("test_meta_commentary", "test_ai_persona_is_meta"),
    ),
    Rule(
        "thinking-leak", "处理过程泄漏", "text", ("zh", "en"), "advisory",
        "命中「让我先检查」「We need to inspect」等把内部过程写进交付物的正则。",
        "引用与反例、排障文档中对排查步骤的正当描述。",
        "clue", "§1 原则 4", ("anti-generic.md",),
        ("test_thinking_leak",),
    ),
    Rule(
        "overclaim", "无依据的绝对化保证", "text", ("*",), "advisory",
        "命中「100%」「绝对不会」「zero-risk」「完全杜绝」等正则。",
        "引用与反例、有证据支撑后写明的保证、行内代码。",
        "clue", "§4", ("anti-hallucination.md",),
        ("test_overclaim", "test_universal_pack_applies_in_every_language"),
    ),
    Rule(
        "closer", "收尾客套", "text", ("*",), "advisory",
        "命中「希望有帮助」「let me know if」「お役に立てれば幸いです」等正则。",
        "引用与反例；面向外部用户的正式信函类文体（由项目惯例决定）。",
        "clue", "§3.2 / §4", ("anti-generic.md",),
        ("test_closer",),
    ),
    Rule(
        "conversational", "对话化表达与无依据的「我们」断言", "zh-doc", ("zh",), "advisory",
        "命中「你会发现」「说白了」「我们相信」等正则。",
        "带依据的「我们建议/我们使用」等客观陈述（负向断言白名单见正则）。",
        "clue", "§3.2", ("anti-generic.md", "documentation.md"),
        ("test_conversational", "test_normal_usage_is_not_flagged", "test_unsupported_assertions_are_flagged"),
    ),
    Rule(
        "buzzword", "中文营销词", "zh-doc", ("zh",), "advisory",
        "命中「赋能」「助力」「打造」「一站式」等正则。",
        "「开箱即用」描述真实零配置默认值；引用与反例。",
        "clue", "§3.2", ("anti-generic.md",),
        ("test_buzzword", "test_buzzword_allows_factual_zero_config"),
    ),
    Rule(
        "contrast", "对仗修辞", "zh-doc", ("zh",), "advisory",
        "命中「不是 X 而是 Y」「并非 X 而是 Y」正则。",
        "排障结论：X 或 Y 侧含具体失败词（故障/问题/错误/缺陷/异常/失败/原因/配置/瓶颈/根因）。",
        "clue", "§3.2", ("anti-generic.md",),
        ("test_contrast", "test_contrast_allows_diagnostic_root_cause"),
    ),
    # Linter rules — deterministic measurements.
    Rule(
        "exclamation", "装饰性感叹号", "zh-doc", ("zh",), "warning",
        "zh-doc 正文出现「!」「！」字符；中文技术文档纪律默认零感叹号。",
        "面向新用户的一句欢迎；行内代码与图片 alt（已剔除）；引用块整行。",
        "auto", "§3.3", ("documentation.md",),
        ("test_exclamation_flagged_in_zh_doc", "test_exclamation_not_flagged_in_code_span",
         "test_exclamation_not_flagged_in_image_alt", "test_exclamation_only_in_zh_doc_profile"),
    ),
    Rule(
        "long-line", "单行超限", "budget", ("*",), "warning",
        "正文行长度超过 profile 阈值（general 140 / zh-doc 120，按长度口径折算）。",
        "标题、表格行、列表项、引用块、行内代码、链接 URL 不计入。",
        "auto", "§3.1", ("documentation.md",),
        ("test_long_line", "test_inline_code_embedded_in_prose_is_excluded"),
    ),
    Rule(
        "long-sentence", "单句超限", "budget", ("*",), "warning",
        "单句长度超过 profile 阈值（general 90 / zh-doc 40，按长度口径折算）。",
        "缩写、版本号、日期不切分；标题、表格、列表、引用不计。",
        "auto", "§3.1", ("documentation.md",),
        ("test_long_sentence", "test_abbreviations_do_not_split", "test_sentence_budget_is_40_cjk"),
    ),
    Rule(
        "long-paragraph", "段落行数超限", "budget", ("*",), "warning",
        "连续正文行数超过 profile 阈值（general 8 / zh-doc 4）。",
        "表格、代码块、参数映射清单、列表项不算正文段落。",
        "auto", "§3.1", ("documentation.md",),
        ("test_long_paragraph", "test_paragraph_budget_is_4_lines"),
    ),
    Rule(
        "repeated-line", "正文重复行", "text", ("*",), "warning",
        "同一规范化正文（去行内代码、大小写折叠）在全文出现第二次，且达到最小长度。",
        "短行（<24 字符且 <12 个东亚字符）不报；结构性行（标题/列表/表格）不参与。",
        "auto", "§4 Repetition", ("anti-generic.md",),
        ("test_repeated_line", "test_short_chinese_repeated_line",
         "test_repeated_line_ignores_inline_code_difference"),
    ),
    Rule(
        "readme-line-budget", "README 行数预算", "budget", ("zh",), "error",
        "zh-doc 下 README 主体超过 120 行（frontmatter 除外）。确定性预算违规。",
        "README 之外的文档不适用。",
        "auto", "§3.1", ("documentation.md", "readme-skeleton.md"),
        ("test_zh_doc_enforces_readme_line_budget", "test_budget_does_not_apply_to_usage_guide_names"),
    ),
    Rule(
        "readme-char-budget", "README 中文字符预算", "budget", ("zh",), "error",
        "zh-doc 下 README 汉字字符（不含标点）超过 800。确定性预算违规。",
        "README 之外的文档不适用。",
        "auto", "§3.1", ("documentation.md", "readme-skeleton.md"),
        ("test_zh_doc_enforces_readme_char_budget",),
    ),
    Rule(
        "parity-heading", "语言对标题结构不一致", "pair", ("*",), "error",
        "两个语言版本的某级标题数量不同；结构性事实分叉。",
        "围栏与行内代码不参与；确需不同的结构应先改两个语言版本。",
        "auto", "§5", ("documentation.md",),
        ("test_heading_structure_mismatch_flagged",),
    ),
    Rule(
        "parity-table", "语言对表格行数不一致", "pair", ("*",), "error",
        "两个语言版本的表格行数不同。",
        "围栏与行内代码不参与。",
        "auto", "§5", ("documentation.md",),
        ("test_table_row_mismatch_flagged",),
    ),
    Rule(
        "parity-number", "语言对正文数字不一致", "pair", ("*",), "error",
        "同一数字在两个语言版本正文中的出现次数不同。",
        "围栏与行内代码不参与；版本号与正文数字按整体比较。",
        "auto", "§5", ("documentation.md",),
        ("test_prose_number_mismatch_flagged",),
    ),
    # Skill-level disciplines no script can verify.
    Rule(
        "fact-audit", "操作性声明逐条核对", "verification", ("*",), "advisory",
        "命令、旗标、默认值、数量、路径必须对照同树实现（file:line 或实际输出）。",
        "无法本地核对的声明写明适用版本，降级为待验证。",
        "manual", "§5", ("anti-hallucination.md", "documentation.md"), (),
    ),
    Rule(
        "count-by-script", "计数用脚本不用印象", "verification", ("*",), "advisory",
        "「共 N 个」类声明必须由 ls | wc -l、grep -c 产出。",
        "无。",
        "manual", "§5", ("anti-hallucination.md",), (),
    ),
    Rule(
        "ported-facts", "移植的文档不继承事实", "verification", ("*",), "advisory",
        "上游/旧版本移植的文档按本树全部重核。",
        "写明适用版本/分支的声明。",
        "manual", "§5", ("anti-hallucination.md", "documentation.md"), (),
    ),
    Rule(
        "mirror-consistency", "多语言镜像事实一致", "verification", ("*",), "advisory",
        "语言对散文可不同，数字、命令、旗标、列表项、结构必须一一对应；机械部分由 parity-* 自动查。",
        "围栏与行内代码内容由声明核对流程覆盖。",
        "manual", "§5", ("documentation.md",), (),
    ),
    Rule(
        "terminology-anchor", "术语以代码为准绳", "verification", ("*",), "advisory",
        "同一概念在文档集内用同一个词，锚定代码 user-facing 字符串。",
        "无。",
        "manual", "§5", ("documentation.md",), (),
    ),
    Rule(
        "hunk-adjudication", "对照版本逐 hunk 裁决", "verification", ("*",), "advisory",
        "fork/新旧版本 diff 以「哪边符合当前代码树」裁决，不凭新旧或文风。",
        "运行时行为等无法静态裁决的标注待验证。",
        "manual", "§5", ("documentation.md",), (),
    ),
    Rule(
        "no-hallucination", "不编造事实", "verification", ("*",), "advisory",
        "不编造 API、文件、数据、引用、功能、测试结果或视觉细节；事实分级。",
        "标明为假设的推断。",
        "manual", "§1 原则 3", ("anti-hallucination.md",), (),
    ),
    Rule(
        "verification-states", "四态验证报告", "verification", ("*",), "advisory",
        "验证结论只用 Passed / Failed / Blocked / Not Run 并附命令与输出。",
        "无。",
        "manual", "§1 原则 9", ("quality-verification.md",), (),
    ),
    Rule(
        "minimal-sufficiency", "最小充分", "engineering", ("*",), "advisory",
        "只保留解决任务所需的结构、抽象、依赖与解释。",
        "用户明确要求的详细解释；结构化格式需要。",
        "manual", "§1 原则 5", ("anti-overengineering.md",), (),
    ),
    Rule(
        "real-constraint-complexity", "复杂度由真实约束支付", "engineering", ("*",), "advisory",
        "抽象/依赖/配置必须有真实约束（性能、安全、并发、可测试性、明确需求）支撑。",
        "两个以上真实调用方；规范强制结构；实测数据支撑的优化；安全与校验。",
        "manual", "§4", ("anti-overengineering.md",), (),
    ),
    Rule(
        "scope-drift", "无无关改动", "engineering", ("*",), "advisory",
        "不顺手重构、不顺手统一风格、不混入行为变更。",
        "正确性、安全性或集成要求时。",
        "manual", "§4", ("anti-overengineering.md", "software-engineering.md"), (),
    ),
    Rule(
        "comment-discipline", "注释纪律", "engineering", ("*",), "advisory",
        "不写复述代码的注释与无信息量注释；注释解释复杂算法、不变量、安全约束与非显而易见的设计原因。",
        "公共 API 文档注释遵循项目既有惯例；命令示例不放行内注释。",
        "manual", "§1 原则 5", ("software-engineering.md",), (),
    ),
    Rule(
        "visual-purpose", "视觉元素有职责", "visual", ("*",), "advisory",
        "每个显眼元素承担层级、状态、操作或身份职责；装饰不冒充信息。",
        "用户要求的风格；品牌规范；功能性动画。",
        "manual", "§4", ("anti-visual-slop.md",), (),
    ),
    Rule(
        "visual-truthfulness", "视觉内容不虚构", "visual", ("*",), "advisory",
        "图表数据、界面数字、用户信息、徽章必须来自真实来源。",
        "占位内容明确标注。",
        "manual", "§4", ("anti-visual-slop.md", "anti-hallucination.md"), (),
    ),
    Rule(
        "render-gate", "视觉验证须渲染后进行", "verification", ("*",), "advisory",
        "读代码、看 SVG 源码不构成视觉验证；无渲染环境记 Blocked 或 Not Run。",
        "无。",
        "manual", "§1 原则 8", ("anti-visual-slop.md", "quality-verification.md"), (),
    ),
    Rule(
        "target-size", "触摸目标按平台标准", "visual", ("*",), "advisory",
        "触屏目标 ≥ 44×44 px（WCAG 2.5.5 AAA 参考）；WCAG 2.5.8 AA 最低 24×24 px 含间距豁免；"
        "桌面鼠标界面不适用该下限；键盘焦点单独验证；平台原生规范优先。",
        "图标加间距补偿；仅鼠标/键盘的桌面控件。",
        "manual", "§4", ("anti-visual-slop.md",), (),
    ),
    Rule(
        "zh-budget", "中文篇幅预算", "budget", ("zh",), "advisory",
        "README 120 行/800 汉字、单节 15 行、单段 4 行、单句 40 字、标题 3 层（机械部分由 linter 自动查）。",
        "表格、代码块、参数映射清单不算正文段落；全局规则另有规定时以全局为准。",
        "manual", "§3.1", ("documentation.md",), (),
    ),
    Rule(
        "zh-structure", "中文结构与取舍", "zh-doc", ("zh",), "advisory",
        "开篇定义句、祈使句、名词短语标题、术语一致、不写元话语。",
        "面向新用户的一句欢迎可带一个感叹号。",
        "manual", "§3.3", ("documentation.md",), (),
    ),
    Rule(
        "decision-discipline", "决策提问纪律", "process", ("*",), "advisory",
        "需要用户拍板的决策列 2-4 个具体选项并写明代价；优先宿主交互式提问能力，不支持时普通对话提问；"
        "只有确实需要用户决策才中断。",
        "不阻断正确执行的信息缺口用低风险假设并标明。",
        "manual", "§1 原则 7", ("anti-overengineering.md",), (),
    ),
)

RULE_IDS = frozenset(rule.rule_id for rule in RULES)
SEVERITY_BY_ID = {rule.rule_id: rule.severity for rule in RULES}

LINTER_RULE_IDS = frozenset(
    rule.rule_id for rule in RULES if rule.detectable in ("auto", "clue")
)
