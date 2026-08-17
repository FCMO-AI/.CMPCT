from __future__ import annotations

import binascii
import io
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_geometry_guarded as guarded


g = guarded.geometry


def _valid_meta(node_size: int = 1) -> tuple[dict, list[bytes], list[int], bytes]:
    logical = b"x" * node_size
    leaf = g.H(b"payload")
    leaves = [leaf]
    offsets = [0]
    meta = {
        "v": 1,
        "engine": "Geometry-Compiler-v1",
        "files": {"file.bin": [[0], node_size, g.H(logical)]},
        "nodes": [["direct", 0, node_size, g.H(logical)]],
        "record_rel_offsets": offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": "0" * 64,
        "max_chunk": g.MAX_CHUNK,
        "max_decode_unit": g.MAX_DECODE_UNIT,
        "max_decoder_memory": g.MAX_DECODER_MEMORY,
        "max_dependency_depth": 0,
        "max_read_amplification": 1.0,
        "lane_widths": list(g.LANE_WIDTHS),
        "max_delimiter_candidates": g.MAX_DELIMITER_CANDIDATES,
        "max_delimiter_segments": g.MAX_DELIMITER_SEGMENTS,
        "max_delimiter_regularity": g.MAX_DELIMITER_REGULARITY,
    }
    return meta, leaves, offsets, g._merkle_root(leaves)


def test_bounded_unpack_rejects_duplicate_map_keys() -> None:
    packer = msgpack.Packer(use_bin_type=True)
    raw = b"".join((packer.pack_map_header(2), packer.pack("v"), packer.pack(1), packer.pack("v"), packer.pack(1)))
    with pytest.raises(RuntimeError, match="duplicate map key"):
        guarded._bounded_unpack(raw)


def test_schema_rejects_archive_wide_materialization_bomb() -> None:
    meta, leaves, offsets, merkle = _valid_meta(g.MAX_CHUNK)
    repeats = guarded.MAX_TOTAL_MATERIALIZED_BYTES // g.MAX_CHUNK + 1
    logical_size = repeats * g.MAX_CHUNK
    meta["files"] = {"huge.bin": [[0] * repeats, logical_size, g.H(b"placeholder")]}
    with pytest.raises(RuntimeError, match="materialization budget"):
        guarded._validate_meta_schema(meta, leaves, offsets, 1, merkle)


def test_schema_rejects_unsafe_path_before_materialization() -> None:
    meta, leaves, offsets, merkle = _valid_meta()
    meta["files"] = {"../escape": [[0], 1, g.H(b"x")]}
    with pytest.raises(RuntimeError, match="unsafe Geometry extraction path"):
        guarded._validate_meta_schema(meta, leaves, offsets, 1, merkle)


def test_schema_rejects_physical_record_aliasing() -> None:
    meta, leaves, offsets, merkle = _valid_meta()
    meta["nodes"] = [
        ["direct", 0, 1, g.H(b"x")],
        ["direct", 0, 1, g.H(b"x")],
    ]
    meta["files"] = {"file.bin": [[0, 1], 2, g.H(b"xx")]}
    meta["record_leaf_sha256"] = leaves * 2
    meta["record_rel_offsets"] = [0, g.PH.size + 1]
    leaves2 = leaves * 2
    merkle2 = g._merkle_root(leaves2)
    with pytest.raises(RuntimeError, match="one-to-one node/physical record mapping"):
        guarded._validate_meta_schema(meta, leaves2, [0, g.PH.size + 1], 2, merkle2)


def test_physical_table_rejects_overlap_or_gap() -> None:
    raw = b"x"
    header = g.PH.pack(g.CODEC_RAW, 1, 1, binascii.crc32(raw) & 0xFFFFFFFF, g.H(raw))
    record_start = g.HDR.size
    table = b"\x00" * record_start + header + raw + header + raw
    # Correct second offset is PH.size+1; PH.size points one byte into the first record and must fail before
    # any payload decompression. This single invariant rejects both overlap and non-canonical gap layouts.
    stream = io.BytesIO(table)
    with pytest.raises(RuntimeError, match="not contiguous"):
        guarded._validate_physical_table(stream, record_start, [0, g.PH.size])


def test_guarded_reader_accepts_writer_bytes_without_grammar_change(tmp_path: Path) -> None:
    source = tmp_path / "source"; source.mkdir()
    payload = (b"tenant=17,status=active,score=0.125\n" * 4000) + bytes(range(256)) * 80
    (source / "records.bin").write_bytes(payload)
    archive = tmp_path / "geometry.cmpct"
    g._build_geometry(source, archive)

    # Footnote: the hardening facade aliases the original writer.  Its only admissible effect is to reject
    # hostile reader shapes earlier; a writer-produced CMPNX13 artifact must still verify byte-for-byte.
    assert guarded.build is g.build
    verified = guarded.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == g.treehash(source)
