from __future__ import annotations

"""Focused invariants for the v0.29 Locality Budget Compiler research planner."""

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "entropygraph_v029_pack_budget.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_v029_pack_budget_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pareto_pruning_removes_jointly_worse_states() -> None:
    mod = _module()
    root = mod._State(0, 0, 0.0, None, ())
    states = [
        mod._State(10, 100, 1.0, root, (0,)),
        mod._State(12, 110, 1.0, root, (1,)),  # More read and more bytes: dominated.
        mod._State(15, 90, 1.0, root, (2,)),
    ]
    kept = mod._prune_pareto(states)
    assert kept is not None
    assert [(row.decoded, row.cost) for row in kept] == [(10, 100), (15, 90)]


def test_coarsener_can_spend_weighted_budget_inside_existing_worst_case(monkeypatch) -> None:
    mod = _module()
    nodes = [b"A" * 65536, b"B" * 65536, b"C" * 65536]
    groups = [[0], [1], [2]]

    # Footnote: this synthetic call gives the planner a pre-existing 3x worst-member envelope. That lets
    # the test prove selective weighted-budget spending without teaching the implementation that a new
    # locality outlier is acceptable merely because it remains below the global 8x safety ceiling.
    monkeypatch.setattr(mod, "_record_cost", lambda raw: 100 if len(raw) <= 65536 else 150 if len(raw) <= 131072 else 220)
    candidate, diag = mod._coarsen_source_plan(nodes, [0, 1, 2], groups, 65536, original_worst=3.0)
    assert candidate is not None
    cost, amp, max_group, selected_groups = candidate
    assert cost == 220
    assert amp == 3.0
    assert max_group == 3 * 65536
    assert selected_groups == [[0, 1, 2]]
    assert sorted(node_id for group in selected_groups for node_id in group) == [0, 1, 2]
    assert diag["worst_member_amp"] == 3.0


def test_budgeted_selector_never_worsens_global_plan_or_weighted_budget() -> None:
    mod = _module()
    nodes = [
        (b"alpha-line\n" * 7000) + bytes([index]) * 4096
        for index in range(8)
    ]
    sketches = [mod.V028.similarity_sketch(raw) for raw in nodes]
    root_ids = list(range(len(nodes)))
    original, _ = mod._ORIGINAL_CHOOSE(nodes, sketches, root_ids)
    chosen, trials = mod._choose_pack_plan_budgeted(nodes, sketches, root_ids)

    assert chosen[0] <= original[0]
    assert chosen[1] <= mod.MAX_READ_AMP
    assert chosen[2] <= mod.MAX_PACK_BYTES
    assert sorted(node_id for group in chosen[3] for node_id in group) == root_ids
    # Footnote: the numeric 8x policy is not permission to make a workload's already-better locality
    # worse. The optimizer must remain at or below the exact accepted worst-member envelope.
    assert mod._worst_member_amp(chosen[3], nodes) <= mod._worst_member_amp(original[3], nodes) + 1e-12
    assert any(row.get("strategy") == "pack-budget-summary" for row in trials)
