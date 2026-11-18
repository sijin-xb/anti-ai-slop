import argparse
import json
import sys
from pathlib import Path

DEFAULT_DB = "inventory.db"
EXIT_USAGE = 2


def load_items(path: str) -> list[dict]:
    source = Path(path)
    if not source.is_file():
        return []
    return json.loads(source.read_text(encoding="utf-8"))


def save_items(path: str, items: list[dict]) -> None:
    Path(path).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inventory")
    parser.add_argument("--db", default=DEFAULT_DB, help="JSON 库文件路径")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="新增条目")
    add.add_argument("sku")
    add.add_argument("--qty", type=int, required=True)
    add.add_argument("--location", default="A1")

    take = sub.add_parser("take", help="扣减库存")
    take.add_argument("sku")
    take.add_argument("--qty", type=int, required=True)

    sub.add_parser("list", help="列出全部条目")

    args = parser.parse_args(argv)
    items = load_items(args.db)

    if args.command == "add":
        for item in items:
            if item["sku"] == args.sku:
                item["qty"] += args.qty
                item["location"] = args.location
                break
        else:
            items.append({"sku": args.sku, "qty": args.qty, "location": args.location})
        save_items(args.db, items)
        return 0

    if args.command == "take":
        for item in items:
            if item["sku"] == args.sku:
                if item["qty"] < args.qty:
                    print(f"insufficient stock: {args.sku}", file=sys.stderr)
                    return 1
                item["qty"] -= args.qty
                save_items(args.db, items)
                return 0
        print(f"unknown sku: {args.sku}", file=sys.stderr)
        return 1

    if args.command == "list":
        for item in sorted(items, key=lambda entry: entry["sku"]):
            print(f"{item['sku']}\t{item['qty']}\t{item['location']}")
        return 0

    parser.error("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
