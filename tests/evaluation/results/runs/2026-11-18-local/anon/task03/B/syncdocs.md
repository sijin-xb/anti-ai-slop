# syncdocs 使用说明

syncdocs 把源目录下所有 Markdown（`*.md`，含子目录）文件一次性复制到目标目录：目标端不存在或修改时间早于源端的文件会被覆盖，其余跳过。脚本每次运行只同步一遍即退出，不做常驻轮询。

## 安装

无第三方依赖，只用 Python 3 标准库（argparse、sys、pathlib）。用 `python3 syncdocs.py` 运行；如需作为命令直接调用，要先给文件加上 Python shebang 行和可执行权限再放入 PATH——原文件没有 shebang，直接放进 PATH 无法执行。

## 用法

```bash
syncdocs ./docs-en ./docs-zh
```

可选参数：

- `--interval N`：轮询间隔秒数，默认 30。当前版本只同步一次就退出，该参数解析后并未使用，不产生任何效果；数值也没有下限校验，0 和负数都会被接受。
- `--retries N`：单文件失败重试次数，默认 2。当前版本没有实现重试逻辑，该参数同样不起作用；复制失败时脚本直接崩溃退出。
- `--dry-run`：只列出将要同步的文件，不做任何修改。
- `--delete`：删除目标端在源端已不存在的 `.md` 文件。

## 退出码

- 0：同步成功（含 `--dry-run`）。
- 1：不会作为"部分文件同步失败"返回；仅当复制过程中抛出未捕获异常（如权限不足）时进程才以 1 退出，此时出错文件之后的文件不再同步，也没有重试。
- 2：源目录或目标目录不存在；命令行参数错误时 argparse 也返回 2。

## 注意

- 源目录和目标目录本身必须预先存在，工具不会创建；但目标目录下缺失的子目录会在复制文件时自动创建。
- 只处理 `*.md` 文件，其他扩展名一律忽略。
- 同步方向固定为源 → 目标：目标端比源端新的文件不会被旧内容覆盖。

---

## 核对记录

以下逐条核对原文档的操作性声明。代码行号指 `materials/syncdocs.py`；实测均在 Python 3.14 下完成。

| # | 原文档声明 | 结论 | 依据 |
|---|-----------|------|------|
| 1 | "在两个目录之间同步 Markdown 文件，按修改时间判断" | 属实，可补充细节 | syncdocs.py:22 递归 `rglob("*.md")`；syncdocs.py:25 仅当目标缺失或目标 mtime 早于源时复制。实测：更新源后 dry-run 列出 `src/a.md`；目标文件追加内容变新后不再列出，且未被覆盖 |
| 2 | "把 syncdocs.py 放进 PATH 即可" | 不符 | syncdocs.py:1 首行为 `import argparse`，无 shebang。实测 `PATH=… syncdocs --help` 运行 5 秒无任何输出，被 timeout 杀死（exit=124）。修正为：需补 shebang 或用 `python3` 调用 |
| 3 | "无第三方依赖" | 属实 | syncdocs.py:1-3 仅 `argparse`、`sys`、`pathlib`，均为标准库 |
| 4 | 用法示例 `syncdocs ./docs-en ./docs-zh --interval 60` | 命令本身可运行，但 `--interval` 无效果 | 见第 5 条 |
| 5 | "`--interval` 控制轮询间隔，默认 10 秒，最小 5 秒" | 三处不符 | ① 默认 30：syncdocs.py:5、13，`--help` 实测；② 无最小值校验：实测 `--interval 0`、`--interval -3` 均正常执行 exit=0；③ 并无轮询：main（syncdocs.py:30-60）无循环，参数解析后从未被使用（`grep -n "interval"` 仅命中 :13），实测 `--interval 60` 运行耗时 0.041s 即退出 |
| 6 | "`--retries` 控制单个文件失败后的重试次数，默认 3 次" | 不符 | ① 默认 2：syncdocs.py:6、14；② 无重试逻辑：参数解析后从未被使用（`grep -n "retries"` 仅命中 :14）；实测复制失败直接抛 `PermissionError` 崩溃，无任何重试 |
| 7 | "`--dry-run` 只列出将要同步的文件，不做任何修改" | 属实 | syncdocs.py:41-44 打印待同步路径后直接返回 0。实测目标目录无变化，exit=0 |
| 8 | "`--prune` 删除目标端在源端已不存在的文件" | 参数名不符 | 实际参数为 `--delete`：syncdocs.py:16、52，`--help` 实测无 `--prune`。行为属实但仅针对目标端 `.md` 文件（syncdocs.py:53）。实测：目标端新建 `stale.md` 后运行 `--delete`，该文件被删除，exit=0 |
| 9 | "退出码 0：同步成功" | 属实 | syncdocs.py:60；实测同步与 dry-run 均 exit=0 |
| 10 | "退出码 1：部分文件同步失败" | 不符 | 失败计数器从未递增：syncdocs.py:57 为 `failures += 0`，故 syncdocs.py:59 的 `return 1` 不可达。实测复制失败时抛未捕获 `PermissionError`（traceback 指向 syncdocs.py:51 `write_bytes`），解释器以 exit=1 终止，且其后文件不再同步（实测排序靠后的 `z_after.md` 未被复制） |
| 11 | "退出码 2：源目录或目标目录不存在" | 属实 | syncdocs.py:33-38；实测缺目标、缺源均打印错误并 exit=2。补充：argparse 参数错误也返回 2 |
| 12 | "目标目录必须预先存在，工具不会自动创建" | 部分不符 | 目标根目录必须存在：syncdocs.py:36-38 缺失时返回 2；但目标下缺失的子目录会自动创建：syncdocs.py:50 `destination.parent.mkdir(parents=True, exist_ok=True)`，实测首次同步即在目标端生成 `tgt/sub/nested.md` |
