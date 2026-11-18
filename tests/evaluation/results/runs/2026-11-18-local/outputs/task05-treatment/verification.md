# 核对记录 — task-05 多语言镜像同步

事实来源：`materials/getcfg.py`（只读）。行号均指该文件。
文档行号对 `materials/` 原文件与修正后交付件同时成立（改动均为行内替换，行数未变：EN 32 行、ZH 31 行）。
核对方式：先实测代码行为建立基线，再逐条裁决文档声明；静态核对与实测冲突时以实测为准。

## 一、实测基线

在临时目录以 `python3 -I getcfg.py` 执行，样例配置
`{"server": {"port": 8000, "hosts": ["a", "b"]}, "name": "app", "debug": true}`。

| 行为 | getcfg.py 依据 | 实测 |
|---|---|---|
| 配置文件缺失 → stderr 报错，退出码 2 | 9, 21-24 | `config not found: missing.json`，exit 2，目录内无新文件产生 |
| JSON 非法 → stderr 报错，退出码 2 | 28-30 | `invalid json: ...`，exit 2 |
| 键缺失且无 `--default` → stderr 报错，退出码 1 | 8, 40-41 | `key not found: missing.key`，exit 1 |
| 数组下标寻址（`server.hosts.0`）→ 退出码 1 | 33-35 | `key not found: server.hosts.0`，exit 1 |
| 键缺失且有 `--default` → 输出默认值，退出码 0 | 18, 37-39 | 输出 `fallback`，exit 0 |
| `--format` 默认 json，输出 JSON | 6, 16, 45-46 | `"app"` |
| raw 标量 → 裸值输出 | 43-44 | `app` |
| raw 对象/数组 → 仍输出 JSON | 43-44 | `{"port": 8000, "hosts": ["a", "b"]}` / `["a", "b"]` |
| `--timeout` 被接受、无行为差异 | 7, 17 | `--timeout 1` 与不传输出一致（`"app"`） |
| `--timeout` 无其他引用 | grep 全文 | 仅 7（`DEFAULT_TIMEOUT = 15`）与 17（argparse 注册）出现 |
| 无创建文件逻辑 | grep 全文 | 无 `write`/`open`/`mkdir`/`touch` |

## 二、改动明细（改前 → 改后，附 getcfg.py 行号）

```
[事实核对] README.md:17
声明：`--timeout` sets a ceiling of 15 seconds for file reads.
核对：getcfg.py:7,17——旗标注册、默认 15，但全文无其他引用；实测传参与不传输出一致
结果：不一致已改 → `--timeout` is accepted but unused; no timeout is applied.
```

```
[事实核对] README.zh-CN.md:17
声明：`--timeout` 限制读取超时，默认 30 秒。
核对：getcfg.py:7——DEFAULT_TIMEOUT = 15，非 30；且该旗标未被任何逻辑使用（同上实测）
结果：不一致已改 → `--timeout` 仅被解析、未被使用；不施加任何超时。（默认值错误与虚构行为一并修正）
```

```
[事实核对] README.md:15 与 README.zh-CN.md:15
声明：`--format raw` prints the value without JSON quoting. / 输出值本身，不加 JSON 引号
核对：getcfg.py:43-44——非 dict/list 才裸输出；raw 对对象/数组仍走 json.dumps（实测 `{"port": 8000, ...}`）
结果：不一致已改（两版同步补限定）→ 标量值不加引号直接输出；对象和数组仍输出 JSON
```

```
[事实核对] README.zh-CN.md:27
声明：退出码表第三行「3 | 配置文件缺失或 JSON 无效」
核对：getcfg.py:9——EXIT_INVALID = 2，在 24、30 两处返回；实测两种场景 exit 均为 2
结果：不一致已改 → 3 改为 2
```

```
[事实核对] README.zh-CN.md:31
声明：配置文件不存在时工具会自动创建一个空配置。
核对：getcfg.py:21-24——文件缺失走报错分支并返回 2；全文无写文件代码；实测后目录无新文件
结果：不一致已改 → 整句删除（虚构行为）
```

## 三、未改动声明的逐条确认

| 文档:行 | 声明 | getcfg.py 依据 | 结果 |
|---|---|---|---|
| EN:3 / ZH:3 | 按点分键读单值 | 14（key help）、27（json.loads）、33-35（按 `.` 下钻） | 一致 |
| EN:7 / ZH:7 | 放进 PATH，无第三方依赖 | 1-4（import argparse/json/sys/pathlib，全为标准库） | 一致 |
| EN:12 / ZH:12 | 示例命令 | 13-18（prog=getcfg、位置参数 key、`--file`） | 一致 |
| EN:19 / ZH:19 | `--default` 键缺失时输出、退出码 0 | 18, 37-39；实测 `fallback`，exit 0 | 一致 |
| EN:23-27 / ZH:23-27 | 退出码 0（含 default）、1（键缺失）、2（文件缺失或 JSON 无效） | 8, 9, 24, 30, 39, 41, 47；实测 T7-T10 | 一致 |
| EN:31-32 / ZH:31 | 数组不能用下标寻址，取父键自行解析 | 33-35（仅对 dict 下钻）；实测 `server.hosts.0` → exit 1 | 一致 |
| EN:15 / ZH:15 | `--format` 默认 `json` | 6, 16 | 一致 |

## 四、镜像一致性

- 小节结构：EN 与 ZH 均为 1 个 H1 + 4 个 H2（Install/安装、Usage/用法、Exit codes/退出码、Notes/注意）。
- 退出码表：两版均为 3 个数据行，数值 0/1/2 一一对应。
- 正文数字：`--timeout` 的「15 秒 / 30 秒」两处均已移除，正文不再含数字声明。
- 命令示例：两版同一 bash 命令，逐字一致。
- 术语：raw/json、退出码、`--default` 等概念两版一一对应。

## 五、验证

- Passed：实测基线 12 项（第一节，`python3 -I getcfg.py` 各分支，含退出码与输出内容）。
- Passed：`python3 scripts/anti_slop_lint.py <OUT>/README.md --pair <OUT>/README.zh-CN.md` → 0 条提示，exit 0。
- Passed：`python3 scripts/anti_slop_lint.py --profile zh-doc <OUT>/README.zh-CN.md` → 0 条提示，exit 0。
- Passed：`python3 scripts/anti_slop_lint.py <OUT>/README.md`（general）→ 0 条提示，exit 0。
- Not Run：干净环境复现示例命令（`--file /etc/app/config.json` 指向真实系统路径，仅静态核对 argparse 注册）。

linter 只作机械比对提示，事实核对以第二、三节的逐条裁决为准。
