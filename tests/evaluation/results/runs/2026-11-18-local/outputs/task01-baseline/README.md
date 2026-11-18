# inventory

单文件库存命令行工具：`add` 新增/累加、`take` 扣减、`list` 列出，全部数据存在一个 JSON 文件里。

## 安装

需要 Python 3.10 及以上，仅用标准库，无第三方依赖。把 `inventory_cli.py` 放到任意目录即可：

```bash
cp inventory_cli.py ~/bin/   # 或任意你想放的位置
cd ~/bin
```

## 快速上手

```bash
python inventory_cli.py add SKU-001 --qty 100    # 新增条目，货位默认 A1
python inventory_cli.py add SKU-001 --qty 20     # 同一 SKU 再加 20，货位仍是 A1
python inventory_cli.py take SKU-001 --qty 30    # 扣减 30
python inventory_cli.py list
```

`list` 输出（SKU、数量、货位，以制表符分隔，按 SKU 排序）：

```
SKU-001	90	A1
```

数据默认写在当前目录的 `inventory.db`，首次 `add` 时自动创建。

## 命令

用法：`python inventory_cli.py [--db 路径] {add,take,list} ...`（`-h` / `--help` 查看帮助，帮助里的程序名显示为 `inventory`）。

全局参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--db 路径` | `inventory.db` | JSON 库文件路径。**必须写在子命令之前**，写在子命令后面会报 `unrecognized arguments` 并以退出码 2 结束 |

### add — 新增或累加

```
python inventory_cli.py add SKU --qty 数量 [--location 货位]
```

- `--qty` 必填，整数。
- `--location` 可选，默认 `A1`。
- SKU 不存在时新建条目；已存在时数量累加，并把货位**改写**为本次给定的值——省略 `--location` 会把货位重置回默认的 `A1`。
- 成功退出码 0。

### take — 扣减

```
python inventory_cli.py take SKU --qty 数量
```

- `--qty` 必填，整数。
- SKU 不存在：向 stderr 输出 `unknown sku: SKU`，退出码 1，不写库。
- 库存不足：向 stderr 输出 `insufficient stock: SKU`，退出码 1，库不变。
- 成功则扣减并写库，退出码 0。

### list — 列出

```
python inventory_cli.py list
```

- 按 SKU 字典序输出 `SKU<TAB>数量<TAB>货位`。
- 库文件不存在或为空时无任何输出，退出码 0；`list` 不会创建库文件。

## 数据文件

JSON 数组，UTF-8，2 空格缩进，非 ASCII 字符原样保存（中文 SKU、货位可直接阅读）：

```json
[
  {
    "sku": "SKU-001",
    "qty": 90,
    "location": "A1"
  }
]
```

- 条目字段：`sku`（字符串）、`qty`（整数）、`location`（字符串）。
- 新条目按 `add` 顺序追加；`list` 的排序只是输出顺序，不改动文件。
- 库文件不存在时视为空库；文件内容不是合法 JSON 时会抛出未捕获的异常并以退出码 1 结束。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | add / take / list 成功；`-h`、`--help` |
| 1 | take 失败（SKU 不存在或库存不足）；库文件不是合法 JSON |
| 2 | 用法错误：缺子命令、缺 `--qty`、`--qty` 不是整数、未知参数、`--db` 写在子命令之后 |

## 边界行为

- `--qty` 不做符号校验，负数会被接受：`add --qty -5` 等于扣减，`take --qty -5` 等于增加。
