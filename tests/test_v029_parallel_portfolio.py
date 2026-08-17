from pathlib import Path

from experiments.entropygraph_v029_parallel_portfolio import ACCEPTED_ENGINE, build_parallel
from experiments import entropygraph_v029_residual_strict as accepted


def test_parallel_scheduler_preserves_exact_selected_archive(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.bin").write_bytes((b"alpha-beta-gamma\n" * 7000) + b"tail-a")
    (root / "b.bin").write_bytes((b"alpha-beta-delta\n" * 7000) + b"tail-b")

    sequential = tmp_path / "sequential.cmpct"
    parallel = tmp_path / "parallel.cmpct"
    seq = accepted.build(root, sequential)
    par = build_parallel(root, parallel)

    # Footnote: compare against the stable attempt-5 wrapper rather than a generic archive identity.
    # The first scheduler experiment accidentally benchmarked attempt #1 and still produced perfectly
    # self-consistent bytes, so byte equality alone is not sufficient protection against stale engines.
    assert par["accepted_engine"] == ACCEPTED_ENGINE == "attempt5-residual-program-packing"
    assert par["scheduler_mode"] == "parallel-independent-portfolio"
    assert par["selection_materialization"] == "same-filesystem-atomic-move"
    assert par["selection_extra_payload_write_bytes"] == 0
    assert par["selected"] == seq["selected"]
    assert par["archive_bytes"] == seq["archive_bytes"]
    assert par["v028_bytes"] == seq["v028_bytes"]
    assert par["attempt5_graph_bytes"] == seq["mosaic_graph_bytes"]
    assert parallel.read_bytes() == sequential.read_bytes()


def test_parallel_scheduler_preserves_single_file_fast_reject_policy(tmp_path: Path) -> None:
    root = tmp_path / "single"
    root.mkdir()
    # Deterministic pseudo-random-looking bytes make the inherited graph unattractive without relying on
    # os.urandom. If v0.28 does not select its v0.25 fallback on a future engine, the identity invariant
    # below still matters; the scheduler must never speculate around accepted single-file policy.
    raw = bytes(((i * 73 + (i >> 3) * 19) & 0xFF) for i in range(256 * 1024))
    (root / "one.bin").write_bytes(raw)

    sequential = tmp_path / "single-sequential.cmpct"
    scheduled = tmp_path / "single-scheduled.cmpct"
    seq = accepted.build(root, sequential)
    par = build_parallel(root, scheduled)

    assert par["accepted_engine"] == ACCEPTED_ENGINE
    assert par["scheduler_mode"] == "single-file-accepted-policy"
    assert par["selected"] == seq["selected"]
    assert scheduled.read_bytes() == sequential.read_bytes()
