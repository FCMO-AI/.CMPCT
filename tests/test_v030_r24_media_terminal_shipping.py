from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_r24_media_terminal as MEDIA


def test_entropy_refinement_rejects_compressible_media_magic(tmp_path: Path) -> None:
    root = tmp_path / "compressible"
    root.mkdir()
    payload = b"\xff\xd8\xff" + b"\0" * (1024 * 1024 - 3)
    for index in range(8):
        (root / f"f{index}").write_bytes(payload)
    shape = MEDIA.analyze(root)
    assert shape["regular_files"] == 8
    assert shape["opaque_encoded_media_share"] == 1.0
    assert shape["sample_bytes"] >= MEDIA.MIN_SAMPLE_BYTES
    assert shape["sample_entropy_bits_per_byte"] < MEDIA.MIN_ENTROPY_BITS_PER_BYTE
    assert shape["eligible"] is False


def test_release_product_terminalizes_only_when_media_policy_admits(monkeypatch, tmp_path: Path) -> None:
    out = tmp_path / "out.cmpct"
    calls: list[str] = []

    monkeypatch.setattr(
        PRODUCT._LOGS_PROMOTED,
        "_build_logs_terminal_if_eligible",
        lambda root, target: None,
    )
    monkeypatch.setattr(
        PRODUCT,
        "_locality_bounded_r24_build",
        lambda root, target: calls.append("r24") or {"archive_bytes": 123, "format_revision": 24},
    )
    monkeypatch.setattr(
        PRODUCT._BASE_IMPL,
        "build",
        lambda root, target: calls.append("tournament") or {"archive_bytes": 456},
    )

    admitted = {
        "eligible": True,
        "regular_files": 8,
        "logical_bytes": 8 * 1024 * 1024,
        "opaque_encoded_media_share": 1.0,
        "sample_bytes": MEDIA.MIN_SAMPLE_BYTES,
        "sample_entropy_bits_per_byte": 7.99,
    }
    monkeypatch.setattr(PRODUCT._R24_MEDIA, "analyze", lambda root: admitted)
    result = PRODUCT.build(tmp_path, out)
    assert calls == ["r24"]
    assert result["terminal_r24"] is True
    assert result["terminal_r24_reason"] == "opaque-media-entropy-v1"
    assert result["speculative_r25_search_skipped"] is True
    assert result["terminal_r24_media_admission"] is admitted

    calls.clear()
    monkeypatch.setattr(PRODUCT._R24_MEDIA, "analyze", lambda root: {"eligible": False})
    result = PRODUCT.build(tmp_path, out)
    assert calls == ["tournament"]
    assert result == {"archive_bytes": 456}
