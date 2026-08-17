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


def test_coarsener_can_spend_read_budget_selectively_without_losing_roots(monkeypatch) -> None:
    mod = _module()
    nodes = [b"A" * 65536, b"B" * 65536, b"C" * 65536]
    groups = [[0], [1], [2]]

    # Footnote: use a synthetic physical-cost oracle here so the test proves the partition algorithm,
    # not a particular zstd release's preference. Real benchmark admission still uses exact compressed
    # bytes from the repository's pinned compressor path.
    monkeypatch.setattr(mod, "_record_cost", lambda raw: 100 if len(raw) <= 65536 else 150 if len(raw) <= 131072 else 220)
    candidate, diag = mod._coarsen_source_plan(nodes, [0, 1, 2], groups, 65536, original_worst=1.0)
    assert candidate is not None
    cost, amp, max_group, selected_groups = candidate
    assert cost == 220
    assert amp == 3.0
    assert max_group == 3 * 65536
    assert selected_groups == [[0, 1, 2]]
    assert sorted(node_id for group in selected_groups for node_id in group) == [0, 1, 2]
    assert diag["worst_member_amp"] == 3.0


def test_coarsener_rejects_byte_win_that_exceeds_per_member_8x(monkeypatch) -> None:
    mod = _module()
    nodes = [b"x" * 1024, b"y" * (9 * 1024)]
    groups = [[0], [1]]

    # Footnote: a merged 10 KiB record would be only 2x in the historical weighted metric but 10x for
    # the 1 KiB member. Make that unsafe merge look overwhelmingly attractive in bytes and verify the
    # planner still keeps the two independent groups.
    monkeypatch.setattr(mod, "_record_cost", lambda raw: 1 if len(raw) > 9 * 1024 else 100)
    candidate, diag = mod._coarsen_source_plan(nodes, [0, 1], groups, 1024, original_worst=1.0)
    assert candidate is not None
    cost, amp, _, selected_groups = candidate
    assert cost == 200
    assert amp == 1.0
    assert selected_groups == [[0], [1]]
    assert diag["worst_member_amp"] == 1.0


def test_budgeted_selector_never_worsens_bytes_and_new_plan_obeys_both_read_budgets() -> None:
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
    assert chosen[2] <= mod.MAX_PACK_BYTES
    assert sorted(node_id for group in chosen[3] for node_id in group) == root_ids
    summary = next(row for row in trials if row.get("strategy") == "pack-budget-summary")
    if summary.get("selected"):
        assert chosen[1] <= mod.MAX_READ_AMP
        assert mod._worst_member_amp(chosen[3], nodes) <= mod.MAX_READ_AMP + 1e-12
    else:
        assert chosen == original
