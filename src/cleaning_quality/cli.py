"""Command line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .scoring import load_inspections, score_groups


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cleaning_quality", description="Score cleaning inspections.")
    p.add_argument("file", type=Path, help="inspections CSV")
    p.add_argument("--by", choices=["building", "area"], default="building", help="group results (default building)")
    p.add_argument("--since", help="only inspections on or after YYYY-MM-DD")
    p.add_argument("--pass-mark", type=float, default=85.0, help="percent needed to pass (default 85)")
    p.add_argument("--worst", type=int, help="show only the N lowest groups")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = score_groups(load_inspections(args.file), args.by, args.since)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.worst:
        results = results[:args.worst]
    print(f"{'Group':<34} {'Score':>6} {'Grade':>5} {'Items':>5}  Result  Low items")
    failing = 0
    for r in results:
        ok = r.percent >= args.pass_mark
        failing += not ok
        print(f"{r.name:<34} {r.percent:>5.1f}% {r.grade:>5} {r.items:>5}  {'PASS' if ok else 'FAIL':<6}  "
              f"{', '.join(r.failed_items) or '-'}")
    print(f"\n{failing} of {len(results)} below the {args.pass_mark:g}% pass mark.")
    return 1 if failing else 0
