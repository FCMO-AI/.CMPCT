from __future__ import annotations

import binascii
import io
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_gir_guarded as guarded


g = guarded.gir


def _valid_meta(kind: str = "direct", node_size: int = 1) -> tuple[dict, list[bytes], list[int], bytes]:
    logical = b"x" * node_size
    leaf = g.H(b"payload")
    if kind == "lane":
        node = ["lane", 0, g.G.LANE_WIDTHS[0], node_size, g.H(logical)]
    else:
        node = [kind, 0, node_size, g.H(logical)]
    leaves = [leaf]
    offsets = [0]
    meta = {
        "v": 1,
        "engine": "Geometry-IR-v1",
        "files": {"file.bin": [[0], node_size, g.H(logical)]},
        "nodes": [node],
        "record_rel_offsets": offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": "0" * 64,
        "max_chunk": g.MAX_CHUNK,
        "max_decode_unit": g.MAX_DECODE_UNIT,
        "max_decoder_memory": g.MAX_DECODER_MEMORY,
        "max_dependency_depth": 0,
        "max_read_amplification": 1.0,
        "geometry": {
            "lane_widths": list(g.G.LANE_WIDTHS),
            "max_delimiter_candidates": g.G.MAX_DELIMITER_CANDIDATES,
            "max_delimiter_segments": g.G.MAX_DELIMITER_SEGMENTS,
        },
        "hierarchical_geometry": dict(g.HG.RESOURCE_LIMITS),
    }
    return meta, leaves, offsets, g._merkle_root(leaves)


def test_bounded_unpack_rejects_duplicate_map_keys() -> None:
    packer = msgpack.Packer(use_bin_type=True)
    raw = b"".join(
        (packer.pack_map_header(2), packer.pack("v"), packer.pack(1), packer.pack("v"), packer.pack(1))
    )
    with pytest.raises(RuntimeError, match="duplicate map key"):
        guarded._bounded_unpack(raw)


def test_schema_accepts_hierarchical_node_but_rejects_path_traversal() -> None:
    meta, leaves, offsets, merkle = _valid_meta("hierarchical")
    guarded._validate_meta_schema(meta, leaves, offsets, 1, merkle)

    meta["files"] = {"../escape": [[0], 1, g.H(b"x")]}
    with pytest.raises(RuntimeError, match="unsafe GIR extraction path"):
        guarded._validate_meta_schema(meta, leaves, offsets, 1, merkle)


def test_schema_rejects_archive_wide_materialization_bomb() -> None:
    meta, leaves, offsets, merkle = _valid_meta("direct", g.MAX_CHUNK)
    repeats = guarded.MAX_TOTAL_MATERIALIZED_BYTES // g.MAX_CHUNK + 1
    meta["files"] = {
        "huge.bin": [[0] * repeats, repeats * g.MAX_CHUNK, g.H(b"placeholder")]
    }
    with pytest.raises(RuntimeError, match="materialization budget"):
        guarded._validate_meta_schema(meta, leaves, offsets, 1, merkle)


def test_schema_rejects_physical_record_aliasing() -> None:
    meta, leaves, _, _ = _valid_meta()
    meta["nodes"] = [
        ["direct", 0, 1, g.H(b"x")],
        ["hierarchical", 0, 1, g.H(b"x")],
    ]
    meta["files"] = {"file.bin": [[0, 1], 2, g.H(b"xx")]}
    leaves2 = leaves * 2
    offsets2 = [0, g.PH.size + 1]
    with pytest.raises(RuntimeError, match="one-to-one node/physical record mapping"):
        guarded._validate_meta_schema(meta, leaves2, offsets2, 2, g._merkle_root(leaves2))


def test_physical_table_rejects_gap_before_next_record() -> None:
    raw = b"x"
    ph = g.PH.pack(g.CODEC_RAW, 1, 1, binascii.crc32(raw) & 0xFFFFFFFF, g.H(raw))
    record_start = g.HDR.size
    first_end = g.PH.size + len(raw)
    # Two valid record bodies separated by one unowned byte.  The tail declaration itself is structurally
    # valid, so the guard must prove exact physical ownership rather than merely sorted offsets.
    body = ph + raw + b"!" + ph + raw
    footer = g.FTR.pack(g.TAIL, 0, 0, g.H(b""), g._merkle_root([]))
    stream = io.BytesIO((b"\0" * record_start) + body + footer)
    with pytest.raises(RuntimeError, match="not contiguous"):
        guarded._validate_physical_table(stream, record_start, [0, first_end + 1])


def test_valid_primary_survives_corrupted_redundant_footer(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    payload = (b"tenant=17,status=active,score=0.125\n" * 5000) + bytes(range(256)) * 40
    (source / "records.bin").write_bytes(payload)
    archive = tmp_path / "gir.cmpct"
    guarded._build_gir(source, archive)

    data = bytearray(archive.read_bytes())
    data[-g.FTR.size] ^= 0x01  # corrupt only the duplicate-tail footer magic
    archive.write_bytes(data)

    # Footnote: redundancy must remain two-way.  Hardening may ignore an unusable tail when the primary
    # metadata copy is authenticated; it must not accidentally turn the redundant footer into a single point
    # of failure for an otherwise complete archive.
    verified = guarded.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == guarded.treehash(source)


def test_valid_tail_still_recovers_corrupted_primary_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "records.bin").write_bytes((b"worker=07 route=/api/jobs latency=19\n" * 4000))
    archive = tmp_path / "gir.cmpct"
    guarded._build_gir(source, archive)

    data = bytearray(archive.read_bytes())
    _, metadata_bytes, _, _, _, _, _, _ = g.HDR.unpack(bytes(data[: g.HDR.size]))
    assert metadata_bytes > 8
    data[g.HDR.size + min(7, metadata_bytes - 1)] ^= 0x01
    archive.write_bytes(data)

    verified = guarded.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == guarded.treehash(source)


def test_guarded_reader_preserves_cmpnx14_writer_contract(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "opaque.bin").write_bytes((b"2026-08-17 level=INFO tenant=T0042 route=/v1/run\n" * 6000))
    archive = tmp_path / "gir.cmpct"
    stats = guarded._build_gir(source, archive)

    assert stats["node_kind_counts"]["hierarchical"] >= 0
    assert guarded.build is g.build
    verified = guarded.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == guarded.treehash(source)
