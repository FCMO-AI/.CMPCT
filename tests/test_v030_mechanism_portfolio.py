from __future__ import annotations

from pathlib import Path

from benchmarks import v030_mechanism_portfolio as portfolio


def _row(name: str, klass: str, saving: int, selected: str, *, prefix: bool = False) -> dict:
    base = 10_000_000
    return {
        "name": name,
        "class": klass,
        "v029_bytes": base,
        "candidate_bytes": base - saving,
        "saving_vs_v029_bytes": saving,
        "gir_saving_vs_v029_bytes": saving if klass == "structured" else 0,
        "prefixgraph_saving_vs_v029_bytes": saving if prefix else None,
        "prefixgraph_eligible": prefix,
        "prefix_records": 1 if prefix else None,
        "prefix_max_dependency_depth": 1 if prefix else None,
        "selected": selected,
    }


def _passing_rows() -> list[dict]:
    rows = [
        _row("01_shifted_versions", "structural", 12 * 1024, "prefixgraph", prefix=True),
        _row("03_boundary_churn", "structural", 12 * 1024, "prefixgraph", prefix=True),
        _row("05_logs_and_telemetry", "structured", 256 * 1024, "gir"),
        _row("04_analytics_and_database", "structured", 256 * 1024, "gir"),
        _row("09_ml_artifacts", "structured", 1536 * 1024, "gir"),
    ]
    assert sum(row["saving_vs_v029_bytes"] for row in rows) == portfolio.MIN_PORTFOLIO_AGGREGATE
    return rows


def test_complete_artifact_selector_returns_v029_on_exact_tie() -> None:
    assert portfolio._select_complete_artifact({"v029": 100, "gir": 100, "prefixgraph": 100}) == "v029"
    assert portfolio._select_complete_artifact({"v029": 100, "gir": 99, "prefixgraph": 99}) == "gir"


def test_prefix_eligibility_rejects_file_above_oracle_ceiling(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    with (root / "too-large.bin").open("wb") as stream:
        stream.truncate(portfolio.PG.MAX_FILE_BYTES + 1)
    eligible, reason = portfolio._prefix_eligibility(root)
    assert eligible is False
    assert reason is not None and "file_size" in reason


def test_portfolio_gate_exactly_inherits_both_frozen_mechanism_floors() -> None:
    result = portfolio._gate(_passing_rows())
    assert portfolio.MIN_PORTFOLIO_AGGREGATE == 2_121_728
    assert result["prefixgraph_frozen_gate"] is True
    assert result["gir_frozen_gate"] is True
    assert result["coexistence_gate"] is True
    assert result["workloads_improved"] == 5
    assert result["workloads_regressed"] == 0
    assert result["portfolio_gate"] is True


def test_portfolio_gate_cannot_hide_one_byte_gir_floor_miss_behind_other_rows() -> None:
    rows = _passing_rows()
    target = next(row for row in rows if row["name"] == "05_logs_and_telemetry")
    target["gir_saving_vs_v029_bytes"] = portfolio.MIN_GIR_EACH - 1
    # Keep the selected portfolio total unchanged on purpose.  The mechanism-specific floor must still fail;
    # aggregate over-performance elsewhere is not allowed to launder a weak structured row into acceptance.
    result = portfolio._gate(rows)
    assert result["gir_frozen_gate"] is False
    assert result["portfolio_gate"] is False


def test_portfolio_gate_requires_both_mechanisms_to_win_real_rows() -> None:
    rows = _passing_rows()
    next(row for row in rows if row["name"] == "05_logs_and_telemetry")["selected"] = "prefixgraph"
    next(row for row in rows if row["name"] == "04_analytics_and_database")["selected"] = "prefixgraph"
    next(row for row in rows if row["name"] == "09_ml_artifacts")["selected"] = "prefixgraph"
    result = portfolio._gate(rows)
    assert result["coexistence_gate"] is False
    assert result["portfolio_gate"] is False
