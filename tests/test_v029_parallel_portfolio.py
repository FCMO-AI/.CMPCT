import os
from pathlib import Path

from experiments import entropygraph_v029_parallel_portfolio as portfolio
from experiments import entropygraph_v029_residual_strict as accepted


ACCEPTED_ENGINE = portfolio.ACCEPTED_ENGINE
build_parallel = portfolio.build_parallel


def _make_two_file_corpus(root: Path) -> None:
    root.mkdir()
    (root / "a.bin").write_bytes((b"alpha-beta-gamma\n" * 7000) + b"tail-a")
    (root / "b.bin").write_bytes((b"alpha-beta-delta\n" * 7000) + b"tail-b")


def test_parallel_scheduler_preserves_exact_selected_archive(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _make_two_file_corpus(root)

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
    assert par["selection_durability"].startswith("atomic-file-fsynced")
    assert par["selected"] == seq["selected"]
    assert par["archive_bytes"] == seq["archive_bytes"]
    assert par["v028_bytes"] == seq["v028_bytes"]
    assert par["attempt5_graph_bytes"] == seq["mosaic_graph_bytes"]
    assert parallel.read_bytes() == sequential.read_bytes()


def test_parallel_scheduler_atomically_replaces_existing_output(tmp_path: Path) -> None:
    root = tmp_path / "replace-corpus"
    _make_two_file_corpus(root)

    expected_path = tmp_path / "expected.cmpct"
    expected = accepted.build(root, expected_path)

    output = tmp_path / "existing.cmpct"
    sentinel = b"old-output-must-not-survive"
    output.write_bytes(sentinel)
    result = build_parallel(root, output)

    # ``os.replace`` is valuable only if the normal overwrite case preserves the exact accepted winner.
    # Pin this explicitly so a future portability workaround cannot silently fall back to append/copy logic
    # or leave the pre-existing output in place while still reporting zero publication payload bytes.
    assert output.read_bytes() != sentinel
    assert output.read_bytes() == expected_path.read_bytes()
    assert result["archive_bytes"] == expected["archive_bytes"]
    assert result["selection_materialization"] == "same-filesystem-atomic-move"
    assert result["selection_extra_payload_write_bytes"] == 0
    assert result["selection_durability"].startswith("atomic-file-fsynced")


def test_durable_replace_flushes_winner_before_publication(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "candidate.cmpct"
    destination = tmp_path / "published.cmpct"
    payload = (b"durability-check\n" * 4096) + b"tail"
    source.write_bytes(payload)

    fsync_calls: list[int] = []
    real_fsync = portfolio.os.fsync

    def recording_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(portfolio.os, "fsync", recording_fsync)
    durability = portfolio._durable_replace(source, destination)

    assert not source.exists()
    assert destination.read_bytes() == payload
    assert fsync_calls, "winner data must be flushed before atomic publication"
    if os.name == "posix" and durability == "atomic-file-and-directory-fsynced":
        assert len(fsync_calls) >= 2, "POSIX durable publication must also flush the parent directory"


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
