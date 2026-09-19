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
    # This cheap prefilter cannot publish anything by itself. The 1,200-file boundary is frozen from exact
    # frozen+unseen/adversarial evidence and rejects the measured 1,162-file counterexample class before r24 work.
    assert PRODUCT._CC_PREFILTER_MIN_REGULAR_FILES == 1200
    assert PRODUCT._CC_PREFILTER_MIN_AVG_REGULAR_BYTES == 4096
    assert PRODUCT._compact_control_source_prefilter(
        {"regular_files": 1200, "logical_bytes": 1200 * 4096, "average_regular_bytes": 4096.0}
    )
    assert not PRODUCT._compact_control_source_prefilter(
        {"regular_files": 1200, "logical_bytes": 1200 * 2048, "average_regular_bytes": 2048.0}
    )
    assert not PRODUCT._compact_control_source_prefilter(
        {"regular_files": 1199, "logical_bytes": 1199 * 8192, "average_regular_bytes": 8192.0}
    )


def test_compact_control_representation_audit_rejects_locality_unsafe_pack():
    """Admission must fail closed from authenticated representation facts, independent of workload identity."""
    cc = PRODUCT._compact_control_module()
    r24 = cc.R24
    index = {
        "files": [
            ["tiny.bin", r24.K_FILE, 0, 0, 37, None, [r24.S_PACK, 0, 0, 37]],
        ],
        # The locality audit intentionally consumes only the decoded-byte field for the referenced physical blob.
        "blobs": [[0, 213_969, 0, 0, 0]],
    }
    try:
        cc._audit_s_pack_locality(index)
    except cc.ProfileNotEligible as exc:
        message = str(exc)
        assert "exceeds release locality" in message
        assert "decoded=213969" in message
        assert "logical=37" in message
    else:
        raise AssertionError("locality-unsafe S_PACK unexpectedly passed compact-control admission")


def test_release_product_compact_control_never_publishes_above_locality_limit(tmp_path):
    """A source-shape prefilter is never publication authority for C25CC01.

    This deterministic high-file-count tree is intentionally inside the cheap structural prefilter. Earlier r24
    packing revisions made this fixture locality-unsafe; the current locality-bounded r24 builder may instead produce
    a safe pack layout. The regression therefore ratchets the invariant that matters: if C25CC01 is published, its
    authenticated representation audit must prove both the <=8x selected-member amplification law and the <=8 MiB
    decode-unit law. Unsafe layouts are covered directly by the representation-level test above.
    """
    source = tmp_path / "source"
    source.mkdir()
    rng = random.Random(0xC25CC01)
    expected = {}
    for index in range(1250):
        rel = f"shard-{index:04d}.dat"
        payload = rng.randbytes(4096)
        (source / rel).write_bytes(payload)
        expected[rel] = payload

    shape = PRODUCT._compact_control_source_shape(source)
    assert PRODUCT._compact_control_source_prefilter(shape) is True

    archive = tmp_path / "shipping.cmpct"
    stats = PRODUCT.build(source, archive)

    assert stats["selected"] in {"r24-fallback", "r24-compact-control"}
    if stats["selected"] == "r24-compact-control":
        locality = stats["locality_admission"]
        assert locality["max_s_pack_member_amplification"] <= locality["max_member_read_amplification"] <= 8.0
        assert locality["max_s_pack_decode_unit_bytes"] <= locality["max_decode_unit_bytes"] <= 8 * 1024 * 1024
        assert stats.get("terminal_compact_control") is True
        assert PRODUCT._is_compact_control_archive(archive) is True
    else:
        assert stats.get("terminal_compact_control") is not True
        assert PRODUCT._is_compact_control_archive(archive) is False
        assert PRODUCT._revision_for_archive(archive)[0] == 24

    verified = PRODUCT.strong_verify(archive)
    assert verified["ok"] is True
    assert PRODUCT.read_member(archive, "shard-0000.dat") == expected["shard-0000.dat"]
    assert PRODUCT.read_member(archive, "shard-1249.dat") == expected["shard-1249.dat"]
    members = PRODUCT.list_members(archive)
    files = {row["path"] for row in members if row["kind"] == "file"}
    assert files == set(expected)
