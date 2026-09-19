from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_prefixgraph as SERIAL
from experiments import entropygraph_v030_prefixgraph_parallel as PARALLEL
from experiments import entropygraph_v030_release_candidate as RC


def _fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    base = (b"alpha-beta-gamma-delta\n" * 8192)
    for index in range(8):
        data = bytearray(base)
        for offset in range(index * 17, len(data), 8191):
            data[offset] ^= (index + 1)
        (root / f"version-{index:02d}.txt").write_bytes(bytes(data))


def test_parallel_prefixgraph_is_exact_byte_drop_in(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)
    serial = tmp_path / "serial.cmpct"
    parallel = tmp_path / "parallel.cmpct"

    serial_stats = SERIAL.build(source, serial)
    parallel_stats = PARALLEL.build(source, parallel)

    assert parallel.read_bytes() == serial.read_bytes()
    assert parallel_stats["anchor"] == serial_stats["anchor"]
    assert parallel_stats["archive_bytes"] == serial_stats["archive_bytes"]
    assert parallel_stats["tree_sha256"] == serial_stats["tree_sha256"]
    assert parallel_stats["candidate_set_unchanged"] is True
    assert parallel_stats["complete_byte_tournament_unchanged"] is True
    assert parallel_stats["direct_payload_floor_unchanged"] is True
    assert parallel_stats["full_candidate_list_retained"] is False
    assert parallel_stats["candidate_retention_policy"] == "winner-plus-bounded-inflight-v1"
    assert PARALLEL.MAX_ANCHOR_WORKERS == 4
    assert PARALLEL.WORKER_POLICY == "global-four-worker-throughput-bounded-retention-v2"
    assert 1 <= parallel_stats["anchor_audition_workers"] <= 4
    assert parallel_stats["anchor_audition_worker_policy"] == PARALLEL.WORKER_POLICY
    assert parallel_stats["max_anchor_results_inflight"] <= parallel_stats["anchor_audition_workers"]
    assert SERIAL.strong_verify(serial)["tree_sha256"] == PARALLEL.strong_verify(parallel)["tree_sha256"]


def test_streaming_tournament_key_preserves_historical_tie_law() -> None:
    direct = (b"1234", {"anchor": None})
    anchor0 = (b"1234", {"anchor": 0})
    anchor7 = (b"1234", {"anchor": 7})
    smaller7 = (b"123", {"anchor": 7})

    assert PARALLEL._candidate_key(direct) < PARALLEL._candidate_key(anchor0)
    assert PARALLEL._candidate_key(anchor0) < PARALLEL._candidate_key(anchor7)
    assert PARALLEL._candidate_key(smaller7) < PARALLEL._candidate_key(direct)


def test_release_candidate_uses_parallel_prefixgraph_semantic_owner() -> None:
    assert RC.PG is PARALLEL
    # The wrapper deliberately forwards canonical-operation bindings dynamically
    # instead of copying reader-visible identity at import time.
    assert RC.PG.MAGIC == SERIAL.MAGIC
    assert RC.PG._read is SERIAL._read
