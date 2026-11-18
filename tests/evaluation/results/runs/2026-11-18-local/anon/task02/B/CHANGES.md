# 改动说明

1. 删 ChannelFactory/ChannelKind/ChannelConfig/NotificationChannel ABC/Sendable Protocol：渠道只有 email、slack 两个固定实现；registry 无任何 register 调用，create 必然抛 ValueError，违反「渠道不可用不抛异常」契约；改为两个模块级发送函数。
2. 删 NotificationPipeline 与 DEFAULT_BATCH_SIZE：分批切片不影响去重、渠道顺序或返回值，属无行为收益的结构开销，改为直接遍历 events。
3. 删 MAX_CHANNELS：渠道数恒为 2，截断是死配置。
4. 删 ChannelConfig 的 enabled/retries/options 字段：取值恒定且从未被读取。
5. 保留 _deliver_email/_post_slack 未配置桩与 except 捕获：承接「发送失败返回 False」契约；函数名不变，测试注入点不受影响。
6. 保留去重写入时机（仅发送成功后记录 event.id）：对应「同一轮只发一次」，失败不算发送，重复出现的失败事件按原实现重试。
7. 渠道顺序 email→slack、每个事件首个成功渠道即停、任一事件发送成功返回 True，与原实现一致。
