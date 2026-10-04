from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "experiments" / "entropygraph_v030_pack_plan_cache.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_v030_pack_cache_test", PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture(mod):
    # Similar but non-identical nodes produce group boundaries that repeat across the six inherited
    # limits.  The fixture is structural, not a corpus identity used by product admission.
    nodes = [
        (b"alpha-beta-gamma-" * 4096) + bytes([i]) * (300 + i * 17)
        for i in range(8)
    ]
    sketches = [mod.V028.similarity_sketch(raw) for raw in nodes]
    return nodes, sketches, list(range(len(nodes)))


def test_cached_selector_is_field_exact_to_inherited_selector() -> None:
    mod = _module()
    nodes, sketches, roots = _fixture(mod)
    stats = mod.assert_exact_equivalence(nodes, sketches, roots)
    assert stats.misses > 0
    assert stats.hits > 0


def test_cache_reuses_exact_lengths_without_retaining_payloads() -> None:
    mod = _module()
    nodes, sketches, roots = _fixture(mod)
    calls = 0

    def counted(raw: bytes):
        nonlocal calls
        calls += 1
        return mod.V028._compress_record(raw)

    cached, _, stats = mod.choose_pack_plan_cached(nodes, sketches, roots, compress_record=counted)
    inherited, _ = mod.V028._choose_pack_plan(nodes, sketches, roots)
    assert cached == inherited
    assert calls == stats.misses
    assert stats.hits > 0


def test_cache_scope_is_per_tournament() -> None:
    mod = _module()
    nodes, sketches, roots = _fixture(mod)
    first = mod.choose_pack_plan_cached(nodes, sketches, roots)[2]
    second = mod.choose_pack_plan_cached(nodes, sketches, roots)[2]
    assert first == second
    assert first.misses > 0
