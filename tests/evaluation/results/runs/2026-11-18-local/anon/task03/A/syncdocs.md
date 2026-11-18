# syncdocs 使用说明

syncdocs 把源目录下的 Markdown 文件单向复制到目标目录，含子目录。目标端缺失或修改时间早于源端的文件会被复制。

## 安装

无第三方依赖，仅用标准库（argparse、sys、pathlib）。脚本不带 shebang，用 `python3` 运行。

## 用法

```bash
python3 syncdocs.py ./docs-en ./docs-zh
```

| 旗标 | 行为 |
|---|---|
| `--interval` | 默认 30。已注册但程序未读取，无轮询，每次运行只同步一次 |
| `--retries` | 默认 2。已注册但程序未读取，复制出错直接抛异常，无重试 |
| `--dry-run` | 只打印待同步文件的源路径，不做修改，返回 0 |
| `--delete` | 删除目标端在源端已不存在的 `.md` 文件 |

## 退出码

- 0：同步成功，`--dry-run` 同样返回 0
- 1：仅当复制抛出未捕获异常（如源文件不可读）时出现，随 traceback 返回；没有部分失败处理逻辑
- 2：源目录或目标目录不存在

## 注意

目标目录本身必须预先存在，缺失时返回 2。目标端缺失的子目录会在复制时自动创建。

## 核对记录

行号指素材版 `syncdocs.md`；`syncdocs.py:x` 指素材实现。证据等级：标注「实测」的条目附实际命令输出，其余为源码级核对（`file:line`）。

| 原文 | 原声明 | 核对 | 结果 |
|---|---|---|---|
| :3 | 在两个目录之间同步，按修改时间判断 | `syncdocs.py:22` 递归 `rglob("*.md")`；`:25` 目标缺失或 `mtime` 早于源端才复制；`:47-51` 单向复制 | 不一致已改：实为源→目标单向复制，目标缺失也复制 |
| :7 | 放进 PATH 即可，无第三方依赖 | `syncdocs.py:1-3` 仅导入 argparse、sys、pathlib；`:1` 起无 shebang 行 | 部分不一致已改：依赖属实；缺 shebang，改为 `python3` 运行 |
| :12 | 示例含 `--interval 60` | 实测 `--help`（exit 0）确认参数可解析；`args.interval` 全文未被读取 | 不一致已改：示例去掉无效旗标 |
| :15 | `--interval` 默认 10 秒，最小 5 秒 | `syncdocs.py:5` `DEFAULT_INTERVAL = 30`；`:13` 注册；全文无最小值校验、无轮询循环 | 不一致已改：默认 30，无最小值，程序不使用 |
| :17 | `--retries` 控制重试，默认 3 次 | `syncdocs.py:6` `DEFAULT_RETRIES = 2`；`:14` 注册；`args.retries` 全文未读取；`:47-51` 复制无异常处理 | 不一致已改：默认 2，无重试逻辑 |
| :19 | `--dry-run` 只列出，不修改 | `syncdocs.py:41-44` 逐行打印后 `return 0`；实测输出见下 | 一致 |
| :21 | `--prune` 删除目标端多余文件 | `syncdocs.py:16` 旗标名为 `--delete`（实测 `--help` 确认）；`:52-57` 仅删除 `*.md` | 不一致已改：旗标名与删除范围 |
| :25 | 退出码 0：同步成功 | `syncdocs.py:44`、`:60`；实测同步、空跑均 exit 0 | 一致 |
| :26 | 退出码 1：部分文件同步失败 | `syncdocs.py:46` `failures = 0`、`:57` `failures += 0`，`:58-59` 分支不可达；实测源文件不可读时 PermissionError，解释器 exit 1 | 不一致已改：1 仅由未捕获异常产生 |
| :27 | 退出码 2：源/目标目录不存在 | `syncdocs.py:33-38`；实测缺失目录 exit 2 | 一致 |
| :31 | 目标目录必须预先存在，不会自动创建 | `syncdocs.py:36-38` 根目录缺失返回 2；`:50` `mkdir(parents=True)` 自动创建子目录 | 部分不一致已改：目标内子目录会自动创建 |
| 补漏 | — | 实测 `--help`：argparse 注册 source、target、`--interval`、`--retries`、`--dry-run`、`--delete` 共 6 项 | 修正后文档已全部覆盖 |

实测输出（证据，`syncdocs.py` 位于素材目录，`-I` 隔离运行）：

```text
$ python3 -I syncdocs.py --help
usage: syncdocs [-h] [--interval INTERVAL] [--retries RETRIES] [--dry-run]
                [--delete]
                source target
options:
  --interval INTERVAL  轮询间隔秒数
  --retries RETRIES    单文件失败重试次数
  --dry-run            只列出将同步的文件
  --delete             删除目标端多余文件
（exit 0）

$ python3 -I syncdocs.py src tgt --dry-run      # tgt/a.md、tgt/sub/b.md 均缺失
src/a.md
src/sub/b.md
（exit 0）

$ touch -d '2020-01-01' tgt/a.md && python3 -I syncdocs.py src tgt --dry-run
src/a.md                                        # 目标更旧，重新列入；mtime 相同时输出为空

$ python3 -I syncdocs.py src tgt --interval 5 --retries 9
（exit 0；tgt/sub/b.md 由程序自动建目录生成，两个旗标无可观察效果）

$ python3 -I syncdocs.py src tgt-nodir
target not a directory: tgt-nodir
（exit 2）

$ python3 -I syncdocs.py src tgt --delete       # tgt/extra.md 在源端不存在
（exit 0；extra.md 已删除）

$ chmod 000 src/a.md && python3 -I syncdocs.py src tgt
PermissionError: [Errno 13] Permission denied: 'src/a.md'
（exit 1，解释器 traceback，无重试）
```
