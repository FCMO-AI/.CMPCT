from __future__ import annotations

from pathlib import Path

import pytest

from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    # Long repeated path structure makes compact control unambiguously smaller without depending on a frozen corpus.
    for i in range(192):
        p = root / "records" / f"group-{i // 32:02d}" / f"measurement-record-with-a-long-stable-prefix-{i:04d}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((f"row={i}\n" * 8).encode())


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
    assert stats["archive_bytes"] < stats["source_r24_bytes"]
    assert stats["physical_payload_records_unchanged"] is True
    assert stats["two_authenticated_control_copies"] is True
    assert stats["semantic_index_roundtrip_exact"] is True
    assert CC.physical_data_span(out) == CC._source_r24_parts(r24)[1]
    assert verified["tree_sha256"] == PRODUCT.strong_verify(r24)["tree_sha256"]

    # Candidate remains outside the shipping facade until native/Android/selector promotion is independently earned.
    assert PRODUCT.strong_verify(out).get("ok") is not True


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
    assert CC.read_member(out, rel) == (src / rel).read_bytes()
    dst = tmp_path / "dst"
    CC.extract(out, dst)
    assert (dst / rel).read_bytes() == (src / rel).read_bytes()
