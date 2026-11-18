# hero.svg 实现说明

- 1200×600 自包含 SVG；浅色为默认配色，深色由 `@media (prefers-color-scheme: dark)` 中的类选择器覆盖，未用 CSS `var()`（librsvg 2.63.4 对 `var()` 渲染为空白）。
- 入场序列播放一次、总长 6s：标题升起（0.3–1.9s）→ 副标题（1.1–2.5s）→ 标签图形描边（2.6–5.2s，`stroke-dashoffset`）→ 圆点弹出（5.2–6.0s）；均为 CSS keyframes，配 `animation-fill-mode: both`。
- `prefers-reduced-motion: reduce` 下禁用全部动画，直接呈现终帧。
- 文案只用题给标题与副标题，无其他数字、统计或装饰元素。
- 验证：`xmllint` 通过；rsvg-convert 静态渲染与 Chromium 截图（浅色、深色、深色+reduced-motion、t≈0.6/1.7/4.4/6.6s 中间帧）均目视检查通过。加载性能与动画帧率未测量。
