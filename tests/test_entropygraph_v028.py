from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _engine():
    path = ROOT / "experiments" / "entropygraph_v028.py"
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v028_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    # A deterministic high-entropy base plus sparse edits makes delta profitability causal and obvious:
    # each direct Zstd object remains large while a COPY/LITERAL edge can encode only the edits. The
    # previous repetitive-text fixture compressed so well independently that correctly rejecting the
    # delta was sometimes the optimal policy.
    rng = random.Random(0xC028D17A)
    base = bytes(rng.getrandbits(8) for _ in range(220_000))
    for version in range(6):
        data = bytearray(base)
        at = 17_000 + version * 193
        data[at:at] = (f"version={version};".encode() * 19)
        for patch in range(8):
            pos = 43_000 + patch * 19_871 + version
            data[pos:pos + 24] = bytes([(31 + version + patch) & 0xFF]) * 24
        (source / f"snapshot-{version:02d}.bin").write_bytes(data)
    (source / "unique.bin").write_bytes(bytes(rng.getrandbits(8) for _ in range(140_000)))
    return source


def test_graph_is_deterministic_and_byte_exact(tmp_path: Path):
    engine = _engine()
    source = _source(tmp_path)
    first = tmp_path / "a.cmpct"
    second = tmp_path / "b.cmpct"
    stats_a = engine._build_graph(source, first)
    stats_b = engine._build_graph(source, second)
    assert first.read_bytes() == second.read_bytes()
    # Footnote: this fixture is deliberately constructed to make a delta materially cheaper. The
    # assertion proves the graph path is exercised without demanding delta use on arbitrary inputs.
    assert stats_a["delta_nodes"] > 0
    assert stats_a["max_decode_unit"] == engine.MAX_DECODE_UNIT
    assert stats_a["max_decoder_memory"] == engine.MAX_DECODER_MEMORY
    assert stats_a["adaptive_pack_limit"] <= engine.MAX_PACK
    verified=engine.strong_verify(first)
    assert verified["ok"] is True
    assert verified["max_decode_unit"]==engine.MAX_DECODE_UNIT
    assert verified["max_decoder_memory"]==engine.MAX_DECODER_MEMORY
    restored = tmp_path / "restored"
    engine.extract(first, restored)
    assert engine.treehash(restored) == engine.treehash(source)
    assert stats_a["graph_bytes"] == stats_b["graph_bytes"]


def test_primary_metadata_corruption_recovers_from_authenticated_tail(tmp_path: Path):
    engine = _engine()
    source = _source(tmp_path)
    archive = tmp_path / "recover.cmpct"
    engine._build_graph(source, archive)
    payload = bytearray(archive.read_bytes())
    header = engine.HDR.unpack(payload[:engine.HDR.size])
    primary_meta_bytes = header[1]
    assert primary_meta_bytes > 8
    # Footnote: corrupt only the primary compressed metadata. The duplicate tail copy and physical
    # records remain untouched, so successful strong verification proves recovery is operational.
    payload[engine.HDR.size + primary_meta_bytes // 2] ^= 0x5A
    archive.write_bytes(payload)
    verified = engine.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == engine.treehash(source)


def test_physical_merkle_leaf_corruption_is_rejected(tmp_path: Path):
    engine = _engine()
    source = _source(tmp_path)
    archive = tmp_path / "corrupt.cmpct"
    engine._build_graph(source, archive)
    stream, meta, record_start, offsets, _ = engine._open_graph(archive)
    stream.close()
    assert offsets
    first_header = record_start + offsets[0]
    payload = bytearray(archive.read_bytes())
    codec, usize, csize, crc, logical_sha = engine.PH.unpack(
        payload[first_header:first_header + engine.PH.size]
    )
    assert csize > 0
    payload[first_header + engine.PH.size + csize // 2] ^= 0x01
    archive.write_bytes(payload)
    # Metadata remains authentic, but the touched physical payload no longer matches its Merkle leaf.
    with pytest.raises(RuntimeError, match="Merkle leaf|physical"):
        engine.strong_verify(archive)


def test_tail_damage_does_not_mask_primary_success(tmp_path: Path):
    engine = _engine()
    source = _source(tmp_path)
    archive = tmp_path / "tail-damaged.cmpct"
    engine._build_graph(source, archive)
    payload = bytearray(archive.read_bytes())
    payload[-engine.FTR.size] ^= 0x7F
    archive.write_bytes(payload)
    # A valid primary copy is authoritative; a damaged redundant tail must not poison normal reads.
    assert engine.strong_verify(archive)["ok"] is True


def test_authenticated_decoder_memory_ceiling_is_policy_checked(tmp_path: Path):
    engine=_engine();source=_source(tmp_path);archive=tmp_path/'too-much-memory.cmpct'
    supported=engine.MAX_DECODER_MEMORY
    try:
        # Build a self-consistent research artifact whose authenticated metadata asks for more memory
        # than this reader's policy. Resetting the implementation ceiling afterwards proves both the
        # primary and recovery metadata paths reject it rather than trusting an unauthenticated header.
        engine.MAX_DECODER_MEMORY=supported*2
        engine._build_graph(source,archive)
    finally:
        engine.MAX_DECODER_MEMORY=supported
    with pytest.raises(RuntimeError,match="metadata copy|memory"):
        engine.strong_verify(archive)
