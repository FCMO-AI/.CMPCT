from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_gir_safe as gir


def _structured_rows(count: int) -> bytes:
    rows = []
    for index in range(count):
        rows.append(
            f"2026-08-17T12:{index % 60:02d}:00Z level=INFO worker={index % 32:02d} "
            f"tenant=T{index % 380:04d} route=/api/jobs latency={8 + index % 820} request={index:012x}"
        )
    return ("\n".join(rows) + "\n").encode()


def _minimal_meta() -> dict:
    return {
        "v": 1,
        "engine": "Geometry-IR-v1",
        "files": {},
        "nodes": [],
        "record_rel_offsets": [],
        "record_leaf_sha256": [],
        "tree_sha256": "0" * 64,
        "max_chunk": gir.MAX_CHUNK,
        "max_decode_unit": gir.MAX_DECODE_UNIT,
        "max_decoder_memory": gir.MAX_DECODER_MEMORY,
        "max_dependency_depth": 0,
        "max_read_amplification": 1.0,
        "geometry": {
            "lane_widths": list(gir.G.LANE_WIDTHS),
            "max_delimiter_candidates": gir.G.MAX_DELIMITER_CANDIDATES,
            "max_delimiter_segments": gir.G.MAX_DELIMITER_SEGMENTS,
        },
        "hierarchical_geometry": dict(gir.HG.RESOURCE_LIMITS),
    }


def _decode_meta_for_test(meta: dict):
    raw = msgpack.packb(meta, use_bin_type=True)
    comp = gir.zc(raw, 12)
    return gir._decode_meta(comp, len(raw), gir.H(raw), gir.gir._merkle_root([]), 0)


def test_gir_complete_archive_round_trips_and_selects_hierarchy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "opaque.bin").write_bytes(_structured_rows(7_000))
    # Deterministic hostile bytes stop a structured-only fixture from making the archive unrealistically easy.
    (source / "noise.bin").write_bytes(bytes((index * 73 + 19) & 255 for index in range(120_000)))

    archive = tmp_path / "research.cmpct"
    stats = gir._build_gir(source, archive)
    assert stats["node_kind_counts"]["hierarchical"] > 0
    assert stats["hierarchical_prefix_nodes"] > 0
    assert stats["transform_payload_saving_bytes"] > 0
    assert stats["max_dependency_depth"] == 0
    assert stats["max_read_amplification"] == 1.0

    verified = gir.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == gir.treehash(source)

    restored = tmp_path / "restored"
    gir.extract(archive, restored)
    assert gir.treehash(restored) == gir.treehash(source)
    assert (restored / "opaque.bin").read_bytes() == (source / "opaque.bin").read_bytes()
    assert (restored / "noise.bin").read_bytes() == (source / "noise.bin").read_bytes()


def test_gir_tail_metadata_recovers_corrupted_primary_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "records.dat").write_bytes(_structured_rows(4_000))
    archive = tmp_path / "research.cmpct"
    gir._build_gir(source, archive)

    data = bytearray(archive.read_bytes())
    header = bytes(data[: gir.HDR.size])
    _, metadata_bytes, _, _, _, _, _, _ = gir.HDR.unpack(header)
    assert metadata_bytes > 8
    # Footnote: changing one compressed primary-metadata byte preserves its declared length and record start.
    # The primary authentication must fail, while the duplicate authenticated tail must still recover the tree.
    flip_at = gir.HDR.size + min(7, metadata_bytes - 1)
    data[flip_at] ^= 0x01
    archive.write_bytes(data)

    verified = gir.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == gir.treehash(source)


def test_gir_meta_rejects_hierarchical_resource_escalation() -> None:
    meta = _minimal_meta()
    meta["hierarchical_geometry"]["max_cell_scans"] = gir.HG.RESOURCE_LIMITS["max_cell_scans"] + 1
    with pytest.raises(RuntimeError, match="hierarchical resource budget"):
        _decode_meta_for_test(meta)


def test_gir_meta_rejects_compressor_identity_drift() -> None:
    meta = _minimal_meta()
    meta["hierarchical_geometry"]["exact_level"] = gir.HG.RESOURCE_LIMITS["exact_level"] - 1
    with pytest.raises(RuntimeError, match="compressor identity mismatch"):
        _decode_meta_for_test(meta)


def test_gir_safe_entrypoint_installs_flat_geometry_cell_guard() -> None:
    assert hasattr(gir.G, "MAX_DELIMITER_CELL_SCANS")
    assert gir.G.MAX_DELIMITER_CELL_SCANS == 8 * gir.MAX_CHUNK


def test_gir_path_policy_rejects_traversal() -> None:
    for unsafe in ("../escape", "/absolute", "a/../escape", "a\\escape", "", "nul\x00name"):
        with pytest.raises(RuntimeError):
            gir._safe_relpath(unsafe)
