import argparse
import sys
from pathlib import Path

DEFAULT_INTERVAL = 30
DEFAULT_RETRIES = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syncdocs")
    parser.add_argument("source", help="源目录")
    parser.add_argument("target", help="目标目录")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="轮询间隔秒数")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="单文件失败重试次数")
    parser.add_argument("--dry-run", action="store_true", help="只列出将同步的文件")
    parser.add_argument("--delete", action="store_true", help="删除目标端多余文件")
    return parser


def files_to_sync(source: Path, target: Path) -> list[Path]:
    result = []
    for path in sorted(source.rglob("*.md")):
        relative = path.relative_to(source)
        counterpart = target / relative
        if not counterpart.is_file() or counterpart.stat().st_mtime < path.stat().st_mtime:
            result.append(path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source, target = Path(args.source), Path(args.target)
    if not source.is_dir():
        print(f"source not a directory: {source}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"target not a directory: {target}", file=sys.stderr)
        return 2

    pending = files_to_sync(source, target)
    if args.dry_run:
        for path in pending:
            print(path)
        return 0

    failures = 0
    for path in pending:
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
    if args.delete:
        for path in sorted(target.rglob("*.md")):
            relative = path.relative_to(target)
            if not (source / relative).is_file():
                path.unlink()
                failures += 0
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
