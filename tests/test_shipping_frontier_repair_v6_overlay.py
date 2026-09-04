from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "shipping_vs_frontier_v029_repair_v6.py"


def _load_overlay():
    # The benchmark is a script whose sibling import intentionally resolves from benchmarks/.
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        spec = importlib.util.spec_from_file_location("cmpct_shipping_frontier_repair_v6_test", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_repair_v6_overlay_preserves_history_and_hurdle() -> None:
    module = _load_overlay()
    rows, record = module._accepted_rows_repair_v6()
    overlay = record["accepted_identity_overlay"]

    assert len(rows) == 15
    assert overlay["accepted"] is True
    assert overlay["historical_record_rewritten"] is False
    assert overlay["hurdle_lowered"] is False
    assert overlay["absolute_v030_saving_hurdle_bytes"] == 687_783
    assert overlay["historical_candidate_bytes"] == 137_501_815
    assert overlay["candidate_bytes"] == 137_499_525
    assert overlay["delta_vs_historical_bytes"] == -2_290
    assert record["portable_frontier"]["candidate_bytes"] == 137_499_525

    dev = rows[("neutral_hostile_v1", "01_developer_repository")]
    assert dev["tree_sha256"] == "d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49"
    assert dev["candidate_bytes"] == 744_337
    assert dev["benchmark_identity"] == "neutral-hostile-repair-v6"


def test_repair_v6_overlay_changes_only_the_accepted_five_rows() -> None:
    module = _load_overlay()
    historical, _ = module._ORIGINAL_ACCEPTED_ROWS()
    repaired, record = module._accepted_rows_repair_v6()
    overlaid = {
        (row["suite"], row["name"])
        for row in record["accepted_identity_overlay"]["rows"]
    }

    assert len(overlaid) == 5
    changed = {
        key
        for key in repaired
        if repaired[key]["tree_sha256"] != historical[key]["tree_sha256"]
        or int(repaired[key]["candidate_bytes"]) != int(historical[key]["candidate_bytes"])
    }
    assert changed <= overlaid
    assert ("neutral_hostile_v1", "01_developer_repository") in changed

    untouched = set(repaired) - overlaid
    assert untouched
    for key in untouched:
        assert repaired[key]["tree_sha256"] == historical[key]["tree_sha256"]
        assert int(repaired[key]["candidate_bytes"]) == int(historical[key]["candidate_bytes"])
