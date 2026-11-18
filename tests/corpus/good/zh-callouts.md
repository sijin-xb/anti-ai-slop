# relay-worker

任务队列中继服务：把上游 webhook 事件转入内部队列，供下游按组消费。

## 配置

| 参数 | 默认值 | 说明 |
|---|---|---|
| `listen` | `127.0.0.1:8080` | 监听地址 |
| `bucket` | `relay` | 上游 bucket 名称 |
| `workers` | `4` | 消费进程数 |

## 部署

```bash
relay-worker --config /etc/relay/worker.toml
```

> [!WARNING]
> 修改 `bucket` 后必须重启，运行中不会重新加载。

配置校验失败时进程退出码为 2，日志输出第一个错误的字段名与期望格式。

## 排障

启动失败常见于两类：这不是权限问题，而是配置文件路径写错；另一种是 bucket 凭据过期，报错信息会带 `AuthError` 前缀。

<!--
下游团队接入步骤维护在 runbook 仓库，此处不放重复内容。
-->

事件去重键是 `event_id` 加来源组，重复投递在同一组内只消费一次。
