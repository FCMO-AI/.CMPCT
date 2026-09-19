from __future__ import annotations

import os
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v6 as EG06
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07
from experiments import entropygraph_v030_fs_implicit_v5 as V5
from experiments import entropygraph_v030_fs_implicit_v6 as V6
from experiments import entropygraph_v030_product_fs as FS


def _manifest(root: Path) -> bytes:
    raw, _regular, _stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=EG01.MAX_PATH_BYTES,
        max_profile_files=EG01.MAX_PROFILE_FILES,
        max_profile_logical_bytes=EG01.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=EG01.MAX_MANIFEST_ENTRIES,
    )
    return raw


def test_implicit_v6_preserves_semantics_and_beats_v5_on_mixed_runs(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    for index in range(80):
        path = root / f"doc-{index:03d}.txt"
        path.write_text(f"document {index}\n", encoding="utf-8")
        path.chmod(0o644 if index % 9 else 0o600)
        # Deliberately create many singleton non-default runs among long default runs.
        stamp = 1_700_000_000_000_000_000 + (index % 11 == 0) * index
        os.utime(path, ns=(stamp, stamp))
    (root / "nested").mkdir()
    (root / "nested").chmod(0o755)

    v1 = _manifest(root)
    v5 = V5.encode_v1(v1, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    v6 = V6.encode_v1(v1, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    assert V6.semantics_equal(v1, v6, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    assert len(v6) < len(v5)


def test_implicit_v6_scalar_default_and_repeated_override_round_trip() -> None:
    assert V6._decode_runs([0, -3, [1, 2], [-2, 1, 3]], max_entries=16) == [
        [0], [0], [0], [0], [1, 2], [1, 3], [1, 3]
    ]
    with pytest.raises(RuntimeError, match="positive scalar"):
        V6._decode_runs([2], max_entries=16)
    with pytest.raises(RuntimeError, match="exceeds policy"):
        V6._decode_runs([-17], max_entries=16)
    with pytest.raises(RuntimeError, match="empty"):
        V6._decode_runs([[-2]], max_entries=16)


def test_implicit_v6_directory_uses_short_arity_and_rejects_payload(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "dir").mkdir()
    (root / "file.txt").write_text("x", encoding="utf-8")
    raw = V6.encode_v1(_manifest(root), max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)
    payload = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    directory_rows = [row for row in payload[3] if row[2] == 1]
    assert directory_rows and all(len(row) == 4 for row in directory_rows)
    bad = list(payload)
    bad_rows = [list(row) for row in payload[3]]
    bad_rows[0] = [*bad_rows[0], None]
    bad[3] = bad_rows
    with pytest.raises(RuntimeError, match="directory carries unexpected payload"):
        V6._unpack(msgpack.packb(bad, use_bin_type=True), max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=EG01.MAX_MANIFEST_ENTRIES)


def test_eg07_preserves_single_historical_engine_owner() -> None:
    assert EG07._LOCK is EG06._LOCK
    assert EG07._PENDING_CONTROL is EG06._PENDING_CONTROL
