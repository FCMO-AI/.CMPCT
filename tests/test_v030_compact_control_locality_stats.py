from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    """Positive compact-control tree whose r24 packs stay exactly inside the 8x law."""
    root.mkdir(parents=True, exist_ok=True)
    for i in range(192):
        path = root / "records" / f"group-{i // 32:02d}" / f"measurement-record-with-a-long-stable-prefix-{i:04d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = f"row={i:04d}|".encode()
        path.write_bytes((prefix + bytes([65 + i % 23]) * 128)[:128])


def _locality_violating_tree(root: Path) -> None:
    """Reproduce the small-member pack shape that previously yielded a 9x selected read."""
    root.mkdir(parents=True, exist_ok=True)
    for i in range(192):
        path = root / "records" / f"group-{i // 32:02d}" / f"variable-record-{i:04d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 64 if i % 17 == 0 else 48
        path.write_bytes((f"{i:04d}|".encode() + bytes([97 + i % 19]) * size)[:size])


def test_compact_control_selective_read_reports_physical_locality_without_compat_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    stats = CC._write_profile(r24, out)

    assert float(stats["locality_admission"]["max_s_pack_member_amplification"]) <= 8.0
    assert int(stats["locality_admission"]["max_s_pack_decode_unit_bytes"]) <= 8 * 1024 * 1024

    rel = "records/group-02/measurement-record-with-a-long-stable-prefix-0073.txt"
    expected = (src / rel).read_bytes()

    def forbidden(_parsed: dict) -> bytes:
        raise AssertionError("selected-member reads must not rebuild a compatibility r24 archive")

    monkeypatch.setattr(CC, "_rebuild_r24_bytes", forbidden)
    data, read_stats = CC.read_member_with_stats(out, rel)

    assert data == expected
    assert read_stats["format_revision"] == 25
    assert read_stats["format_profile"] == CC.PROFILE
    assert read_stats["source_format_revision"] == 24
    assert read_stats["compatibility_materialization"] is False
    assert read_stats["physical_payload_records_unchanged"] is True
    assert read_stats["physical_blob_reads"] == len(read_stats["physical_blob_indices"])
    assert read_stats["physical_blob_reads"] > 0
    assert int(read_stats["decoded_context_bytes"]) >= len(expected)
    assert float(read_stats["decoded_context_amplification"]) == pytest.approx(
        int(read_stats["decoded_context_bytes"]) / len(expected)
    )
    assert float(read_stats["decoded_context_amplification"]) <= 8.0
    assert int(read_stats["wrapper_control_raw_bytes"]) > 0
    assert int(read_stats["wrapper_control_comp_bytes"]) > 0


def test_compact_control_selective_read_matches_materialized_r24_semantics(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)

    rel = "records/group-04/measurement-record-with-a-long-stable-prefix-0141.txt"
    direct, stats = CC.read_member_with_stats(out, rel)
    baseline, _baseline_stats = PRODUCT.read_member_with_stats(r24, rel)

    assert direct == baseline == (src / rel).read_bytes()
    assert int(stats["decoded_context_bytes"]) >= len(direct)
    assert float(stats["decoded_context_amplification"]) <= 8.0

    # The fused verification pass must preserve the exact canonical r24 semantic tree grammar.
    wrapped_verified = CC.strong_verify(out)
    r24_verified = PRODUCT.strong_verify(r24)
    assert wrapped_verified["ok"] is True
    assert r24_verified["ok"] is True
    assert wrapped_verified["tree_sha256"] == r24_verified["tree_sha256"]


def test_compact_control_rejects_inherited_r24_pack_above_locality_ceiling(tmp_path: Path) -> None:
    src = tmp_path / "violating-src"
    _locality_violating_tree(src)
    r24 = tmp_path / "violating-source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "must-not-exist.cmpct"

    with pytest.raises(CC.ProfileNotEligible, match="exceeds release locality"):
        CC._write_profile(r24, out)
    assert not out.exists()
