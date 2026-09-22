from __future__ import annotations

import gzip
import os
from pathlib import Path

import pytest
import zstandard as zstd

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS


def _tree(root: Path) -> None:
    root.mkdir(parents=True)
    for stem, payload in (("a.log", b"alpha\n" * 4096), ("b.log", b"beta\n" * 4096)):
        (root / stem).write_bytes(payload)
    (root / "a.log.zst").write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress((root / "a.log").read_bytes()))
    (root / "b.log.gz").write_bytes(gzip.compress((root / "b.log").read_bytes(), compresslevel=6, mtime=0))
    try:
        os.symlink("a.log", root / "a-link")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")


def test_symlink_target_is_authenticated_metadata_not_content_amplification(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _tree(source)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(source, archive)

    # The user-visible target is authenticated by the bounded filesystem manifest and remains readable.
    assert LOGS.read_member(archive, "a-link") == b"a.log"

    # Do not silently relabel those few metadata bytes as a graph-owned content member to manufacture <=8x.
    # The measured content-member API must continue to fail closed when the full manifest context cannot satisfy
    # the content amplification law for a metadata-only value.
    with pytest.raises(RuntimeError, match="selective-read locality violation"):
        LOGS.read_member_with_stats(archive, "a-link")


def test_regular_member_still_pays_manifest_plus_content_context(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _tree(source)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(source, archive)

    value, stats = LOGS.read_member_with_stats(archive, "a.log")
    assert value == (source / "a.log").read_bytes()
    assert stats["filesystem_manifest_decoded_context_bytes"] > 0
    assert stats["content_decoded_context_bytes"] > 0
    assert stats["decoded_context_bytes"] == (
        stats["filesystem_manifest_decoded_context_bytes"] + stats["content_decoded_context_bytes"]
    )
    assert stats["decoded_context_amplification"] <= LOGS.MAX_MEMBER_AMPLIFICATION
    assert stats["decoded_context_bytes"] <= LOGS.MAX_DECODE_UNIT
