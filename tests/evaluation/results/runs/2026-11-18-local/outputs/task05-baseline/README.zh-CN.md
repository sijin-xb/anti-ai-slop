# getcfg

用点分键从 JSON 配置文件里读取单个值。

## 安装

把 `getcfg.py` 放进 PATH，无第三方依赖。

## 用法

```bash
getcfg server.port --file /etc/app/config.json
```

`--format raw` 对标量值不加 JSON 引号、直接输出；字典与列表的值仍按 JSON
打印。默认 `json`。

`--timeout` 会被接受但不起作用：读取不设超时限制。默认值为 15。

`--default VALUE` 在键缺失时输出该值，退出码为 0。

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 找到键（或使用了默认值） |
| 1 | 键不存在 |
| 2 | 配置文件缺失或 JSON 无效 |

## 注意

数组无法用下标寻址；请取父键后自行解析 JSON 数组。
