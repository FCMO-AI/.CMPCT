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


def test_agglomerator_spends_read_budget_only_for_exact_byte_wins(monkeypatch) -> None:
    mod = _module()
    nodes = [b"A" * 65536, b"B" * 65536, b"C" * 65536]

    # Footnote: synthetic physical costs isolate the grouping algorithm from a particular zstd release.
    # Singles cost 100 each, pairs 150 and the triple 220, so both accepted merges buy exact bytes.
    monkeypatch.setattr(
        mod, "_record_cost",
        lambda raw: 100 if len(raw) <= 65536 else 150 if len(raw) <= 131072 else 220,
    )
    candidate, diag = mod._agglomerate(nodes, [0, 1, 2], "bytes")
    assert candidate is not None
    cost, amp, max_group, selected_groups = candidate
    assert cost == 220
    assert amp == 3.0
    assert max_group == 3 * 65536
    assert selected_groups == [[0, 1, 2]]
    assert diag["merges"] == 2
    assert diag["worst_member_amp"] == 3.0


def test_agglomerator_rejects_attractive_merge_above_per_member_8x(monkeypatch) -> None:
    mod = _module()
    nodes = [b"x" * 1024, b"y" * (9 * 1024)]
    probe_lengths = []

    # Footnote: the merged 10 KiB record is only 2x in the historical weighted metric but 10x for the
    # 1 KiB member. Make that unsafe record nearly free and verify locality rejects it *before* the
    # compressor is called, so the exact-cost budget is reserved for physically admissible candidates.
    def fake_cost(raw: bytes) -> int:
        probe_lengths.append(len(raw))
        return 1 if len(raw) > 9 * 1024 else 100

    monkeypatch.setattr(mod, "_record_cost", fake_cost)
    candidate, diag = mod._agglomerate(nodes, [0, 1], "bytes")
    assert candidate is not None
    cost, amp, _, selected_groups = candidate
    assert cost == 200
    assert amp == 1.0
    assert selected_groups == [[0], [1]]
    assert diag["worst_member_amp"] == 1.0
    assert diag["exact_cost_probes"] == 2
    assert sorted(probe_lengths) == [1024, 9 * 1024]


def test_efficiency_strategy_is_deterministic_and_bounded(monkeypatch) -> None:
    mod = _module()
    nodes = [b"a" * 4096, b"b" * 4096, b"c" * 4096, b"d" * 4096]
    monkeypatch.setattr(mod, "_record_cost", lambda raw: max(1, 500 - len(raw) // 64))
    first, first_diag = mod._agglomerate(nodes, [0, 1, 2, 3], "efficiency")
    second, second_diag = mod._agglomerate(nodes, [0, 1, 2, 3], "efficiency")
    assert first == second
    assert first_diag["bytes"] == second_diag["bytes"]
    assert first is not None
    assert first[1] <= mod.MAX_READ_AMP
    assert mod._worst_member_amp(first[3], nodes) <= mod.MAX_READ_AMP


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
