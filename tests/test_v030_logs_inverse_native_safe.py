from __future__ import annotations

import gzip
import lzma
from pathlib import Path

import zstandard as zstd

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS


def _regular_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_canonical_logs_writer_never_emits_xz_only_inverse_edge(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    plain = (b"2026-08-22T02:30:00Z INFO portable=xz-fallback value=41\n" * 3072)
    (source / "only.log").write_bytes(plain)
    (source / "only.log.xz").write_bytes(lzma.compress(plain, preset=6))

    archive = tmp_path / "candidate.cmpct"
    stats = LOGS.build(source, archive)
    assert stats["native_inverse_codec_safe"] is True
    assert stats["native_supported_inverse_codecs"] == ["gzip", "zstd"]
    assert stats["inverse_edge_codecs"] == []
    assert stats["edge_detection"]["inverse_edges"] == 0

    verified = LOGS.strong_verify(archive)
    assert verified["ok"] is True
    restored = tmp_path / "restored"
    LOGS.extract(archive, restored)
    assert _regular_tree(restored) == _regular_tree(source)


def test_canonical_logs_writer_retains_native_supported_gzip_and_zstd_edges(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    gzip_plain = (b"2026-08-22T02:31:00Z WARN portable=gzip value=17\n" * 3072)
    zstd_plain = (b"2026-08-22T02:32:00Z INFO portable=zstd value=42\n" * 4096)
    (source / "gzip.log").write_bytes(gzip_plain)
    (source / "gzip.log.gz").write_bytes(gzip.compress(gzip_plain, compresslevel=6, mtime=0))
    (source / "zstd.log").write_bytes(zstd_plain)
    (source / "zstd.log.zst").write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress(zstd_plain))

    archive = tmp_path / "candidate.cmpct"
    stats = LOGS.build(source, archive)
    assert stats["native_inverse_codec_safe"] is True
    assert set(stats["inverse_edge_codecs"]) == {"gzip", "zstd"}
    assert set(stats["edge_detection"]["inverse_edge_sources"]) == {"gzip.log.gz", "zstd.log.zst"}

    verified = LOGS.strong_verify(archive)
    assert verified["ok"] is True
    restored = tmp_path / "restored"
    LOGS.extract(archive, restored)
    assert _regular_tree(restored) == _regular_tree(source)
