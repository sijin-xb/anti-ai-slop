# inventory

基于单个 JSON 库文件的命令行库存工具，按 SKU 记录数量与库位。适合个人或小团队手工记账出入库。

## 快速开始

需要 Python 3.10 及以上。把 `inventory_cli.py` 放到任意目录即可运行，无第三方依赖。

```console
$ python inventory_cli.py add SKU-100 --qty 5 --location B2
$ python inventory_cli.py take SKU-100 --qty 2
$ python inventory_cli.py list
SKU-100	3	B2
```

`list` 输出每行一条记录，制表符分隔 SKU、数量、库位，按 SKU 排序。`add` 和 `take` 成功时无输出。

## 命令

全局参数 `--db PATH` 指定库文件路径，默认 `inventory.db`，必须写在子命令之前。

### add

| 参数 | 说明 |
|---|---|
| `sku` | 位置参数，条目标识 |
| `--qty` | 必填，整数，变动数量 |
| `--location` | 库位，默认 `A1` |

SKU 不存在时新增条目；已存在时数量累加，库位覆盖为本次 `--location` 值。

### take

| 参数 | 说明 |
|---|---|
| `sku` | 位置参数，条目标识 |
| `--qty` | 必填，整数，扣减数量 |

SKU 不存在时输出 `unknown sku: SKU-100`；扣减量超过现有数量时输出 `insufficient stock: SKU-100`。两种失败都写入 stderr，退出码 1，库文件不变。

### list

无参数。库文件不存在或为空时无输出，退出码 0。

## 库文件格式

JSON 数组，每个元素一个条目：

```json
[
  {
    "sku": "SKU-100",
    "qty": 3,
    "location": "B2"
  }
]
```

文件不存在视为空库；`add` 和 `take` 成功后整体写回，UTF-8 编码，缩进 2。

## 退出码

| 退出码 | 条件 |
|---|---|
| 0 | 成功，含空库执行 `list` |
| 1 | `take` 库存不足或 SKU 不存在 |
| 2 | 用法错误：缺少参数、未知子命令、`--db` 写在子命令之后 |

## 已知限制

- 对已有条目执行 `add` 且未给 `--location` 时，库位被重置为默认值 `A1`。
- `--qty` 不做正负校验，负数会反向改动库存。
