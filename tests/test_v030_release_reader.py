from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_prefixgraph as pg
from experiments import entropygraph_v030_release_reader as reader


def _prefix_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    base = (b'{"id":1,"name":"alpha","values":[' + b"1234567890," * 200 + b"]}\n") * 40
    for index in range(5):
        body = base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1)
        (root / f"version-{index:02d}.json").write_bytes(body)


def _g04_archive(root: Path, archive: Path, work: Path) -> None:
    """Create a real G0-G4 framed archive even if the final size tournament would prefer v0.29.

    Footnote: reader tests need the new grammar itself, not a fallback artifact.  We therefore build the
    authoritative pre-fallback graph, apply the real audition functions, and serialize the G0-G4 frame directly.
    Compression admission remains covered independently by the release oracle.
    """
    graph = work / "prefallback.cmpct"
    g04.A5.build_graph(root, graph)
    source_format, _source, meta, records = g04.strict._read_source_records(graph)
    users = g04.O._record_member_lengths(meta, len(records))
    selected_records = []
    transforms = []
    for record_id, record in enumerate(records):
        chosen, transform, _stats = g04._audition_record(record_id, record, users[record_id])
        selected_records.append(chosen)
        transforms.append(transform)
    annotated = dict(meta)
    annotated["overlay_source_format"] = source_format
    g04._write_overlay(annotated, selected_records, transforms, archive)


def _corrupt_byte(path: Path, offset: int) -> Path:
    data = bytearray(path.read_bytes())
    data[offset] ^= 0x5A
    path.write_bytes(data)
    return path


def test_prefixgraph_streamed_verify_and_extract(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    stats = pg.build(source, archive)
    assert stats["prefix_records"] > 0

    verified = reader.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == pg.treehash(source)
    assert verified["reader"] == "v030-release-streaming-prefixgraph-v1"
    assert verified["max_member_read_amplification"] <= 8.0

    destination = tmp_path / "out"
    reader.extract(archive, destination)
    assert reader.treehash(destination) == reader.treehash(source)


def test_prefixgraph_primary_and_tail_recover_independently(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    original = tmp_path / "prefix.cmpct"
    pg.build(source, original)

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(original.read_bytes())
    _corrupt_byte(primary_bad, pg.HEADER.size)
    result = reader.strong_verify(primary_bad)
    assert result["ok"] is True
    assert result["tail_metadata_authenticated"] is True

    tail_bad = tmp_path / "tail-bad.cmpct"
    tail_bad.write_bytes(original.read_bytes())
    _corrupt_byte(tail_bad, tail_bad.stat().st_size - 1)
    result = reader.strong_verify(tail_bad)
    assert result["ok"] is True
    assert result["tail_metadata_authenticated"] is False

    both_bad = tmp_path / "both-bad.cmpct"
    both_bad.write_bytes(original.read_bytes())
    _corrupt_byte(both_bad, pg.HEADER.size)
    _corrupt_byte(both_bad, both_bad.stat().st_size - 1)
    assert reader.strong_verify(both_bad)["ok"] is False


def test_prefixgraph_extraction_publication_failure_restores_destination(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    pg.build(source, archive)

    destination = tmp_path / "destination"
    destination.mkdir()
    (destination / "sentinel.txt").write_text("old", encoding="utf-8")

    real_replace = reader.os.replace
    calls = {"count": 0}

    def fail_install(src, dst):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("injected publication failure")
        return real_replace(src, dst)

    monkeypatch.setattr(reader.os, "replace", fail_install)
    try:
        reader.extract(archive, destination)
    except OSError as exc:
        assert "injected publication failure" in str(exc)
    else:  # pragma: no cover - the monkeypatch must reach the publication edge.
        raise AssertionError("expected publication failure")

    assert (destination / "sentinel.txt").read_text(encoding="utf-8") == "old"
    assert not any("v030-stage" in path.name for path in tmp_path.iterdir())


def test_g04_streamed_verify_extract_and_recovery(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    rows = [f"{index:06d},region-{index % 4},metric-{index % 17:04d}\n" for index in range(12000)]
    (source / "events.csv").write_text("".join(rows), encoding="utf-8")
    (source / "events-copy.csv").write_text("".join(rows).replace("region-3", "region-7"), encoding="utf-8")

    archive = tmp_path / "g04.cmpct"
    _g04_archive(source, archive, tmp_path)
    assert archive.read_bytes()[:8] == g04.MAG

    verified = reader.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == g04.treehash(source)
    assert verified["reader"] == "v030-release-streaming-g04-v1"
    assert verified["max_member_read_amplification"] <= 8.0
    assert verified["record_cache_peak_bound_bytes"] == reader.MAX_RECORD_CACHE_BYTES
    assert verified["node_cache_peak_bound_bytes"] == reader.MAX_NODE_CACHE_BYTES

    destination = tmp_path / "g04-out"
    reader.extract(archive, destination)
    assert reader.treehash(destination) == reader.treehash(source)

    primary_bad = tmp_path / "g04-primary-bad.cmpct"
    primary_bad.write_bytes(archive.read_bytes())
    _corrupt_byte(primary_bad, g04.HDR.size)
    assert reader.strong_verify(primary_bad)["ok"] is True

    tail_bad = tmp_path / "g04-tail-bad.cmpct"
    tail_bad.write_bytes(archive.read_bytes())
    _corrupt_byte(tail_bad, tail_bad.stat().st_size - 1)
    result = reader.strong_verify(tail_bad)
    assert result["ok"] is True
    assert result["tail_metadata_authenticated"] is False


def test_extract_budget_fails_before_publication(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    pg.build(source, archive)
    destination = tmp_path / "out"
    destination.mkdir()
    (destination / "sentinel").write_bytes(b"old")

    try:
        reader.extract(archive, destination, max_output_bytes=1)
    except RuntimeError as exc:
        assert "output budget" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected output-budget failure")
    assert (destination / "sentinel").read_bytes() == b"old"
