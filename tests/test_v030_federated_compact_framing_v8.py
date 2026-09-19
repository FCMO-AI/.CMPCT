from __future__ import annotations

import binascii
import hashlib
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07


def _fixture_bytes() -> tuple[bytes, bytes, bytes, bytes]:
    # Integer root key 7 is the narrowly authorized EG07 filesystem-control slot.
    meta = {"v": 4, "pack_count": 1, "files": [], "micro": [], "tree_sha256": "0" * 64, 7: b"fs"}
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = V25.zc(meta_raw, 1)
    meta_hash = hashlib.sha256(meta_raw).digest()
    pack_raw = (b"compact-framing-payload-" * 137) + b"tail"
    pack_comp = V25.zc(pack_raw, 1)
    pack_hash = hashlib.sha256(pack_raw).digest()
    crc = binascii.crc32(pack_raw) & 0xFFFFFFFF
    blob = b"".join(
        (
            EG08.HDR.pack(EG08.MAGIC, len(meta_comp), meta_hash),
            meta_comp,
            EG08.PH.pack(1, len(pack_comp), crc, pack_hash),
            pack_comp,
            meta_comp,
            EG08.FTR.pack(EG08.TAIL_MAGIC, len(meta_comp), meta_hash),
        )
    )
    return blob, meta_raw, meta_comp, pack_raw


def test_compact_parser_recovers_sizes_from_authenticated_frames(tmp_path: Path) -> None:
    blob, meta_raw, meta_comp, pack_raw = _fixture_bytes()
    archive = tmp_path / "fixture.cmpct"
    archive.write_bytes(blob)
    parsed = EG08._parse(archive)
    assert parsed["meta_raw"] == meta_raw
    assert parsed["meta_comp"] == meta_comp
    assert parsed["meta"]["pack_count"] == 1
    codec, usize, _csize, _crc, _sha, _payload = parsed["packs"][0]
    assert codec == 1
    assert usize == len(pack_raw)
    assert parsed["primary_error"] is None


def test_compact_parser_has_operational_two_way_metadata_recovery(tmp_path: Path) -> None:
    blob, _meta_raw, meta_comp, _pack_raw = _fixture_bytes()
    primary_bad = bytearray(blob)
    primary_bad[EG08.HDR.size + max(0, len(meta_comp) // 2)] ^= 0x01
    p = tmp_path / "primary-bad.cmpct"
    p.write_bytes(primary_bad)
    recovered = EG08._parse(p)
    assert recovered["primary_error"] is not None

    tail_bad = bytearray(blob)
    tail_start = len(blob) - EG08.FTR.size - len(meta_comp)
    tail_bad[tail_start + max(0, len(meta_comp) // 2)] ^= 0x01
    t = tmp_path / "tail-bad.cmpct"
    t.write_bytes(tail_bad)
    assert EG08._parse(t)["primary_error"] is None

    both_bad = bytearray(primary_bad)
    both_bad[tail_start + max(0, len(meta_comp) // 2)] ^= 0x01
    b = tmp_path / "both-bad.cmpct"
    b.write_bytes(both_bad)
    with pytest.raises(RuntimeError, match="no authenticated compact metadata copy"):
        EG08._parse(b)


def test_compact_framing_expands_to_exact_inherited_header_semantics(tmp_path: Path) -> None:
    blob, meta_raw, meta_comp, pack_raw = _fixture_bytes()
    archive = tmp_path / "compact.cmpct"
    expanded = tmp_path / "expanded.cmpct"
    archive.write_bytes(blob)
    parsed = EG08._expand_to_eg07(archive, expanded)
    raw = expanded.read_bytes()
    magic, mcs, mus, pack_count, digest = V25.HDR.unpack_from(raw, 0)
    assert magic == EG07.MAGIC
    assert mcs == len(meta_comp)
    assert mus == len(meta_raw)
    assert pack_count == 1
    assert digest == hashlib.sha256(meta_raw).digest()
    pos = V25.HDR.size + mcs
    codec, usize, csize, crc, sha = V25.PH.unpack_from(raw, pos)
    assert codec == 1
    assert usize == len(pack_raw)
    assert csize == len(parsed["packs"][0][-1])
    assert crc == (binascii.crc32(pack_raw) & 0xFFFFFFFF)
    assert sha == hashlib.sha256(pack_raw).digest()


def test_compact_metadata_key_ownership_is_exactly_eg07() -> None:
    # EG08 parses EG07-authenticated metadata after EG07 has restored EG06's process-global key to 6.
    # The compact parser must therefore own key 7 explicitly, not accept either historical sibling key.
    EG08._validate_metadata_map({"v": 4, EG07.EMBEDDED_FS_KEY: b"fs"}, root=True)
    with pytest.raises(RuntimeError, match="unauthorized non-string root key"):
        EG08._validate_metadata_map({"v": 4, 6: b"old-eg06-slot"}, root=True)
    with pytest.raises(RuntimeError, match="non-string nested key"):
        EG08._validate_metadata_map({"v": 4, "nested": {EG07.EMBEDDED_FS_KEY: b"not-root"}}, root=True)


def test_compact_header_saving_formula_exceeds_office_remaining_gap() -> None:
    fixed = (V25.HDR.size - EG08.HDR.size) + (V25.FTR.size - EG08.FTR.size)
    per_pack = V25.PH.size - EG08.PH.size
    assert fixed == 20
    assert per_pack == 8
    # Three packs are already enough to recover >42 bytes. Office's federated graph has many more than this;
    # the exact frontier workflow measures its real pack count before claiming the office result.
    assert fixed + 3 * per_pack > 42
