from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _engine():
    path = ROOT / "experiments" / "entropygraph_v028_strict.py"
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v028_strict_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"; source.mkdir()
    rng = random.Random(0x51A1C7)
    for i in range(80):
        payload = (f"record={i:04d}\n".encode() * 64) + bytes(rng.getrandbits(8) for _ in range(4096))
        (source / f"item-{i:04d}.bin").write_bytes(payload)
    return source


def test_tiny_population_falls_back_to_independent_records_when_packs_exceed_budget():
    engine = _engine()
    # Thousands of tiny roots make even a 64 KiB pack expensive for a one-file selective read. This is
    # the workload that falsified the first selector's "some pack will be <=8x" assumption.
    nodes = [(f"tiny={i:05d}|".encode() * 3) for i in range(3000)]
    sketches = [engine.BASE.similarity_sketch(node) for node in nodes]
    chosen, trials = engine.strict_choose_pack_plan(nodes, sketches, list(range(len(nodes))))
    cost, amp, limit, groups = chosen
    assert amp <= engine.READ_AMPLIFICATION_BUDGET
    assert limit == 0
    assert len(groups) == len(nodes)
    assert any(row["limit"] == 65536 and not row["feasible"] for row in trials)


def test_strict_graph_never_reports_pack_amplification_above_budget(tmp_path: Path):
    engine = _engine()
    source = _source(tmp_path)
    archive = tmp_path / "strict.cmpct"
    stats = engine._build_graph(source, archive)
    assert stats["strict_locality_policy"] is True
    assert stats["pack_read_amplification"] <= engine.READ_AMPLIFICATION_BUDGET
    assert engine.strong_verify(archive)["ok"] is True


def test_oversized_primary_metadata_declaration_uses_bounded_tail_recovery(tmp_path: Path):
    engine = _engine(); source = _source(tmp_path); archive = tmp_path / "recover.cmpct"
    engine._build_graph(source, archive)
    data = bytearray(archive.read_bytes())
    magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = engine.HDR.unpack(data[:engine.HDR.size])
    # Footnote: an attacker can change the unauthenticated primary size fields. The strict reader must
    # refuse to allocate from the absurd value and recover through the separately authenticated tail.
    data[:engine.HDR.size] = engine.HDR.pack(
        magic, mcs, engine.MAX_METADATA + 1, count, max_decode, max_memory, meta_sha, merkle
    )
    archive.write_bytes(data)
    assert engine.strong_verify(archive)["ok"] is True


def test_header_magic_damage_still_routes_to_authenticated_tail_recovery(tmp_path: Path):
    engine = _engine(); source = _source(tmp_path); archive = tmp_path / "magic-damaged.cmpct"
    engine._build_graph(source, archive)
    data = bytearray(archive.read_bytes())
    data[:8] = b"BROKEN!!"
    archive.write_bytes(data)
    # Footnote: the footer magic is only a dispatcher hint. The subsequent strict tail path still
    # authenticates metadata, the physical Merkle leaves and the final logical tree before success.
    verified = engine.strong_verify(archive)
    assert verified["ok"] is True
    restored = tmp_path / "restored"
    engine.extract(archive, restored)
    assert engine.treehash(restored) == engine.treehash(source)


def test_oversized_physical_stored_size_is_rejected_before_payload_read(tmp_path: Path):
    engine = _engine(); source = _source(tmp_path); archive = tmp_path / "oversized-record.cmpct"
    engine._build_graph(source, archive)
    stream, meta, record_start, offsets, _ = engine.strict_open_graph(archive); stream.close(); assert offsets
    data = bytearray(archive.read_bytes())
    start = record_start + offsets[0]
    codec, usize, csize, crc, logical_sha = engine.PH.unpack(data[start:start + engine.PH.size])
    data[start:start + engine.PH.size] = engine.PH.pack(
        codec, usize, engine.MAX_DECODER_MEMORY + 1, crc, logical_sha
    )
    archive.write_bytes(data)
    with pytest.raises(RuntimeError, match="stored physical record exceeds decoder-memory ceiling"):
        engine.strong_verify(archive)


def test_non_monotonic_record_offsets_fail_closed(tmp_path: Path):
    engine = _engine(); source = _source(tmp_path); archive = tmp_path / "offsets.cmpct"
    engine._build_graph(source, archive)
    stream, meta, record_start, offsets, merkle = engine.strict_open_graph(archive); stream.close()
    if len(offsets) < 2:
        pytest.skip("fixture unexpectedly produced fewer than two records")
    # This property is authenticated inside metadata, so exercising the helper directly is the clean
    # parser-unit test: duplicate offsets are not a legal aliasing mechanism in CMPNX8.
    meta["record_rel_offsets"][1] = meta["record_rel_offsets"][0]
    import msgpack
    raw = msgpack.packb(meta, use_bin_type=True)
    comp = engine.zc(raw, 12)
    with pytest.raises(RuntimeError, match="strictly increasing"):
        engine._decode_meta(comp, len(raw), engine.H(raw), merkle)
