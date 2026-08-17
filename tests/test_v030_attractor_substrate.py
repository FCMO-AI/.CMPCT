from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_attractor_substrate as S


def test_phrase_split_is_exact_and_bounded() -> None:
    raw = (b"header|tenant=0042|status=active|" + bytes(range(64))) * 400
    for average in S.AVG_PHRASE_CANDIDATES:
        parts = S._split(raw, average)
        assert b"".join(parts) == raw
        assert all(len(part) <= min(S.MAX_PHRASE, average * 4) for part in parts)


def test_collect_content_addresses_exact_shared_phrases(tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir()
    common = (b"COMMON-PHRASE-" + bytes(range(64))) * 80
    (root / "a.bin").write_bytes(b"aaa" * 200 + common + b"tail-a" * 100)
    (root / "b.bin").write_bytes(b"bbb" * 200 + common + b"tail-b" * 100)
    _, raws, parses, uses = S._collect(root, 256)
    assert len(raws) == 2
    assert len(parses) == 2
    assert any(use > 1 for use in uses)


def test_complete_substrate_round_trip_and_strong_verify(tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir()
    shared = (b"id=0042 status=active payload=shared\n" * 2000)
    for index in range(4):
        (root / f"snapshot-{index}.txt").write_bytes(
            shared + f"version={index}\n".encode() + shared + bytes((index,)) * 4096
        )
    archive = tmp_path / "substrate.cmpct"
    stats = S._build_one(root, archive, 512, "encounter")
    assert stats["shared_phrase_ids"] > 0
    assert stats["exact_phrase_dedup_saved_raw_bytes"] > 0
    assert stats["max_decode_unit"] == 8 * 1024 * 1024
    verified = S.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == S.treehash(root)
    restored = tmp_path / "restored"
    S.extract(archive, restored)
    assert S.treehash(restored) == S.treehash(root)


def test_every_physical_pack_obeys_decode_unit(tmp_path: Path) -> None:
    phrases = [bytes((index % 251,)) * (256 * 1024) for index in range(80)]
    records, locations = S._pack_phrases(phrases)
    assert records
    assert len(locations) == len(phrases)
    assert all(record[1] <= S.MAX_DECODE_UNIT for record in records)


def test_path_policy_rejects_traversal_and_windows_separator() -> None:
    for unsafe in ("../escape", "/absolute", "a/../escape", "a\\escape", "", "x\x00y"):
        with pytest.raises(RuntimeError):
            S._safe_relpath(unsafe)


def test_primary_metadata_corruption_recovers_from_authenticated_tail(tmp_path: Path) -> None:
    root = tmp_path / "root"; root.mkdir()
    for index in range(3):
        (root / f"f{index}.txt").write_bytes((b"shared-row\n" * 3000) + bytes((index,)) * 200)
    archive = tmp_path / "substrate.cmpct"
    S._build_one(root, archive, 512, "lexicographic")
    original_tree = S.treehash(root)

    data = bytearray(archive.read_bytes())
    header = bytes(data[:S.HDR.size])
    _, metadata_compressed, _, _, _, _, _, _ = S.HDR.unpack(header)
    assert metadata_compressed > 4
    data[S.HDR.size + metadata_compressed // 2] ^= 0x5A
    archive.write_bytes(data)

    verified = S.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == original_tree


def test_lexicographic_order_is_only_a_physical_hypothesis() -> None:
    phrases = [b"z-last", b"alpha-2", b"alpha-1", b"middle"]
    parses = [[0, 1, 2, 3, 1]]
    ordered, remapped, order = S._reorder(phrases, parses, "lexicographic")
    assert ordered == sorted(phrases)
    restored = [ordered[phrase_id] for phrase_id in remapped[0]]
    assert restored == [phrases[phrase_id] for phrase_id in parses[0]]
    assert sorted(order) == list(range(len(phrases)))
