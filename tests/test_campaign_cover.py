import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import campaign_cover as cc  # noqa: E402


def test_one_site_covers_both_rows_wins():
    sites = [{"id": "a", "rows": {"terrain"}, "window": 0, "d": 0.1},
             {"id": "b", "rows": {"terrain", "low_sun"}, "window": 30, "d": 0.9}]
    chosen, left = cc.greedy_cover(sites, cc.FIELD_ROWS)
    assert [s["id"] for s in chosen] == ["b"] and not left


def test_two_sites_when_needed_and_tie_breaks():
    sites = [{"id": "t1", "rows": {"terrain"}, "window": 0, "d": 0.5},
             {"id": "t2", "rows": {"terrain"}, "window": 0, "d": 0.2},
             {"id": "s", "rows": {"low_sun"}, "window": 40, "d": 2.0}]
    chosen, left = cc.greedy_cover(sites, cc.FIELD_ROWS)
    assert {s["id"] for s in chosen} == {"t2", "s"} and not left


def test_uncoverable_row_reported():
    chosen, left = cc.greedy_cover([{"id": "t", "rows": {"terrain"}}], cc.FIELD_ROWS)
    assert [s["id"] for s in chosen] == ["t"] and left == {"low_sun"}
    assert cc.greedy_cover([], cc.FIELD_ROWS) == ([], {"terrain", "low_sun"})
