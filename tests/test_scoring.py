from pathlib import Path

import pytest

from cleaning_quality.cli import main
from cleaning_quality.scoring import Item, grade, load_inspections, score_groups

ROOT = Path(__file__).resolve().parents[1]
DATA = str(ROOT / "data" / "inspections.csv")


def I(b, a, s, d="2026-03-02", item="x"):
    return Item(d, b, a, item, s)


def test_grade_boundaries():
    assert [grade(p) for p in (100, 90, 89.9, 80, 70, 69.9, 0)] == ["A", "A", "B", "B", "C", "F", "F"]


def test_percent_is_sum_over_max():
    r = score_groups([I("A", "r", 5), I("A", "r", 3)])[0]
    assert r.percent == 80.0 and r.grade == "B"


def test_perfect_and_zero():
    assert score_groups([I("A", "r", 5)])[0].percent == 100.0
    assert score_groups([I("A", "r", 0)])[0].percent == 0.0


def test_lowest_first():
    got = score_groups([I("Good", "r", 5), I("Bad", "r", 1)])
    assert [r.name for r in got] == ["Bad", "Good"]


def test_group_by_area():
    got = score_groups([I("A", "r1", 5), I("A", "r2", 1)], by="area")
    assert [r.name for r in got] == ["A / r2", "A / r1"]


def test_since_filters_old_rows():
    items = [I("A", "r", 1, d="2026-01-01"), I("A", "r", 5, d="2026-03-01")]
    assert score_groups(items, since="2026-02-01")[0].percent == 100.0


def test_failed_items_listed():
    r = score_groups([I("A", "r", 2, item="Fixtures"), I("A", "r", 5, item="Floors")])[0]
    assert r.failed_items == ("Fixtures",)


def test_empty_returns_empty():
    assert score_groups([]) == []


def test_bad_by_rejected():
    with pytest.raises(ValueError):
        score_groups([], by="floor")


def test_score_out_of_range_rejected(tmp_path):
    f = tmp_path / "i.csv"
    f.write_text("date,building,area,item,score\n2026-03-02,A,r,x,9\n")
    with pytest.raises(ValueError):
        load_inspections(f)


def test_non_number_rejected(tmp_path):
    f = tmp_path / "i.csv"
    f.write_text("date,building,area,item,score\n2026-03-02,A,r,x,good\n")
    with pytest.raises(ValueError):
        load_inspections(f)


def test_cli_report(capsys):
    assert main([DATA]) == 1
    out = capsys.readouterr().out
    assert "Building B" in out and "FAIL" in out


def test_cli_worst_and_missing(capsys):
    assert main([DATA, "--by", "area", "--worst", "1"]) == 1
    assert "1 of 1 below" in capsys.readouterr().out
    assert main(["missing.csv"]) == 2
