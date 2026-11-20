"""Turn inspection line items into percentage scores and grades."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MAX_SCORE = 5


@dataclass(frozen=True)
class Item:
    date: str
    building: str
    area: str
    item: str
    score: int


@dataclass(frozen=True)
class Result:
    name: str
    percent: float
    grade: str
    items: int
    failed_items: tuple[str, ...]


def load_inspections(path: Path) -> list[Item]:
    """Read inspections.csv; each score is 0 to 5."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for n, row in enumerate(rows, start=2):
        try:
            s = int(row["score"])
            if not 0 <= s <= MAX_SCORE:
                raise ValueError(f"score {s} outside 0 to {MAX_SCORE}")
            out.append(Item(row["date"].strip(), row["building"].strip(), row["area"].strip(),
                            row["item"].strip(), s))
        except (KeyError, ValueError, AttributeError) as exc:
            raise ValueError(f"{path}: bad inspection row on line {n}: {exc!r}") from exc
    return out


def grade(percent: float) -> str:
    """A at 90 and up, B at 80, C at 70, otherwise F."""
    if percent >= 90:
        return "A"
    if percent >= 80:
        return "B"
    if percent >= 70:
        return "C"
    return "F"


def _result(name: str, items: list[Item]) -> Result:
    pct = 100.0 * sum(i.score for i in items) / (MAX_SCORE * len(items))
    low = tuple(sorted({i.item for i in items if i.score <= 2}))
    return Result(name, round(pct, 1), grade(pct), len(items), low)


def score_groups(items: list[Item], by: str = "building", since: str | None = None) -> list[Result]:
    """Score items grouped by building or by 'building / area', lowest first.

    since keeps only inspections dated on or after that YYYY-MM-DD date.
    failed_items lists line items that scored 2 or less.
    """
    if by not in {"building", "area"}:
        raise ValueError("by must be 'building' or 'area'")
    groups: dict[str, list[Item]] = {}
    for i in items:
        if since and i.date < since:
            continue
        key = i.building if by == "building" else f"{i.building} / {i.area}"
        groups.setdefault(key, []).append(i)
    results = [_result(k, v) for k, v in groups.items()]
    return sorted(results, key=lambda r: (r.percent, r.name))
