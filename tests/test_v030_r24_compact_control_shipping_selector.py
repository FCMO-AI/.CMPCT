from __future__ import annotations

import os
from pathlib import Path
import random
import stat

from experiments import entropygraph_v030_release_product as PRODUCT


def _legacy_compact_control_source_shape(root: Path) -> dict:
    """Frozen pre-scandir semantics used only to ratchet source-shape identity."""
    root = Path(root)
    regular_files = 0
    logical_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                regular_files += 1
                logical_bytes += int(st.st_size)
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "average_regular_bytes": logical_bytes / max(1, regular_files),
    }


def test_compact_control_scandir_source_shape_preserves_legacy_semantics(tmp_path):
    source = tmp_path / "shape-source"
    (source / "nested").mkdir(parents=True)
    (source / "a.bin").write_bytes(b"a" * 4096)
    (source / "nested" / "b.bin").write_bytes(b"b" * 8193)
    (source / "empty").write_bytes(b"")
    try:
        (source / "file-link").symlink_to(source / "a.bin")
        (source / "dir-link").symlink_to(source / "nested", target_is_directory=True)
    except (OSError, NotImplementedError):
        pass

    expected = _legacy_compact_control_source_shape(source)
    actual = PRODUCT._compact_control_source_shape(source)
    assert actual == expected
    assert actual["regular_files"] == 3
    assert actual["logical_bytes"] == 4096 + 8193


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
