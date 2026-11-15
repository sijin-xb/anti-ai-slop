# portmap

把本机端口转发到远端主机的极简工具。

## 安装

```bash
paru -S portmap
```

## 用法

```bash
portmap add 8080 remote:80
portmap list
portmap rm 8080
```

`add` 立即建立转发并在 systemd user unit 中注册，重启后自动恢复。`rm` 只删除转发，不清理已建立的连接。

## 配置文件

配置位于 `~/.config/portmap/config.toml`：

```toml
[defaults]
host = "example.com"
keepalive = 30
```

`keepalive` 单位是秒。设为 0 关闭心跳，此时空闲连接会在服务端超时后断开。

## 已知限制

- 只支持 TCP，不支持 UDP。
- 远端需要允许 SSH 端口转发。
- 同一端口不能同时映射到两个目标，`add` 会报错而不是覆盖。

## 排障

连接建立后立即断开时，先确认远端 `AllowTcpForwarding` 为 `yes`。日志：

```bash
journalctl --user -u portmap -n 50 --no-pager
```
