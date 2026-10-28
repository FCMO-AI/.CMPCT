from __future__ import annotations

"""Focused invariants for the dormant one-hop reference-context oracle."""

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "entropygraph_v029_reference_context_oracle.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_reference_context_oracle_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_logical_base_records_are_forbidden_as_context_coded_targets() -> None:
    mod = _module()
    meta = {
        "nodes": [
            ["direct", 10, 0, 4096, b"a" * 32],
            ["direct", 11, 0, 4096, b"b" * 32],
            ["direct", 12, 0, 4096, b"c" * 32],
            ["delta", 0, 20, 4096, b"d" * 32],
            ["mosaic", [1, 2], 21, 4096, b"e" * 32],
        ]
    }
    assert mod._logical_base_node_ids(meta) == {0, 1, 2}
    assert mod._records_containing_logical_bases(meta) == {10, 11, 12}


def test_context_slice_is_tail_bounded_to_128_kib() -> None:
    mod = _module()
    raw = bytes(range(256)) * 1024
    ctx = mod._context_slice(raw)
    assert len(ctx) == mod.MAX_CONTEXT_SLICE
    assert ctx == raw[-mod.MAX_CONTEXT_SLICE:]


def test_direct_member_lengths_group_by_physical_record() -> None:
    mod = _module()
    meta = {
        "nodes": [
            ["direct", 7, 0, 1024, b"a" * 32],
            ["direct", 7, 1024, 2048, b"b" * 32],
            ["direct", 8, 0, 4096, b"c" * 32],
        ]
    }
    assert mod._direct_members_by_record(meta) == {7: [1024, 2048], 8: [4096]}


def test_existing_central_base_selector_prevents_context_chains() -> None:
    mod = _module()
    # Edge 1->0 and 2->1 are both profitable. The reusable selector must not allow record 1 to be both
    # an encoded target and a context anchor, which would create a context-on-context chain.
    assignment = mod.choose_central_bases(3, [(1, 0, 100), (2, 1, 200)])
    assert set(assignment).isdisjoint(set(assignment.values()))
