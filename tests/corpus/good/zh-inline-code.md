# 部署流程

把 `config.toml` 安装到 `/etc/app/` 后重启服务：

```bash
sudo install -m 0644 config.toml /etc/app/config.toml
sudo systemctl restart app.service
```

健康检查返回 `{"status":"ok"}` 表示进程就绪。此时迁移可能仍在进行，`/api/v1/items` 在迁移完成前返回 503。

日志由 systemd 收集，查看最近 200 行：

```bash
journalctl -u app.service -n 200 --no-pager
```

常见失败按现象查：进程启动即退出时先确认配置文件大小写；端口占用时用 `ss -ltnp | grep 8080` 定位；健康检查通过但接口 503 时等待迁移或查看 `/var/log/app/migrate.log`。
