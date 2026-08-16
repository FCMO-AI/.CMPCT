from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]


def _engine():
    path = ROOT / "experiments" / "entropygraph_v028_strict.py"
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v028_strict_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tiny_population_falls_back_to_independent_records_when_packs_exceed_budget():
    engine = _engine()
    # Thousands of tiny roots make even a 64 KiB pack expensive for a one-file selective read. This is
    # the workload that falsified the first selector's "some pack will be <=8x" assumption.
    nodes = [(f"tiny={i:05d}|".encode() * 3) for i in range(3000)]
    sketches = [engine.BASE.similarity_sketch(node) for node in nodes]
    chosen, trials = engine.strict_choose_pack_plan(nodes, sketches, list(range(len(nodes))))
    cost, amp, limit, groups = chosen
    assert amp <= engine.READ_AMPLIFICATION_BUDGET
    assert limit == 0
    assert len(groups) == len(nodes)
    assert any(row["limit"] == 65536 and not row["feasible"] for row in trials)


def test_strict_graph_never_reports_pack_amplification_above_budget(tmp_path: Path):
    engine = _engine()
    source = tmp_path / "source"; source.mkdir()
    rng = random.Random(0x51A1C7)
    for i in range(400):
        payload = (f"record={i:04d}\n".encode() * 16) + bytes(rng.getrandbits(8) for _ in range(111))
        (source / f"item-{i:04d}.bin").write_bytes(payload)
    archive = tmp_path / "strict.cmpct"
    stats = engine._build_graph(source, archive)
    assert stats["strict_locality_policy"] is True
    assert stats["pack_read_amplification"] <= engine.READ_AMPLIFICATION_BUDGET
    assert engine.strong_verify(archive)["ok"] is True
