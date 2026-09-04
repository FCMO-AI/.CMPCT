from __future__ import annotations

import gzip
import os
from pathlib import Path

import pytest
import zstandard as zstd

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product_logs_candidate as CAND


def _source(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    a = (b"2026-08-22 INFO alpha value=42\n" * 4096)
    b = (b"2026-08-22 WARN beta value=17\n" * 4096)
    (root / "a.log").write_bytes(a)
    (root / "a.log.zst").write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress(a))
    (root / "b.log").write_bytes(b)
    (root / "b.log.gz").write_bytes(gzip.compress(b, compresslevel=6, mtime=0))
    (root / "unmatched.log").write_bytes(b"direct\n" * 1024)
    os.link(root / "a.log", root / "zz-a-hard.log")
    try:
        os.symlink("a.log", root / "a-link")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")


def test_candidate_public_facade_owns_logs_profile(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _source(source)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(source, archive)

    revision, profile = CAND._revision_for_archive(archive)
    assert revision == 25
    assert profile == CAND.LOGS_PROFILE

    verified = CAND.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == CAND.LOGS_PROFILE
    assert verified["filesystem_semantics_verified"] is True
    assert verified["tree_sha256"] == CAND.treehash(source)

    members = {row["path"]: row for row in CAND.list_members(archive)}
    assert members["a.log"]["kind"] == "file"
    assert members["zz-a-hard.log"]["kind"] == "hardlink"
    assert members["a-link"]["kind"] == "symlink"
    assert not any(path.startswith(CAND.FS.INTERNAL_ROOT) for path in members)

    owner, owner_stats = CAND.read_member_with_stats(archive, "a.log")
    alias, alias_stats = CAND.read_member_with_stats(archive, "zz-a-hard.log")
    assert alias == owner == (source / "a.log").read_bytes()
    assert owner_stats["decoded_context_amplification"] <= 8.0
    assert alias_stats["decoded_context_amplification"] <= 8.0
    assert CAND.read_member(archive, "a-link") == b"a.log"

    restored = tmp_path / "restored"
    CAND.extract(archive, restored)
    assert (restored / "a.log").read_bytes() == (source / "a.log").read_bytes()
    assert (restored / "a-link").is_symlink()
    assert os.readlink(restored / "a-link") == "a.log"
    assert os.stat(restored / "a.log").st_ino == os.stat(restored / "zz-a-hard.log").st_ino


def test_logs_admission_requires_every_measured_bound() -> None:
    r24 = {"archive_bytes": 5_000_000}
    logs = {
        "archive_bytes": 3_500_000,
        "edge_detection": {"inverse_edges": 2},
        "max_member_read_amplification": 3.0,
        "max_decode_unit_bytes": 7_000_000,
    }
    admitted, facts = CAND._admission(r24, logs)
    assert admitted is True
    assert facts["saving_vs_r24_bytes"] == 1_500_000

    for key, bad in (
        ("archive_bytes", 4_200_000),
        ("max_member_read_amplification", 8.01),
        ("max_decode_unit_bytes", 8 * 1024 * 1024 + 1),
    ):
        mutated = dict(logs)
        mutated[key] = bad
        if key == "archive_bytes":
            # 800 KiB saving: below the immutable 1 MiB structural evidence floor.
            pass
        assert CAND._admission(r24, mutated)[0] is False

    mutated = dict(logs)
    mutated["edge_detection"] = {"inverse_edges": 1}
    assert CAND._admission(r24, mutated)[0] is False


def test_non_sidecar_tree_delegates_to_frozen_mature_product(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "plain.txt").write_text("plain\n" * 128, encoding="utf-8")
    out = tmp_path / "candidate.cmpct"
    sentinel = {"selected": "sentinel", "archive_bytes": 123, "format_revision": 24}
    calls = []

    def fake_build(root: Path, archive: Path) -> dict:
        calls.append((Path(root), Path(archive)))
        archive.write_bytes(b"sentinel")
        return dict(sentinel)

    # The promotion wrapper deliberately freezes the mature implementation before the public facade is rebound.
    # Prove non-sidecar traffic delegates to that exact frozen callable rather than a mutable module attribute.
    monkeypatch.setattr(CAND, "_BASE_BUILD", fake_build)
    result = CAND.build(source, out)
    assert len(calls) == 1
    assert calls[0] == (source, out)
    assert result["selected"] == "sentinel"
    assert result["logs_terminal"] is False
    assert result["logs_terminal_prefilter"]["eligible"] is False


def test_logs_prefilter_stops_when_structural_floor_is_proven(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "source"
    first = root / "a"
    later = root / "z"
    first.mkdir(parents=True)
    later.mkdir()
    for stem in ("one.log", "two.log"):
        (first / stem).write_bytes(b"plain")
        (first / f"{stem}.zst").write_bytes(b"sidecar")
    (later / "must-not-be-scanned.txt").write_bytes(b"late")

    real_scandir = CAND.os.scandir
    scanned: list[Path] = []

    def guarded_scandir(path):
        path = Path(path)
        scanned.append(path)
        if path == later:
            raise AssertionError("positive preflight kept scanning after admission floor")
        return real_scandir(path)

    monkeypatch.setattr(CAND.os, "scandir", guarded_scandir)
    result = CAND.logs_source_prefilter(root)
    assert result["eligible"] is True
    assert result["sidecar_pairs"] == CAND.MIN_SIDECAR_PAIRS
    assert result["sidecar_pairs_exact"] is False
    assert result["scan_terminated_at_admission_floor"] is True
    assert later not in scanned


def test_logs_prefilter_negative_result_remains_exact(tmp_path: Path) -> None:
    root = tmp_path / "source"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "a.log").write_bytes(b"plain")
    (root / "a.log.zst").write_bytes(b"sidecar")
    (nested / "b.log.gz").write_bytes(b"orphan")

    result = CAND.logs_source_prefilter(root)
    assert result["eligible"] is False
    assert result["sidecar_pairs"] == 1
    assert result["sidecar_pairs_exact"] is True
    assert result["scan_terminated_at_admission_floor"] is False
