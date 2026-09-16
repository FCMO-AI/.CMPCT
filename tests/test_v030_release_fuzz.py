from __future__ import annotations

import copy
from pathlib import Path
import random

import pytest

from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_prefixgraph as pg
from experiments import entropygraph_v030_release_reader as reader
from experiments import entropygraph_v030_release_reader_policy as policy


SEED = 0xC0A030


def _prefix_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    base = (b'{"id":1,"name":"alpha","values":[' + b"1234567890," * 200 + b"]}\n") * 30
    for index in range(6):
        body = base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1)
        (root / f"version-{index:02d}.json").write_bytes(body)


def _g04_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    rows = [f"{index:06d},region-{index % 4},metric-{index % 17:04d}\n" for index in range(5000)]
    body = "".join(rows).encode()
    (root / "events-a.csv").write_bytes(body)
    (root / "events-b.csv").write_bytes(body.replace(b"region-3", b"region-8"))


def _build_raw_g04(source: Path, archive: Path, work: Path) -> None:
    graph = work / "prefallback-fuzz.cmpct"
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


def _flip_both_metadata_copies_pg(path: Path, rng: random.Random) -> None:
    data = bytearray(path.read_bytes())
    _magic, mcs, _mus, _sha = pg.HEADER.unpack(data[: pg.HEADER.size])
    assert mcs > 4
    index = rng.randrange(1, int(mcs) - 1)
    primary = pg.HEADER.size + index
    duplicate_start = len(data) - pg.FOOTER.size - int(mcs)
    data[primary] ^= 0x5A
    data[duplicate_start + index] ^= 0xA5
    path.write_bytes(data)


def _flip_both_metadata_copies_g04(path: Path, rng: random.Random) -> None:
    data = bytearray(path.read_bytes())
    header = g04.HDR.unpack(data[: g04.HDR.size])
    mcs = int(header[1])
    assert mcs > 4
    index = rng.randrange(1, mcs - 1)
    primary = g04.HDR.size + index
    duplicate_start = len(data) - g04.FTR.size - mcs
    data[primary] ^= 0x33
    data[duplicate_start + index] ^= 0xCC
    path.write_bytes(data)


def _flip_first_payload_pg(path: Path) -> None:
    data = bytearray(path.read_bytes())
    _magic, mcs, _mus, _sha = pg.HEADER.unpack(data[: pg.HEADER.size])
    meta, _payloads = pg._read(path)
    csize = int(meta["records"][0][3])
    assert csize > 0
    offset = pg.HEADER.size + int(mcs) + min(3, csize - 1)
    data[offset] ^= 0x7F
    path.write_bytes(data)


def _flip_first_payload_g04(path: Path) -> None:
    data = bytearray(path.read_bytes())
    _magic, mcs, _mus, count, _decode, _memory, _sha, _merkle = g04.HDR.unpack(data[: g04.HDR.size])
    assert count > 0
    physical_header = g04.HDR.size + int(mcs)
    _codec, _usize, csize, _crc, _logical = g04.PH.unpack(
        data[physical_header : physical_header + g04.PH.size]
    )
    assert csize > 0
    offset = physical_header + g04.PH.size + min(3, int(csize) - 1)
    data[offset] ^= 0x7F
    path.write_bytes(data)


def test_prefixgraph_dual_metadata_corruption_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    pg.build(source, archive)
    rng = random.Random(SEED)
    _flip_both_metadata_copies_pg(archive, rng)
    result = policy.strong_verify(archive)
    assert result["ok"] is False


def test_g04_dual_metadata_corruption_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _g04_fixture(source)
    archive = tmp_path / "g04.cmpct"
    _build_raw_g04(source, archive, tmp_path)
    rng = random.Random(SEED)
    _flip_both_metadata_copies_g04(archive, rng)
    result = policy.strong_verify(archive)
    assert result["ok"] is False


@pytest.mark.parametrize("kind", ["prefixgraph", "g04"])
def test_authenticated_payload_mutation_is_never_silently_accepted(tmp_path: Path, kind: str) -> None:
    source = tmp_path / kind
    archive = tmp_path / f"{kind}.cmpct"
    if kind == "prefixgraph":
        _prefix_fixture(source)
        pg.build(source, archive)
        _flip_first_payload_pg(archive)
    else:
        _g04_fixture(source)
        _build_raw_g04(source, archive, tmp_path)
        _flip_first_payload_g04(archive)
    result = policy.strong_verify(archive)
    assert result["ok"] is False


def test_prefixgraph_policy_rejects_descriptor_type_and_path_mutations(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "prefix.cmpct"
    pg.build(source, archive)
    stream, meta, _payload_start, _offsets, _tail = reader._pg_open(archive)
    stream.close()

    mutations = []
    bad = copy.deepcopy(meta)
    bad["files"][0] = "../escape.bin"
    mutations.append(bad)
    bad = copy.deepcopy(meta)
    direct = next(row for row in bad["records"] if row[0] == "direct")
    direct[1] = "-1"
    mutations.append(bad)
    bad = copy.deepcopy(meta)
    bad["max_dependency_depth"] = True
    mutations.append(bad)
    bad = copy.deepcopy(meta)
    bad["files"] = list(reversed(bad["files"]))
    mutations.append(bad)

    for mutated in mutations:
        with pytest.raises(RuntimeError):
            policy._strict_pg_validate(mutated)


def test_g04_policy_rejects_transform_path_and_graph_mutations(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _g04_fixture(source)
    archive = tmp_path / "g04.cmpct"
    _build_raw_g04(source, archive, tmp_path)
    stream, meta, _record_start, _offsets, _merkle, _tail = reader._g04_open(archive)
    stream.close()

    mutations = []
    bad = copy.deepcopy(meta)
    first_file = next(iter(bad["files"]))
    bad["files"]["../escape.bin"] = bad["files"].pop(first_file)
    mutations.append(bad)
    if bad := copy.deepcopy(meta):
        if bad["physical_geometry"]:
            bad["physical_geometry"][0] = ["unknown-transform", 1]
            mutations.append(bad)
    bad = copy.deepcopy(meta)
    bad["max_geometry_member_read_amplification"] = float("nan")
    mutations.append(bad)
    bad = copy.deepcopy(meta)
    bad["max_geometry_member_read_amplification"] = True
    mutations.append(bad)

    for mutated in mutations:
        with pytest.raises(RuntimeError):
            policy._strict_g04_validate(mutated, len(mutated["record_leaf_sha256"]))

# Footnote: this is deterministic mutation coverage, not a claim of exhaustive fuzzing. The release workflow
# should additionally run repeated byte-level mutations against committed golden vectors once those vectors are
# frozen, so parser safety is independent of the current builders.
