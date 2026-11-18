# Task 05 核对记录

事实来源：`materials/getcfg.py`（52 行，行号均指该文件）。
核对对象：`materials/README.md`、`materials/README.zh-CN.md`。
交付：修正后的 `README.md`、`README.zh-CN.md` 与本记录。

## 一、修改项

### 1. `--timeout` 段落（两版均改）

- 原文：EN 称 "--timeout sets a ceiling of 15 seconds for file reads"；ZH 称 "限制读取超时，默认 30 秒"。
- 问题：`args.timeout` 解析后从未被使用，代码不会对读取实施任何超时；ZH 的默认值 30 也与代码不符。
- 依据：第 7 行（`DEFAULT_TIMEOUT = 15`）、第 17 行（定义 `--timeout`）；第 19–47 行（main 函数体）中没有任何对 `args.timeout` 的引用。
- 修正：两版均改为"旗标被接受但不起作用，读取不设超时；默认值 15"。

### 2. 退出码表 3 → 2（仅 ZH）

- 原文：ZH 表中 "3 | 配置文件缺失或 JSON 无效"。
- 问题：不存在退出码 3；文件缺失与 JSON 无效都返回 2。
- 依据：第 9 行（`EXIT_INVALID = 2`）、第 21–24 行（文件缺失 → `EXIT_INVALID`）、第 28–30 行（JSON 解析失败 → `EXIT_INVALID`）。
- 修正：ZH 改为 2，与 EN 及代码一致。

### 3. 删除"自动创建空配置"说法（仅 ZH）

- 原文：ZH "注意"末尾 "配置文件不存在时工具会自动创建一个空配置"。
- 问题：文件缺失时代码只打印错误并返回 2，从不创建文件。
- 依据：第 21–24 行（`if not path.is_file(): ... return EXIT_INVALID`）。
- 修正：删除该句。

### 4. `--format raw` 对容器值的行为（两版均改）

- 原文：EN "prints the value without JSON quoting"；ZH "输出值本身，不加 JSON 引号"。
- 问题：仅对标量成立；dict/list 值在 raw 模式下仍按 JSON 打印。
- 依据：第 43–44 行（raw 分支对 dict/list 走 `json.dumps`）、第 46 行（json 分支同样 `ensure_ascii=False`，故容器值两格式输出一致）。
- 修正：两版补充"字典与列表的值仍按 JSON 打印"。

## 二、核对无误、保持原样的内容

| 内容 | 依据 |
|---|---|
| 标题 `getcfg`、示例命令 `getcfg server.port --file /etc/app/config.json` | 第 13 行（prog="getcfg"）、第 14 行（键示例 server.port）、第 15 行（--file） |
| 无第三方依赖 | 第 1–4 行（argparse/json/sys/pathlib 均为标准库） |
| `--format` 可选 json/raw，默认 `json` | 第 6 行、第 16 行 |
| `--default VALUE`：键缺失时输出该值，退出码 0 | 第 18 行、第 37–39 行（print 后 `return 0`） |
| 退出码 0（找到键或用默认值）、1（键不存在） | 第 8 行（`EXIT_NOT_FOUND = 1`）、第 40–41 行、第 47 行 |
| EN 退出码 2 行 "config file missing or invalid JSON" | 第 9、21–24、28–30 行 |
| "注意"：数组无法按下标寻址，取父键后自行解析 | 第 33–35 行（逐级下钻仅匹配 dict，list 不支持索引） |
| 小节结构：Intro / Install / Usage / Exit codes / Notes | 两版一一对应，未增删小节 |

## 三、已知但未采纳的补充

- `--file` 默认值 `config.json`（第 15 行）原文未提及。两版原文均未写，不属分叉点；按最小修改原则未新增，避免多余内容。若需补充，应两版同步。
