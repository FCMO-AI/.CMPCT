from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_release_reader as reader
from experiments import entropygraph_v030_release_reader_policy as policy


def _archive(root: Path, archive: Path, work: Path) -> None:
    graph = work / "prefallback.cmpct"
    g04.A5.build_graph(root, graph)
    source_format, _source, meta, records = g04.strict._read_source_records(graph)
    users = g04.O._record_member_lengths(meta, len(records))
    selected = []
    transforms = []
    for record_id, record in enumerate(records):
        chosen, transform, _stats = g04._audition_record(record_id, record, users[record_id])
        selected.append(chosen)
        transforms.append(transform)
    annotated = dict(meta)
    annotated["overlay_source_format"] = source_format
    g04._write_overlay(annotated, selected, transforms, archive)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    rows = [f"{i:05d},region-{i % 4},metric-{i % 13:03d}\n" for i in range(1800)]
    body = "".join(rows)
    (source / "events.csv").write_text(body, encoding="utf-8")
    (source / "events-copy.csv").write_text(body.replace("region-3", "region-7"), encoding="utf-8")
    archive = tmp_path / "g04.cmpct"
    _archive(source, archive, tmp_path)
    assert archive.read_bytes()[:8] == g04.MAG
    return source, archive


def _flip(path: Path, offset: int) -> None:
    data = bytearray(path.read_bytes())
    data[offset] ^= 0x5A
    path.write_bytes(data)


def test_promoted_g04_healthy_open_decodes_identical_metadata_once(tmp_path: Path, monkeypatch) -> None:
    _source, archive = _fixture(tmp_path)
    calls = {"count": 0}
    real_decode = reader._decode_g04_meta

    def counted_decode(*args, **kwargs):
        calls["count"] += 1
        return real_decode(*args, **kwargs)

    monkeypatch.setattr(reader, "_decode_g04_meta", counted_decode)
    stream, _meta, _record_start, _offsets, _merkle, tail_ok = reader._g04_open(archive)
    stream.close()

    assert policy.PROMOTED_G04_IDENTICAL_METADATA_REUSE is True
    assert tail_ok is True
    assert calls["count"] == 1


def test_promoted_g04_metadata_reuse_keeps_primary_and_tail_recovery(tmp_path: Path) -> None:
    source, archive = _fixture(tmp_path)

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(archive.read_bytes())
    _flip(primary_bad, g04.HDR.size)
    result = policy.strong_verify(primary_bad)
    assert result["ok"] is True
    assert result["tree_sha256"] == reader.treehash(source)
    assert result["tail_metadata_authenticated"] is True

    tail_bad = tmp_path / "tail-bad.cmpct"
    tail_bad.write_bytes(archive.read_bytes())
    _flip(tail_bad, tail_bad.stat().st_size - 1)
    result = policy.strong_verify(tail_bad)
    assert result["ok"] is True
    assert result["tree_sha256"] == reader.treehash(source)
    assert result["tail_metadata_authenticated"] is False

    both_bad = tmp_path / "both-bad.cmpct"
    both_bad.write_bytes(archive.read_bytes())
    _flip(both_bad, g04.HDR.size)
    _flip(both_bad, both_bad.stat().st_size - 1)
    assert policy.strong_verify(both_bad)["ok"] is False
