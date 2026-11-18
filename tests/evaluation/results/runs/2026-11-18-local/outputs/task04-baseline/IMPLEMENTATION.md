实现说明（task-04-svg-hero）
1. 机制：单文件 SVG（1200×600）内嵌 `<style>`，无脚本；默认浅色，深色经 `@media (prefers-color-scheme: dark)` 覆盖颜色类实现两套配色。
2. 动效：总长 6s 的纯 CSS keyframes 入场序列——外环 stroke-dashoffset 描画（0–1.4s）→ 中环/内环/标签图形缩放浮现（0.35–2.4s）→ 强调条、标题、副标题位移淡入（2.6–4.8s）→ 三个节点圆点收尾（5.0–6.0s）；`animation-fill-mode: both` 保证延迟期隐藏、结束后停在终态。
3. 减弱动态：`@media (prefers-reduced-motion: reduce)` 下移除全部动画，各元素的无动画默认属性即为可见终态，静态呈现完整画面。
4. 未测：未实测任何浏览器/渲染器的渲染性能与帧率（性能数字：未测量），也未验证各渲染器对 CSS transform-box / 动画的兼容程度。
5. 文案仅使用题面给定的标题与副标题，未添加用户数、下载量等任何虚构数据。
