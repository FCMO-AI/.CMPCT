from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_geometry_streaming as streaming


g = streaming.geometry


def _source(root: Path) -> None:
    root.mkdir(parents=True)
    rows = b"\n".join(
        f"step={i:06d},tenant={i % 41:02d},loss={5/(1+i/3000):.7f},status=active".encode()
        for i in range(30_000)
    )
    (root / "training.bin").write_bytes(rows)
    # A second nontrivial file forces multi-file tree hashing without relying on a one-file special case.
    (root / "index.bin").write_bytes((bytes(range(256)) * 2400) + b"tail")


def test_streaming_verify_never_calls_legacy_whole_materializer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"; _source(source)
    archive = tmp_path / "geometry.cmpct"; g._build_geometry(source, archive)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("legacy whole-archive materializer was called")

    monkeypatch.setattr(g, "_materialize_files", forbidden)
    result = streaming.strong_verify(archive)
    assert result["ok"] is True
    assert result["tree_sha256"] == g.treehash(source)
    assert result["reader"] == "Geometry-streaming-v1"
    assert 0 < result["max_logical_node_bytes"] <= g.MAX_CHUNK
    assert result["max_physical_record_bytes"] <= g.MAX_DECODE_UNIT


def test_streaming_extract_round_trips_without_materializer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"; _source(source)
    archive = tmp_path / "geometry.cmpct"; g._build_geometry(source, archive)

    monkeypatch.setattr(
        g,
        "_materialize_files",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy materializer called")),
    )
    restored = tmp_path / "restored"
    streaming.extract(archive, restored)
    assert g.treehash(restored) == g.treehash(source)


def test_failed_streaming_extract_preserves_existing_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"; _source(source)
    archive = tmp_path / "geometry.cmpct"; g._build_geometry(source, archive)

    # Corrupt the first physical payload but leave metadata/table declarations intact so failure happens
    # during streaming authentication, after the staging directory exists but before destination publication.
    data = bytearray(archive.read_bytes())
    _, mcs, _, _, _, _, _, _ = g.HDR.unpack_from(data, 0)
    first_payload = g.HDR.size + mcs + g.PH.size
    data[first_payload] ^= 0x01
    archive.write_bytes(data)

    destination = tmp_path / "destination"; destination.mkdir()
    sentinel = destination / "keep.txt"; sentinel.write_text("old verified output", encoding="utf-8")
    with pytest.raises(RuntimeError):
        streaming.extract(archive, destination)
    # Footnote: extraction is a verify-then-publish transaction. Corruption must leave previously verified
    # user data untouched rather than replacing it with a partially reconstructed directory.
    assert sentinel.read_text(encoding="utf-8") == "old verified output"
    assert sorted(path.name for path in destination.iterdir()) == ["keep.txt"]
