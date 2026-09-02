from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks" / "history" / "2026-09-02-v029-shipping-vs-frontier.json"
SITE = ROOT / "site" / "src" / "assets" / "shipping-vs-frontier-v029.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_site_mirror_is_exact_durable_benchmark_record() -> None:
    assert HISTORY.read_bytes() == SITE.read_bytes()


def test_shipping_frontier_record_is_complete_and_self_consistent() -> None:
    record = _load(HISTORY)
    assert record["schema"] == "cmpct-v029-shipping-vs-frontier-v1"
    assert record["project_version"] == "0.29.0"
    assert record["shipping"]["format_revision"] == 24
    contract = record["benchmark_contract"]
    assert contract["same_lifetime_measurement"] is True
    assert contract["same_tree_per_row"] is True
    assert contract["timing_claim"] is None

    rows = record["rows"]
    assert len(rows) == 15
    assert len({(row["suite"], row["name"]) for row in rows}) == 15
    assert all(len(row["tree_sha256"]) == 64 for row in rows)
    assert all(row["shipping_bytes"] > 0 and row["frontier_bytes"] > 0 for row in rows)

    totals = record["totals"]
    shipping = sum(row["shipping_bytes"] for row in rows)
    frontier = sum(row["frontier_bytes"] for row in rows)
    assert totals["workloads"] == len(rows)
    assert totals["files"] == sum(row["files"] for row in rows)
    assert totals["logical_bytes"] == sum(row["logical_bytes"] for row in rows)
    assert totals["shipping_bytes"] == shipping
    assert totals["frontier_bytes"] == frontier
    assert totals["frontier_saving_bytes"] == shipping - frontier
    assert totals["frontier_wins"] == sum(row["frontier_bytes"] < row["shipping_bytes"] for row in rows)
    assert totals["shipping_wins"] == sum(row["shipping_bytes"] < row["frontier_bytes"] for row in rows)
    assert totals["ties"] == sum(row["shipping_bytes"] == row["frontier_bytes"] for row in rows)
