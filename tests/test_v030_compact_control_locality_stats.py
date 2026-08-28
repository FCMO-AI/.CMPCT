from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(192):
        path = root / "records" / f"group-{i // 32:02d}" / f"measurement-record-with-a-long-stable-prefix-{i:04d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((f"row={i}\n" * 8).encode())


def test_compact_control_selective_read_reports_physical_locality_without_compat_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    _tree(src)
    r24 = tmp_path / "source.cmpct"
    PRODUCT._locality_bounded_r24_build(src, r24)
    out = tmp_path / "candidate.cmpct"
    CC._write_profile(r24, out)

    rel = "records/group-02/measurement-record-with-a-long-stable-prefix-0073.txt"
    expected = (src / rel).read_bytes()

    def forbidden(_parsed: dict) -> bytes:
        raise AssertionError("selected-member reads must not rebuild a compatibility r24 archive")

    monkeypatch.setattr(CC, "_rebuild_r24_bytes", forbidden)
    data, stats = CC.read_member_with_stats(out, rel)

    assert data == expected
    assert stats["format_revision"] == 25
    assert stats["format_profile"] == CC.PROFILE
    assert stats["source_format_revision"] == 24
    assert stats["compatibility_materialization"] is False
    assert stats["physical_payload_records_unchanged"] is True
    assert stats["physical_blob_reads"] == len(stats["physical_blob_indices"])
    assert stats["physical_blob_reads"] > 0
    assert int(stats["decoded_context_bytes"]) >= len(expected)
    assert float(stats["decoded_context_amplification"]) == pytest.approx(
        int(stats["decoded_context_bytes"]) / len(expected)
    )
    assert float(stats["decoded_context_amplification"]) <= 8.0
    assert int(stats["wrapper_control_raw_bytes"]) > 0
    assert int(stats["wrapper_control_comp_bytes"]) > 0


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
