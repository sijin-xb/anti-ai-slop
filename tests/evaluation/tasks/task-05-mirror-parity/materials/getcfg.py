import argparse
import json
import sys
from pathlib import Path

DEFAULT_FORMAT = "json"
DEFAULT_TIMEOUT = 15
EXIT_NOT_FOUND = 1
EXIT_INVALID = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="getcfg")
    parser.add_argument("key", help="dot-separated config key, e.g. server.port")
    parser.add_argument("--file", default="config.json", help="config file path")
    parser.add_argument("--format", choices=("json", "raw"), default=DEFAULT_FORMAT)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--default", help="value when key is missing")
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"config not found: {path}", file=sys.stderr)
        return EXIT_INVALID

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"invalid json: {exc}", file=sys.stderr)
        return EXIT_INVALID

    node = data
    for part in args.key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            if args.default is not None:
                print(args.default)
                return 0
            print(f"key not found: {args.key}", file=sys.stderr)
            return EXIT_NOT_FOUND

    if args.format == "raw":
        print(node if not isinstance(node, (dict, list)) else json.dumps(node, ensure_ascii=False))
    else:
        print(json.dumps(node, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
