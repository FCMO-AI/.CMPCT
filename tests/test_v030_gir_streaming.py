from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_gir_streaming as streaming


g = streaming.gir


def _structured_rows(count: int) -> bytes:
    rows = []
    for index in range(count):
        rows.append(
            f"2026-08-17T12:{index % 60:02d}:00Z level=INFO worker={index % 32:02d} "
            f"tenant=T{index % 380:04d} route=/api/jobs latency={8 + index % 820} request={index:012x}"
        )
    return ("\n".join(rows) + "\n").encode()


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "structured.log").write_bytes(_structured_rows(8_000))
    (source / "opaque.bin").write_bytes(bytes((index * 73 + 19) & 255 for index in range(180_000)))
    archive = tmp_path / "gir.cmpct"
    stats = streaming._build_gir(source, archive)
    assert stats["node_kind_counts"]["hierarchical"] > 0
    return source, archive


def test_streaming_verify_does_not_call_legacy_whole_materializer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, archive = _fixture(tmp_path)

    def explode(*_args, **_kwargs):
        raise AssertionError("legacy whole-archive materializer was invoked")

    monkeypatch.setattr(g, "_materialize_files", explode)
    result = streaming.strong_verify(archive)
    assert result["ok"] is True
    assert result["tree_sha256"] == streaming.treehash(source)
    assert result["reader"] == "Geometry-IR-streaming-v1"
    assert result["max_logical_node_bytes"] <= g.MAX_CHUNK
    assert result["max_physical_record_bytes"] <= g.MAX_DECODE_UNIT
    assert result["physical_record_reads"] > 0


def test_streaming_extract_round_trips_hierarchical_nodes(tmp_path: Path) -> None:
    source, archive = _fixture(tmp_path)
    restored = tmp_path / "restored"
    streaming.extract(archive, restored)

    assert streaming.treehash(restored) == streaming.treehash(source)
    assert (restored / "structured.log").read_bytes() == (source / "structured.log").read_bytes()
    assert (restored / "opaque.bin").read_bytes() == (source / "opaque.bin").read_bytes()


def test_corrupt_payload_never_replaces_existing_destination(tmp_path: Path) -> None:
    _, archive = _fixture(tmp_path)
    stream, _, record_start, offsets = g._open(archive)
    stream.close()
    assert offsets

    data = bytearray(archive.read_bytes())
    payload_at = record_start + offsets[0] + g.PH.size
    assert payload_at < len(data) - g.FTR.size
    data[payload_at] ^= 0x01
    archive.write_bytes(data)

    destination = tmp_path / "destination"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("old verified state", encoding="utf-8")

    with pytest.raises(RuntimeError):
        streaming.extract(archive, destination)

    # Footnote: verification occurs entirely in a sibling staging directory.  Corruption discovered at any
    # payload/node/file/tree layer must leave the previously published destination untouched.
    assert sentinel.read_text(encoding="utf-8") == "old verified state"
    assert list(destination.iterdir()) == [sentinel]


def test_streaming_strong_verify_reports_corruption_without_raising(tmp_path: Path) -> None:
    _, archive = _fixture(tmp_path)
    stream, _, record_start, offsets = g._open(archive)
    stream.close()
    data = bytearray(archive.read_bytes())
    data[record_start + offsets[-1] + g.PH.size] ^= 0x01
    archive.write_bytes(data)

    result = streaming.strong_verify(archive)
    assert result["ok"] is False
    assert result["reader"] == "Geometry-IR-streaming-v1"
    assert "authentication" in result["error"] or "integrity" in result["error"]
