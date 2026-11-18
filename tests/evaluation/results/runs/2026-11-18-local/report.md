# Run 2026-11-18-local — 首轮自动化评估

模型评标自动化轮（非人工盲评；按 tests/evaluation/README.md，模型评分只作辅助信号，人工复核仍待执行）。

## 方法

- 执行者：10 个全新子代理（5 任务 × Baseline/Treatment）。Baseline 明确禁止加载任何 skill；Treatment 被要求完整阅读 SKILL.md 并按 §2 路由加载 references。两侧都只允许读任务文件与素材。
- 评标：5 个独立盲评代理，输出匿名化为 A/B（映射见 mapping.json，A/B 交错），评标员不知道来源。事实准确性维度强制实测（运行 fixture、Chromium 渲染截图等）。
- 触发验证：11 个只看 description 的全新代理做二选一决策（trigger-results.json）。
- 局限：单一模型家族（与编排代理同源）、平台默认采样参数不可控、每格单样本、评标员为同模型代理。结果方向性参考，非统计结论。

## 交付物级结果（九维，0-2；视觉 N/A 不计分）

| 任务 | A | B | 得分 | 分差维度 |
|---|---|---|---|---|
| task01 zh README | treatment | baseline | 15 : **16** | 任务完成度：baseline 覆盖了损坏 JSON/建库时机/help 退出码等边界 |
| task02 重构 | baseline | treatment | **15** : **15** | 平手：A 丢任务完成度（删除 import 未映射进说明），B 丢事实准确性（"enabled 从未读取"与 :117 相悖） |
| task03 事实核对 | treatment | baseline | 15 : **16** | 事实准确性：treatment 的实测输出三处按其步骤无法精确复现 |
| task04 SVG hero | baseline | treatment | **18** : 17 | 事实准确性：treatment 记录「librsvg 渲染 var() 为空白」复测为不透明黑而非空白 |
| task05 镜像同步 | treatment | baseline | **16** : 15 | 事实准确性：baseline 核对记录写「52 行」实为 51 行 |
| **合计** | | | **78 : 80** | |

逐项明细见 judgments/task0N.json；原始产出（未匿名）见 outputs/taskNN-{baseline,treatment}/。

## 主要发现

1. **交付物事实质量两侧都高**：10 份产出经评标员实测（含实跑 CLI、26 项契约检查、16 张渲染截图）均无编造的命令、API 或数据。task03 两侧都找齐了全部 7 处预埋不符。
2. **全部 5 处分差集中在任务完成度/事实准确性，其中 4 处是「验证记录里的叙述被复测推翻」**——交付物本身是对的，错在证据叙述不精确（印象性措辞、行号笔误）。这说明：验证纪律提升了核对行为，但验证记录自身成为新的声明面。已据此在 `references/quality-verification.md` 增补「验证记录也是声明」条目。
3. **执行成本显著**：token 消耗 treatment ≈ 2.46M vs baseline ≈ 0.83M（约 3 倍）；时长约 1477s vs 878s。主要来自实跑 fixture 与渲染验证。这符合 Skill 的成本纪律吗？rubric 的执行成本维度评的是交付物内的过程噪音（两侧都是 2 分），agent 层面的资源消耗是本 run 级观察，供使用者权衡。
4. **任务完成度反向案例（task01）**：baseline 覆盖了更多退出码边界。单例不足为凭，但提示「预算纪律可能挤压边界枚举」，后续轮次应关注。

## 触发验证

11/11 与预期一致（8 正类全「调用」，3 负类全「不调用」），理由均引用 description 中的对应条款。详见 trigger-results.json。

## 验证状态

- 10 份交付物产出与落盘：Passed
- 5 份盲评 JSON 落盘且结构完整：Passed
- 触发验证 11 条完成：Passed
- 人工盲评复核：Not Run（本轮为模型评标，按协议人工复核不可省略）
- 统计显著性：Not Applicable（每格单样本）
