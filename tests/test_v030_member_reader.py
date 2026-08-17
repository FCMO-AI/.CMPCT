from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_member_reader as member
from experiments import entropygraph_v030_prefixgraph as pg


def _prefix_fixture(root: Path) -> dict[str, bytes]:
    root.mkdir(parents=True)
    files = {}
    base = (b'{"id":1,"name":"alpha","values":[' + b"1234567890," * 160 + b"]}\n") * 25
    for index in range(5):
        rel = f"version-{index:02d}.json"
        body = base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1)
        (root / rel).write_bytes(body)
        files[rel] = body
    return files


def _g04_fixture(root: Path) -> dict[str, bytes]:
    root.mkdir(parents=True)
    rows = [f"{index:06d},region-{index % 4},metric-{index % 17:04d}\n" for index in range(4500)]
    a = "".join(rows).encode()
    b = a.replace(b"region-3", b"region-8")
    (root / "events-a.csv").write_bytes(a)
    (root / "events-b.csv").write_bytes(b)
    return {"events-a.csv": a, "events-b.csv": b}


def _build_raw_g04(source: Path, archive: Path, work: Path) -> None:
    graph = work / "prefallback-member.cmpct"
    g04.A5.build_graph(source, graph)
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


def test_prefixgraph_selective_member_roundtrip_and_stats(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    stats = pg.build(source, archive)
    assert stats["prefix_records"] > 0

    target = next(rel for rel in files if rel != files.keys().__iter__().__next__())
    raw, read_stats = member.read_member(archive, target, with_stats=True)
    assert raw == files[target]
    assert read_stats["representation"] == "prefixgraph"
    assert read_stats["logical_bytes"] == len(raw)
    assert read_stats["max_member_read_amplification"] <= 8.0


def test_g04_selective_member_roundtrip_without_full_extraction(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _g04_fixture(source)
    archive = tmp_path / "g04.cmpct"
    _build_raw_g04(source, archive, tmp_path)

    raw, read_stats = member.read_member(archive, "events-b.csv", with_stats=True)
    assert raw == files["events-b.csv"]
    assert read_stats["representation"] == "g04-overlay"
    assert read_stats["logical_bytes"] == len(raw)
    assert read_stats["physical_record_reads"] >= 1
    assert read_stats["record_cache_bound_bytes"] == 64 * 1024 * 1024
    assert read_stats["node_cache_bound_bytes"] == 32 * 1024 * 1024


def test_member_budget_and_missing_path_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    files = _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    pg.build(source, archive)
    target = sorted(files)[0]

    with pytest.raises(RuntimeError, match="output budget"):
        member.read_member(archive, target, max_output_bytes=1)
    with pytest.raises(KeyError):
        member.read_member(archive, "missing.bin")
    with pytest.raises(ValueError):
        member.read_member(archive, target, max_output_bytes=True)


def test_inherited_representation_is_explicit_not_full_extract_fallback(tmp_path: Path) -> None:
    archive = tmp_path / "inherited.cmpct"
    archive.write_bytes(b"NOTV030!" + b"payload")
    with pytest.raises(member.InheritedRepresentation, match="existing v0.29 reader"):
        member.read_member(archive, "a.bin")

# Footnote: the inherited-representation test is intentionally explicit. Selective read must never silently
# become whole-archive extraction just because the top-level tournament chose exact v0.29 fallback bytes.
