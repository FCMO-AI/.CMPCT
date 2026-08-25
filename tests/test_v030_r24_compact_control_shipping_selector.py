from __future__ import annotations

import random

from experiments import entropygraph_v030_release_product as PRODUCT


def test_compact_control_prefilter_is_only_a_conservative_work_filter():
    # This cheap prefilter cannot publish anything by itself. It deliberately admits a subset of the independently
    # proven terminal envelope and rejects small-average-file trees that would otherwise pay a redundant r24 build.
    assert PRODUCT._compact_control_source_prefilter(
        {"regular_files": 1200, "logical_bytes": 1200 * 4096, "average_regular_bytes": 4096.0}
    )
    assert not PRODUCT._compact_control_source_prefilter(
        {"regular_files": 1200, "logical_bytes": 1200 * 2048, "average_regular_bytes": 2048.0}
    )
    assert not PRODUCT._compact_control_source_prefilter(
        {"regular_files": 999, "logical_bytes": 999 * 8192, "average_regular_bytes": 8192.0}
    )


def test_release_product_terminalizes_proven_compact_control_shape(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rng = random.Random(0xC25CC01)
    expected = {}
    for index in range(1050):
        rel = f"shard-{index:04d}.dat"
        payload = rng.randbytes(4096)
        (source / rel).write_bytes(payload)
        expected[rel] = payload

    archive = tmp_path / "shipping.cmpct"
    stats = PRODUCT.build(source, archive)

    assert stats["selected"] == "r24-compact-control"
    assert stats["format_revision"] == 25
    assert stats["format_profile"] == "r24-compact-control-v1"
    assert stats["terminal_compact_control"] is True
    assert stats["speculative_r25_search_skipped"] is True
    assert stats["terminal_compact_control_admission"]["r24_to_logical"] >= 0.98
    assert stats["terminal_compact_control_admission"]["candidate_to_r24"] <= 0.9995
    assert PRODUCT._revision_for_archive(archive) == (25, "r24-compact-control-v1")

    verified = PRODUCT.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == "r24-compact-control-v1"
    assert PRODUCT.read_member(archive, "shard-0000.dat") == expected["shard-0000.dat"]
    assert PRODUCT.read_member(archive, "shard-1049.dat") == expected["shard-1049.dat"]
    members = PRODUCT.list_members(archive)
    files = {row["path"] for row in members if row["kind"] == "file"}
    assert files == set(expected)
