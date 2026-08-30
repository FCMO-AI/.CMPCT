from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as PRODUCT


def _write(path: Path, payload: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_promoted_logs_prefilter_short_circuits_after_two_proven_pairs(tmp_path: Path) -> None:
    root = tmp_path / "logs"
    _write(root / "a.log", b"alpha")
    _write(root / "a.log.gz", b"gzip")
    _write(root / "b.log", b"beta")
    _write(root / "b.log.zst", b"zstd")
    for index in range(200):
        _write(root / "bulk" / f"f-{index:04d}.bin", bytes((index & 255,)))

    result = PRODUCT.logs_source_prefilter(root)

    assert PRODUCT.PROMOTED_LOGS_STREAMING_PREFILTER is True
    # The public release facade owns the promoted streaming prefilter.  The candidate module intentionally keeps
    # its own implementation so importing the facade cannot mutate research/candidate module globals and make
    # full-suite behavior depend on import order.
    assert PRODUCT.logs_source_prefilter is PRODUCT._logs_streaming_source_prefilter
    assert PRODUCT._LOGS_PROMOTED.logs_source_prefilter is not PRODUCT._logs_streaming_source_prefilter
    assert PRODUCT._LOGS_PROMOTED.logs_source_prefilter.__module__ == PRODUCT._LOGS_PROMOTED.__name__
    assert result["eligible"] is True
    assert result["sidecar_pairs"] >= PRODUCT._LOGS_PROMOTED.MIN_SIDECAR_PAIRS
    assert result["short_circuited"] is True
    assert result["scanned_regular_files"] == 4
    assert result["prefilter"] == "streaming-sidecar-pairs-v1"


def test_promoted_logs_prefilter_preserves_negative_semantics(tmp_path: Path) -> None:
    root = tmp_path / "single-pair"
    _write(root / "only.log", b"plain")
    _write(root / "only.log.gz", b"sidecar")
    _write(root / "orphan.zst", b"not-a-pair")
    for index in range(32):
        _write(root / "bulk" / f"f-{index:03d}.bin")

    result = PRODUCT.logs_source_prefilter(root)

    assert result["eligible"] is False
    assert result["sidecar_pairs"] == 1
    assert result["short_circuited"] is False
    assert result["scanned_regular_files"] == 35
