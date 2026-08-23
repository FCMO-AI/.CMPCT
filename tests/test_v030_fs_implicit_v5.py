from __future__ import annotations

import os
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v6 as EG06
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
    raw = msgpack.packb([5, [0, 0, 0, 0, []], [[9, [0]]], []], use_bin_type=True)
    try:
        V5._unpack(raw, max_path_bytes=EG01.MAX_PATH_BYTES, max_entries=8)
    except RuntimeError as exc:
        assert "exceeds policy" in str(exc) or "run length" in str(exc) or "count" in str(exc)
    else:
        raise AssertionError("oversized metadata run was accepted")


def test_eg06_preserves_parent_engine_lock_contract() -> None:
    """Framing-only descendants must keep the one audited V25 mutation owner.

    The selective-effort harness temporarily swaps its candidate module and calls ``CAND._LOCK`` before it enters
    the inherited V25 engine.  A child that keeps EG05's engine but drops the lock attribute can pass filesystem
    unit tests and then fail only after the expensive frozen corpus is built.  Identity (not merely lock type)
    matters here: a fresh lock would permit two competing mutations of the same process-global historical engine.
    """

    assert EG06._LOCK is EG05._LOCK
    assert EG06._LOCK is EG01._LOCK
    assert EG06._PENDING_CONTROL is EG05._PENDING_CONTROL


def test_eg06_metadata_decoder_allows_only_its_compact_root_integer_key() -> None:
    base = {
        "v": 4,
        "pack_count": 0,
        "files": [],
        "micro": [],
        EG06.EMBEDDED_FS_KEY: b"control",
    }
    raw = msgpack.packb(base, use_bin_type=True)
    decoded = EG06._unpack_authenticated_metadata(raw)
    assert decoded[EG06.EMBEDDED_FS_KEY] == b"control"

    wrong_root = dict(base)
    wrong_root[7] = b"not-authorized"
    with pytest.raises(RuntimeError, match="unauthorized non-string root key"):
        EG06._unpack_authenticated_metadata(msgpack.packb(wrong_root, use_bin_type=True))

    nested_integer_key = dict(base)
    nested_integer_key["bad"] = {1: "nested"}
    with pytest.raises(RuntimeError, match="unauthorized nested non-string map key"):
        EG06._unpack_authenticated_metadata(msgpack.packb(nested_integer_key, use_bin_type=True))


def test_eg06_variant_rebinds_only_v25_open_ar_and_restores_it() -> None:
    original = EG05.V25.open_ar
    with EG06._variant():
        assert EG05.V25.open_ar is EG06._open_ar_intkey
    assert EG05.V25.open_ar is original
