# getcfg

用点分键从 JSON 配置文件里读取单个值。

## 安装

把 `getcfg.py` 放进 PATH，无第三方依赖。

## 用法

```bash
getcfg server.port --file /etc/app/config.json
```

`--format raw` 输出值本身，不加 JSON 引号；默认 `json`。

`--timeout` 限制读取超时，默认 30 秒。

`--default VALUE` 在键缺失时输出该值，退出码为 0。

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 找到键（或使用了默认值） |
| 1 | 键不存在 |
| 3 | 配置文件缺失或 JSON 无效 |

## 注意

数组无法用下标寻址；请取父键后自行解析 JSON 数组。配置文件不存在时工具会自动创建一个空配置。
