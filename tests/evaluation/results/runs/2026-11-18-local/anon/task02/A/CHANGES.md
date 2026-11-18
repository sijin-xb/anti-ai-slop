改动说明（每项删改对应真实约束/契约）
1. 删 ChannelFactory/ChannelKind/ChannelConfig：工厂注册表从未 register 过任何渠道，原 send_user_digest 首次调用即抛 ValueError，直接违反"渠道不可用不抛异常"契约；真实渠道只有 email/slack，改为两个发送函数按固定顺序调用。
2. 删 NotificationChannel ABC 与 Sendable Protocol：Protocol 全程无人引用，ABC 的抽象方法 kind() 只服务于工厂注册，两者是对同一抽象的重复表达。
3. 删 NotificationPipeline 与 batch_size=32：batch 切分不改变任何逐事件行为（去重集合跨 batch 共享），是无效果的包装层。
4. 删 MAX_CHANNELS、retries、enabled、options、DEFAULT_BATCH_SIZE：enabled 恒为 True，retries/options 无任何读取方，MAX_CHANNELS/DEFAULT_BATCH_SIZE 对实际数据（2 渠道、无截断需求）不生效。
5. 保留并核对契约行为：try/except + logging 覆盖传输层异常（契约 2）；event["id"] 去重、仅当渠道真正发送成功才记为已发、成功后不再尝试其余渠道、"[digest] {title}" 与 body 取值格式不变（契约 1、3 及既有输出格式）；_deliver_email/_post_slack 是传输层接缝，保持原样。
