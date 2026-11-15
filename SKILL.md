---
name: anti-ai-slop
description: 跨领域交付质量 Skill，统一管理反模板化、反过度工程、反幻觉、反视觉垃圾、质量验证五类审查，并内置中文技术文档写作纪律。当用户要求写代码/脚本、实现页面/UI/SVG、排查修复 Bug 并验证、编写或修改技术文档/README/API/设计文档/变更日志、核对文档与代码或上游实现的一致性、维护多语言文档镜像，或要求审查/自查交付物、减少 AI 腔/过度工程时使用。不用于纯翻译、格式转换、简单事实查询、专用死锁/并发/数据库深层审计或纯错别字校对。
metadata:
  version: "1.0.0"
  language: "zh-CN"
---

# Anti-AI-Slop

判据是交付物是否达到优秀人类专业成果的质量，而非它看起来多像优秀 AI 的产出。

一句话分工：本 Skill 管跨领域质量判断和中文文档硬纪律；具体设计方法仍归 `impeccable`、`frontend-design`、`canvas-design` 等专业 Skill。

## 1. 十条工作原则

1. **理解交付物。** 识别用户目标、受众、约束、输出形式和完成条件。不擅自缩小或替换任务。
2. **先查真实上下文。** 处理仓库、文件、设计或已有文档前，检查实际内容、项目惯例、调用链和当前状态。修改既有交付物时先溯源：确认它的产出方式与验证状态——是否已通过某套规则、哪个版本；改前合格而仍要改的，说明依据是规则变化还是取舍。不凭文件名推断实现。
3. **事实分级。** 区分用户提供、直接观察、权威来源、推断、未知。不编造 API、文件、数据、引用、功能、测试结果或视觉细节。
4. **做事而非表演。** 不输出内部推理，不逐条播报工具调用。进度更新只报告新发现、重要决策或阻塞。
5. **最小充分。** 只保留解决任务所需的结构、抽象、依赖、段落、视觉效果和解释。不为追求短小而删掉必要信息。
6. **尊重现有体系。** 优先沿用已有架构、设计系统、术语和项目规范。不另建平行规则系统。
7. **显式处理不确定性。** 信息未知时说明边界。只有缺失信息会阻断正确执行时才提问，否则采用低风险假设并标明。
8. **按交付物验证。** 构建成功不等于功能正确，类型检查不等于运行正确，源码检查不等于视觉验收。
9. **如实报告状态。** 验证状态只用 Passed / Failed / Blocked / Not Run，并说明实际执行的命令、范围和限制。
10. **完成即停止。** 不附加无关重构、臆测建议、强制总结或模板化后续邀约。

## 2. 按任务加载参考文件

只加载当前任务需要的文件。小任务直接用本页原则。

| 任务 | 参考文件 |
|---|---|
| 对话、解释、研究、排障、推荐 | `references/anti-generic.md` |
| 编程、调试、重构、代码审查、Agent 执行 | `references/anti-overengineering.md`、`references/software-engineering.md` |
| 幻觉、来源、数据、验证声明 | `references/anti-hallucination.md` |
| 中文 README、技术文档、API 文档、设计文档、变更日志 | `references/documentation.md` |
| UI、网页、SVG、插画、动效、视觉生成 | `references/anti-visual-slop.md` |
| 交付前验收 | `references/quality-verification.md` |

## 3. 中文技术文档硬纪律

默认语言：面向公开仓库与外部读者的文档和提交信息一律英文；中文只用于明确要求、中文受众或维护语言对镜像。本节规则同样强于 `references/documentation.md`，写或改中文 README、使用说明、设计文档、API 文档、变更日志时直接执行，不依赖是否读了 reference。

### 3.1 篇幅预算（硬上限）

| 对象 | 上限 |
|---|---|
| README 主体 | 120 行 / 800 个中文字符 |
| 单个小节 | 15 行 |
| 单个段落 | 4 行 |
| 单个句子 | 40 个中文字符 |
| 标题层级 | 最多 3 层 |

**超出预算就删内容。** 删的是空话和重复，不是信息。表格、代码块、参数映射清单不算正文段落，不受单段 4 行限制。不用缩排、调字号、拆小标题来让行数看起来合规。长尾细节拆到独立文档，README 里放链接。

结构化的多字段信息用表格承载，不要为了压行数把它写成连续长句——那会让读者更难查。这条与「删内容」不冲突：改的是形式，不是删事实。

### 3.2 中文句式黑名单

以下表达默认为空话，出现在正文里就删，或换成具体事实：

`值得注意的` `需要注意的是` `需要指出的是` `总的来说` `综上所述` `总而言之` `众所周知` `显而易见` `不难看出` `至关重要` `不可否认` `毋庸置疑` `正如…所说` `更重要的是` `不仅如此` `焕发出新的活力` `在当今…的时代` `随着…的发展` `不仅…而且` `让我们` `你会发现` `其实` `说白了` `赋能` `助力` `打造` `一站式` `深入浅出` `强大的` `优雅的` `无缝的` `功能强大` `我们`

`开箱即用` 只在描述真实的零配置默认值时保留，作为孤立赞誉时删除。

`不是 X，而是 Y` 只在 X 是抽象概念时判为修辞并改写；排障结论里两侧都是具体失败（如「不是网络故障，而是权限配置错误」）时保留。

收尾客套全删：`希望本文对你有帮助` `如有疑问欢迎交流` `感谢阅读` `相信你已经掌握`。

这些词出现在引用、术语、反例或必要论证中时保留。清单是审查线索，不是机械替换表——见第 4 节末尾。

### 3.3 结构与取舍

- 开篇第一句是定义句（是什么、给谁用），不铺垫动机。
- 读者要做的动作用祈使句写。emoji、感叹号默认为零（面向新用户的一句欢迎除外）；正向文风全貌见 `references/documentation.md` 的极简文风节。
- 先给安装命令和最小示例，再给解释。限制和风险写在相关操作附近。
- 标题用名词短语，不用「关于…」「浅谈…」。
- 列表只用于并列项。能一句话说清的不拆列表。并列且多字段的用表格。
- 每个小节只回答一个问题，每段只表达一个信息点。
- 术语一致：同一概念全篇用同一个词。
- 不写元话语：`本文档旨在` `下面将介绍` `接下来分三点说明`。
- 不加用户没要求的免责声明、最佳实践章节、致谢、路线图、FAQ。

### 3.4 骨架

README 与各类文档的骨架见 `references/readme-skeleton.md`、`references/doc-skeletons.md`。

## 4. 跨领域反模式

- **Filler**：无信息量开场、空洞过渡、重复结论、客套填充。
- **Meta-output**：把任务复述、文档目的声明、内部计划或过程播报塞进交付物；`作为 AI` / `As an AI language model` 这类自指。
- **Unsupported certainty**：无依据的确定语气、虚构引用、未运行却声称通过。
- **Template residue**：仅因模板常见而加入的标题、徽章、卡片、FAQ、免责声明、动画或占位内容。
- **Surface sophistication**：堆砌术语、无必要抽象、装饰性渐变、过量动效、看似高级但不可用的控件。
- **Repetition**：同一事实在正文、表格、列表和总结中重复出现，却没有新增用途。
- **Scope drift**：无关清理、擅自重设计、额外功能、为假想需求提前扩展。

### 多语言黑名单索引

各语言的完整规则在 `scripts/anti_slop_lint.py` 的 `LANG_PACKS`。每个语言包覆盖 filler、meta（含 AI 自指）、closer、overclaim。下表只列典型条目。

| 语言 | 典型条目 |
|---|---|
| 通用 | `100%`、`As an AI language model` |
| zh | 见第 3.2 节 |
| en | `in today's fast-paced digital world`、`as technology continues to evolve`、`delve into`、`testament to`、`beacon of`、`tapestry of`、`revolutionize`、`cutting-edge`、`seamless`、`it is important to note that`、`needless to say`、`at its core`、`in conclusion`、`to summarize` |
| ja | `言うまでもなく`、`現代社会において`、`シームレスな`、`革新的な`、`いかがでしたか`、`お役に立てれば幸いです` |
| ko | `말할 필요도 없이`、`오늘날의 빠르게 변화하는`、`원활한 통합`、`혁신적인`、`도움이 되셨기를 바랍니다` |
| de | `Es ist wichtig zu beachten, dass`、`In der heutigen schnelllebigen Welt`、`nahtlos`、`Ich hoffe, das hilft` |
| fr | `Il est important de noter que`、`Dans le monde d'aujourd'hui`、`sans couture`、`J'espère que cela vous aide` |
| es | `Es importante señalar que`、`En el mundo actual`、`sin fisuras`、`Espero que esto te ayude` |
| ru、pt | 未覆盖，只有通用包 |

`robust` 只在缺少误差界、容错模型或基准数据时判为营销词；`robust error bound` / `robust estimator` / `robust outlier handling` 属于准确术语。其他语言的对应词（如 `robuste`、`robusto`）未入库。

营销形容词绑定具体名词时视为事实，不报：`nahtlose Migration`、`hochmoderne Anlage`、`最先端の技術`、`シームレスな統合`、`최첨단 기술`、`sans couture de`、`de vanguardia en`。裸用时才报。

中文文档额外加载英文包：中文技术文档里夹 `seamless` / `delve into` 需要被检出。其他语言不叠加别的语言包。

短语黑名单和正则只提供审查线索，不能单独判定内容低质。引用、讨论、反例、术语中的短语可能完全合理。

## 5. 技术文档事实核对

文档描述的是它所在代码树的实现。本节适用于任何语言的文档，与第 3 节并列；执行细节见 `references/documentation.md`。

- **操作性声明逐条核对。** 命令、动词、旗标、默认值、数量、路径、配置键写入前必须对照本树实现（`file:line` 或实际输出）。核对是双向的：文档→代码，不写不存在的东西；代码→文档，用 CLI 派发表或 argparse 注册比对文档命令表，用户可见的动词和旗标不漏记。
- **计数用脚本，不用印象。** 「共 N 个」「保留 N 份」这类声明用 `ls | wc -l`、`grep -c` 数出来再写。
- **移植的文档不继承事实。** 从上游、旧版本或他人分支移植文档时，源树为真不代表本树为真。每条声明按本树重新核对；对不上就改文档或先改代码。无法本地核对的，写明适用于哪个版本，不冒充本地事实。
- **多语言镜像事实一致。** 语言对（`README.md` ↔ `README.zh-CN.md`、`Page` ↔ `Page-zh`）的散文可以不同，数字、命令、旗标、列表项、结构必须一一对应；改事实先改两个语言版本。
- **术语以代码为准绳。** 同一文档集（README ↔ wiki ↔ CLI usage 字符串 ↔ 报错信息）里同一概念用同一个词，锚定代码中的 user-facing 字符串。
- **对照版本差异时逐 hunk 裁决。** fork 与上游、新旧版本 diff 审查时，判定标准是「哪边符合当前代码树」，不是哪边更新、哪边更好听。

## 6. 交付前检查

- [ ] 用户要求的结果已交付，没有悄悄遗漏。
- [ ] 关键事实有依据；推断和未知已标明。
- [ ] 没有编造文件、命令、API、数据、引用、功能或验证结果。
- [ ] 操作性声明（命令、旗标、计数、默认值、路径）已对照同树代码逐条核验，能给出 `file:line` 或实际输出（第 5 节）。
- [ ] 多语言版本与文档集内的事实数字、命令、术语一致（第 5 节）。
- [ ] 中文文档已满足第 3 节全部预算。
- [ ] 没有套话、重复内容、过程泄漏或模板残留。
- [ ] 复杂度、篇幅、格式和视觉效果与任务相称。
- [ ] 已按交付物类型验证；未验证部分准确标为 Blocked 或 Not Run。
- [ ] 没有无关改动，最终 diff / 成品已检查。

检查表用于发现风险，不是拖延简单任务或机械删改的理由。

## 7. 文本 Linter

两个 profile，规则集不同。语言包按文档主语言选择，`--lang` 可强制指定。

**general**：查跨领域套话，加载全部语言包；不适用中文文档黑名单和篇幅预算。

```bash
python scripts/anti_slop_lint.py path/to/file.md
```

**zh-doc**：完整启用第 3 节规则，含 120 行 / 800 字 / 40 字预算和中文黑名单。只加载通用包和 zh 包。

```bash
python scripts/anti_slop_lint.py --profile zh-doc README.md
```

**--pair**：对照语言对，检查标题数、表格行数和正文数字是否一致（第 5 节的机械部分）。围栏和行内代码不参与比对——代码块里的计数声明归第 5 节的声明核对流程。主文件写第一个路径，`--pair` 可重复。

```bash
python scripts/anti_slop_lint.py README.md --pair README.zh-CN.md
```

其他选项：

```bash
python scripts/anti_slop_lint.py --json README.md
python scripts/anti_slop_lint.py --lang de docs/
python scripts/anti_slop_lint.py --strict README.md
python scripts/anti_slop_lint.py --ignore-regex '^> ' README.md
python -m unittest discover -s tests -v
```

Linter 是提示器，不是事实核查器——它查不出声明是否与实现相符，第 5 节的核对流程无法被它替代。它也不能评价代码架构、视觉品味或内容是否真正有用。逐条审查告警；不要为了让输出归零而破坏必要内容。
