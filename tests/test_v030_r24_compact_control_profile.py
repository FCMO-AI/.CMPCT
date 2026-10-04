from __future__ import annotations

from pathlib import Path

import pytest

from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    # Long repeated path structure makes compact control unambiguously smaller without depending on a frozen corpus.
    # Keep every text member exactly 32 KiB: the shipping r24 release pack target is bounded to 8x the largest
    # regular member, so equal-size members form at most eight-member S_PACKs and the fixture itself obeys the
    # <=8x selective-read locality law that C25CC01 is required to inherit unchanged.
    for i in range(192):
        p = root / "records" / f"group-{i // 32:02d}" / f"measurement-record-with-a-long-stable-prefix-{i:04d}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        seed = f"row={i:04d}\n".encode()
        p.write_bytes((seed * ((32 * 1024 + len(seed) - 1) // len(seed)))[: 32 * 1024])


def _flip(path: Path, offset: int) -> None:
    payload = bytearray(path.read_bytes())
    payload[offset] ^= 0x5A
    path.write_bytes(payload)


def test_compact_control_preserves_physical_payload_and_semantic_tree(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    assert PRODUCT.strong_verify(r24)["ok"] is True

    out = tmp_path / "candidate.cmpct"
    stats = CC._write_profile(r24, out)
    verified = CC.strong_verify(out)
    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == CC.PROFILE
    assert verified["pack_verification_policy"] == "authenticated-physical-pack-sha-once"
    assert verified["verified_pack_records"] > 0
    assert verified["compatibility_materialization"] is False
    assert stats["archive_bytes"] < stats["source_r24_bytes"]
    assert stats["physical_payload_records_unchanged"] is True
    assert stats["two_authenticated_control_copies"] is True
    assert stats["semantic_index_roundtrip_exact"] is True
    assert CC.physical_data_span(out) == CC._source_r24_parts(r24)[1]
    assert verified["tree_sha256"] == PRODUCT.strong_verify(r24)["tree_sha256"]

    # C25CC01 has earned the release-product reader boundary. Ratchet the public verifier to the same
    # exact semantic tree instead of preserving the obsolete pre-selector rejection expectation.
    product_verified = PRODUCT.strong_verify(out)
    assert product_verified["ok"] is True
    assert product_verified["format_revision"] == 25
    assert product_verified["format_profile"] == CC.PROFILE
    assert product_verified["tree_sha256"] == verified["tree_sha256"]
    assert PRODUCT._revision_for_archive(out) == (CC.REVISION, CC.PROFILE)


def test_compact_control_recovers_either_authenticated_copy(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)
    pristine = out.read_bytes()

    _magic, _version, _flags, primary_cbytes, _raw_bytes, _data_bytes, _sha = R24.HDR.unpack_from(pristine, 0)
    footer_off = len(pristine) - R24.FTR.size
    _fm, _a, _b, _c, _d, tail_cbytes, _tail_raw, _res, _tail_sha = R24.FTR.unpack_from(pristine, footer_off)
    primary_offset = R24.HDR.size + max(0, int(primary_cbytes) // 2)
    tail_start = footer_off - int(tail_cbytes)
    tail_offset = tail_start + max(0, int(tail_cbytes) // 2)

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(pristine)
    _flip(primary_bad, primary_offset)
    pv = CC.strong_verify(primary_bad)
    assert pv["ok"] is True
    assert pv["compact_control_recovery_source"] == "tail"

    tail_bad = tmp_path / "tail-bad.cmpct"
    tail_bad.write_bytes(pristine)
    _flip(tail_bad, tail_offset)
    tv = CC.strong_verify(tail_bad)
    assert tv["ok"] is True
    assert tv["compact_control_recovery_source"] == "primary"

    both_bad = tmp_path / "both-bad.cmpct"
    both_bad.write_bytes(pristine)
    _flip(both_bad, primary_offset)
    _flip(both_bad, tail_offset)
    assert CC.strong_verify(both_bad)["ok"] is False
    assert PRODUCT.strong_verify(both_bad)["ok"] is False


def test_compact_control_rejects_corrupted_physical_pack(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)

    parsed = CC._parse(out)
    index = parsed["index"]
    packed = next(row for row in index["files"] if row[6] and row[6][0] == R24.S_PACK)
    pack_idx = int(packed[6][1])
    blob_off = int(index["blobs"][pack_idx][0])
    payload = out.read_bytes()
    _magic, _version, _flags, primary_cbytes, _raw_bytes, _data_bytes, _sha = R24.HDR.unpack_from(payload, 0)
    record_pos = R24.HDR.size + int(primary_cbytes) + blob_off
    _m, _codec, _flags2, _res, _usize, csize, meta_len, _crc, _blob_sha = R24.BHDR.unpack_from(payload, record_pos)
    assert int(csize) > 0
    corrupt_at = record_pos + R24.BHDR.size + int(meta_len) + min(3, int(csize) - 1)

    bad = tmp_path / "physical-bad.cmpct"
    bad.write_bytes(payload)
    _flip(bad, corrupt_at)
    verified = CC.strong_verify(bad)
    assert verified["ok"] is False
    assert PRODUCT.strong_verify(bad)["ok"] is False


def test_compact_control_reader_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    out = tmp_path / "candidate.cmpct"
    stats = CC.build(src, out)
    assert stats["format_profile"] == CC.PROFILE
    members = CC.list_members(out)
    files = [row for row in members if row["kind"] == "file"]
    assert len(files) == 192
    rel = files[73]["path"]
    expected = (src / rel).read_bytes()
    assert CC.read_member(out, rel) == expected
    direct, direct_stats = CC.read_member_with_stats(out, rel)
    assert direct == expected
    assert direct_stats["decoded_context_amplification"] <= 8.0

    # Public release-product dispatch must use the exact same C25CC01 semantic owner rather than a second grammar.
    assert PRODUCT.list_members(out) == members
    public, public_stats = PRODUCT.read_member_with_stats(out, rel)
    assert public == expected
    assert public_stats == direct_stats
    assert PRODUCT.read_member(out, rel) == expected

    dst = tmp_path / "dst"
    CC.extract(out, dst)
    assert (dst / rel).read_bytes() == expected
    public_dst = tmp_path / "public-dst"
    PRODUCT.extract(out, public_dst)
    assert (public_dst / rel).read_bytes() == expected


def test_compact_control_ephemeral_r24_uses_fast_index_without_semantic_change(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)

    parsed = CC._parse(out)
    compat = tmp_path / "compat-r24.cmpct"
    compat.write_bytes(CC._rebuild_r24_bytes(parsed))
    baseline = PRODUCT.strong_verify(r24)
    rebuilt = PRODUCT.strong_verify(compat)

    assert CC.COMPAT_INDEX_LEVEL == 1
    assert baseline["ok"] is True
    assert rebuilt["ok"] is True
    assert rebuilt["format_revision"] == 24
    assert rebuilt["tree_sha256"] == baseline["tree_sha256"]
    candidate = CC.strong_verify(out)
    assert candidate["ok"] is True
    assert candidate["compatibility_index_level"] is None
    assert candidate["compatibility_materialization"] is False
    assert candidate["pack_verification_policy"] == "authenticated-physical-pack-sha-once"
    assert candidate["tree_sha256"] == baseline["tree_sha256"]


def test_compact_control_strong_verify_never_materializes_compatibility_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)
    baseline = PRODUCT.strong_verify(r24)
    assert baseline["ok"] is True

    def forbidden(_parsed: dict) -> bytes:
        raise AssertionError("strong verification must not rebuild a compatibility r24 archive")

    monkeypatch.setattr(CC, "_rebuild_r24_bytes", forbidden)
    verified = CC.strong_verify(out)
    assert verified["ok"] is True
    assert verified["compatibility_materialization"] is False
    assert verified["tree_sha256"] == baseline["tree_sha256"]
