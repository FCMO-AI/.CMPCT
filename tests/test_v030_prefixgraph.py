from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_prefixgraph as pg


def _similar_family(root: Path) -> None:
    root.mkdir(parents=True)
    base = (b"record|tenant=17|status=active|" * 10_000) + bytes(range(256)) * 64
    for index in range(5):
        data = bytearray(base)
        marker = (f"version={index};".encode() * 71)
        at = 12_000 + index * 777
        data[at:at] = marker
        data[40_000 + index:40_032 + index] = bytes([index + 3]) * 32
        (root / f"snapshot-{index:02d}.bin").write_bytes(data)


def test_prefixgraph_roundtrip_selects_depth_one(tmp_path: Path) -> None:
    source = tmp_path / "source"; _similar_family(source)
    archive = tmp_path / "family.cmpct"; stats = pg.build(source, archive)
    assert stats["prefix_records"] > 0
    assert stats["max_dependency_depth"] == 1
    assert stats["archive_bytes"] <= stats["all_direct_bytes"]
    verified = pg.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == pg.treehash(source)

    extracted = tmp_path / "out"; pg.extract(archive, extracted)
    assert pg.treehash(extracted) == pg.treehash(source)


def test_anchor_tournament_is_complete_costed(tmp_path: Path) -> None:
    source = tmp_path / "source"; _similar_family(source)
    archive = tmp_path / "family.cmpct"; stats = pg.build(source, archive)
    assert stats["anchor_auditions"] == 5
    assert stats["saving_vs_all_direct_bytes"] >= 0
    # Footnote: this assertion is about the serialized artifact, not a payload estimate.  Metadata and
    # recovery-copy overhead are already included in both sides before an anchor is allowed to win.
    assert archive.stat().st_size == stats["archive_bytes"]


def test_winner_only_retention_preserves_legacy_full_tournament_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"; _similar_family(source)
    files = sorted(path for path in source.rglob("*") if path.is_file())
    rels = [path.relative_to(source).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    tree = pg._treehash_parts(rels, raws)
    direct_payloads = [pg._compress(raw) for raw in raws]

    # Reconstruct the historical materialized-list tournament independently.  The shipping builder may retain
    # only one incumbent, but it must still construct every nominated anchor and choose the exact same complete
    # bytes under the original `(archive_bytes, anchor)` tie law.
    legacy_candidates = [pg._serialize_candidate(rels, raws, direct_payloads, tree, None)]
    legacy_candidates.extend(
        pg._serialize_candidate(rels, raws, direct_payloads, tree, anchor)
        for anchor in pg._anchor_indices(len(raws))
    )
    legacy_blob, legacy_stats = min(legacy_candidates, key=lambda item: pg._candidate_key(*item))

    archive = tmp_path / "winner-only.cmpct"
    stats = pg.build(source, archive)
    assert archive.read_bytes() == legacy_blob
    assert stats["anchor"] == legacy_stats["anchor"]
    assert stats["archive_bytes"] == legacy_stats["archive_bytes"]
    assert stats["anchor_auditions"] == len(pg._anchor_indices(len(raws)))
    assert pg.strong_verify(archive)["tree_sha256"] == tree


def test_direct_zstd_floor_is_compressed_once_per_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"; _similar_family(source)
    archive = tmp_path / "family.cmpct"
    original = pg._compress
    calls = 0

    def counted(raw: bytes) -> bytes:
        nonlocal calls
        calls += 1
        return original(raw)

    monkeypatch.setattr(pg, "_compress", counted)
    stats = pg.build(source, archive)
    # Footnote: anchor auditions are intentionally numerous, but their direct Zstd floor is invariant.
    # Locking calls==files prevents a future refactor from silently restoring O(files * anchors) duplicate
    # direct compression work while leaving the serialized bytes deceptively unchanged.
    assert stats["anchor_auditions"] == 5
    assert calls == stats["files"] == 5
    assert pg.strong_verify(archive)["tree_sha256"] == pg.treehash(source)


def test_payload_tamper_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"; _similar_family(source)
    archive = tmp_path / "family.cmpct"; pg.build(source, archive)
    data = bytearray(archive.read_bytes())
    meta_magic, mcs, _, _ = pg.HEADER.unpack_from(data, 0)
    assert meta_magic == pg.MAGIC
    payload_start = pg.HEADER.size + mcs
    data[payload_start + 3] ^= 0x80
    archive.write_bytes(data)
    with pytest.raises(RuntimeError):
        pg.strong_verify(archive)


def test_path_policy_rejects_traversal() -> None:
    for bad in ("../escape", "/absolute", "a\\b", "a/../b", ""):
        with pytest.raises(RuntimeError):
            pg._safe_relpath(bad)


def test_anchor_auditions_are_bounded() -> None:
    indices = pg._anchor_indices(10_000)
    assert len(indices) <= pg.MAX_ANCHOR_AUDITIONS
    assert indices[0] == 0 and indices[-1] == 9_999
    assert indices == sorted(set(indices))
