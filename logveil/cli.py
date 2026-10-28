"""Command-line interface for LogVeil.

Examples
--------
Redact a log before pasting it into an issue or an AI chat::

    logveil redact app.log -o app.redacted.log --map mapping.json

Check (without changing anything) whether a file is safe to share::

    logveil scan app.log

Undo a redaction when a reply comes back full of placeholders::

    logveil restore reply.md --map mapping.json -o reply.restored.md
"""
from __future__ import annotations

import argparse
import json
import sys

from .detectors import CATEGORIES
from .redactor import Redactor, restore_text


def _read(path: str | None) -> str:
    if path in (None, "-"):
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _write(path: str | None, text: str) -> None:
    if path in (None, "-"):
        sys.stdout.write(text)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


def _load_extra(config_path: str | None) -> list[tuple[str, str]]:
    if not config_path:
        return []
    with open(config_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    return [(str(k), str(v)) for k, v in cfg.get("extra_patterns", {}).items()]


def _make_redactor(args) -> Redactor:
    categories = args.categories.split(",") if getattr(args, "categories", None) else None
    return Redactor(categories=categories, extra_patterns=_load_extra(args.config))


def cmd_redact(args) -> int:
    redactor = _make_redactor(args)
    text = _read(args.input)
    _write(args.output, redactor.redact_text(text))
    if args.map:
        redactor.save_mapping(args.map)
    report = {"counts": redactor.counts, "distinct_values": len(redactor.mapping)}
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    else:
        print(f"logveil: {report}", file=sys.stderr)
    return 0


def cmd_scan(args) -> int:
    redactor = _make_redactor(args)
    redactor.redact_text(_read(args.input))
    report = {"counts": redactor.counts, "distinct_values": len(redactor.mapping)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if redactor.mapping else 0


def cmd_restore(args) -> int:
    with open(args.map, encoding="utf-8") as fh:
        mapping = json.load(fh)
    _write(args.output, restore_text(_read(args.input), mapping))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logveil",
        description="Redact logs and traces for safe sharing, with consistent, reversible placeholders.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("input", nargs="?", default="-", help="input file (default: stdin)")
        p.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
        p.add_argument("--categories", help=f"comma-separated subset of: {','.join(CATEGORIES)}")
        p.add_argument("--config", help="JSON config with extra_patterns")

    p_redact = sub.add_parser("redact", help="redact a file")
    common(p_redact)
    p_redact.add_argument("--map", help="write the original->placeholder mapping to this JSON file (keep it private!)")
    p_redact.add_argument("--report", help="write a counts-only report to this JSON file")
    p_redact.set_defaults(func=cmd_redact)

    p_scan = sub.add_parser("scan", help="report findings only; exit 1 when anything is found")
    common(p_scan)
    p_scan.set_defaults(func=cmd_scan)

    p_restore = sub.add_parser("restore", help="undo a redaction using its mapping file")
    common(p_restore)
    p_restore.add_argument("--map", required=True, help="mapping JSON produced by redact")
    p_restore.set_defaults(func=cmd_restore)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
