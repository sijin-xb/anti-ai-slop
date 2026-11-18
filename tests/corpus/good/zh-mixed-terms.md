# exporter-sdk

自定义指标导出 SDK 的接入约定。

## 接入步骤

1. 在构建脚本中加入依赖 `exporter-sdk 2.3.x`，版本号跟随主服务。
2. 初始化时传入 `service_name` 与 `push_gateway` 两个参数。
3. 启动后访问 `/metrics` 确认输出包含 `exporter_build_info`。

## 指标命名

指标名必须以 `app_` 开头，单位写在后缀：`_seconds`、`_bytes`、`_total`。标签数量不超过 8 个，`instance` 与 `job` 由抓取端注入，不要手动设置。

直方图桶默认覆盖 1ms 到 10s。如果接口 P99 长期超过 10s，先确认是不是把重试也计入了时延，再考虑自定义桶边界。

## 中英混合写法

`oauth2_token_refresh_total` 这类计数器在刷新失败时加 1；JWT 过期导致的 401 计入 `auth_failures`，与网络错误分开。RFC 7231 时间戳由网关统一转换，SDK 内部不做时区假设。
