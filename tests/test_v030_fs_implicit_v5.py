from __future__ import annotations

import os
from pathlib import Path

from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_fs_implicit_v4 as V4
from experiments import entropygraph_v030_fs_implicit_v5 as V5
from experiments import entropygraph_v030_product_fs as FS


def test_implicit_v5_preserves_semantics_and_compresses_repeated_regular_metadata(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    # Canonically sorted regular files with identical stat metadata are the exact redundancy EG06 targets.
    for index in range(96):
        path = root / f"doc-{index:03d}.txt"
        path.write_text(f"document {index}\n", encoding="utf-8")
        path.chmod(0o644)
        os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))

    v1, _regular, _stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=EG01.MAX_PATH_BYTES,
        max_profile_files=EG01.MAX_PROFILE_FILES,
        max_profile_logical_bytes=EG01.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=EG01.MAX_MANIFEST_ENTRIES,
    )
    v4 = V4.encode_v1(v1, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    v5 = V5.encode_v1(v1, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)

    assert V5.semantics_equal(v1, v5, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    assert len(v5) < len(v4)
    # The repeated [0] metadata vector should collapse materially, not merely win by a byte of version framing.
    assert len(v4) - len(v5) >= 64


def test_implicit_v5_rejects_run_overflow() -> None:
    import msgpack

    raw = msgpack.packb([5, [0, 0, 0, 0, []], [[9, [0]]], []], use_bin_type=True)
    try:
        V5._unpack(raw, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=8)
    except RuntimeError as exc:
        assert "exceeds policy" in str(exc) or "run length" in str(exc) or "count" in str(exc)
    else:
        raise AssertionError("oversized metadata run was accepted")
