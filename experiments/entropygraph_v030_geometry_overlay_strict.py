"""Strict Geometry-overlay evidence facade: support both accepted v0.29 physical graph embodiments.

Attempt-5 is a portfolio compiler.  When residual packing wins, the accepted graph is ``CMPNX11``; when it
does not, attempt-5 deliberately preserves the Placement Compiler's ``CMPNX10`` archive byte-for-byte.
The first overlay oracle only recognized CMPNX11 and would therefore confuse "residual packing did not win"
with "there is no accepted v0.29 graph to overlay".

This facade fixes only that eligibility blind spot.  The Geometry transform/audition logic remains in
``entropygraph_v030_geometry_overlay``.  Both source grammars share the same authenticated physical-record
shape and logical descriptor families; verification reconstructs a view using the *same source grammar* that
was actually selected by v0.29, then delegates logical reconstruction to that authoritative reader.

Footnote: older inherited v0.28/v0.25 fallback representations remain out of scope and are copied exactly.
Adding an overlay to them would be a third mechanism and must not be smuggled into this causal experiment.
"""
from __future__ import annotations

import binascii
from pathlib import Path
import shutil
import tempfile
import time

import msgpack

from experiments import entropygraph_v030_geometry_overlay as O

A5 = O.A5
A4 = A5.A4
BASE = O.BASE
H = O.H
PH = O.PH


def _source_for_magic(magic: bytes):
    if magic == A5.MAG:
        return "residual-pack-v5", A5
    if magic == A4.MAG:
        return "placement-v4", A4
    return None


def _read_source_records(path: Path) -> tuple[str, object, dict, list[tuple[int, int, bytes, int, bytes]]]:
    with path.open("rb") as probe:
        magic = probe.read(8)
    selected = _source_for_magic(magic)
    if selected is None:
        raise RuntimeError("accepted v0.29 selected no overlay-compatible graph embodiment")
    source_format, source = selected
    stream, meta, record_start, offsets, *_ = source._open(path)
    records = []
    try:
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short accepted-v0.29 overlay source header")
            codec, usize, csize, crc, logical_sha = PH.unpack(header)
            payload = stream.read(csize)
            if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("accepted-v0.29 overlay source leaf mismatch")
            record = (codec, usize, payload, crc, logical_sha)
            O.A5._decode_record(record)
            records.append(record)
    finally:
        stream.close()
    return source_format, source, meta, records


def _write_source_verification_view(meta: dict, originals: list[bytes], out: Path) -> object:
    source_format = meta.get("overlay_source_format")
    source = A5 if source_format == "residual-pack-v5" else A4 if source_format == "placement-v4" else None
    if source is None:
        raise RuntimeError("Geometry overlay source-format declaration is unsupported")

    records = []
    for raw in originals:
        codec, payload = A5._compress_record(raw, 19)
        records.append((codec, len(raw), payload, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
    leaves = [H(record[2]) for record in records]
    offsets = []; cursor = 0
    for record in records:
        offsets.append(cursor); cursor += PH.size + len(record[2])

    clean = dict(meta)
    clean["engine"] = clean.get("overlay_base_engine")
    for key in (
        "overlay_base_engine", "overlay_source_format", "physical_geometry", "max_geometry_overlay_record",
        "max_geometry_member_read_amplification", "geometry_lane_widths",
        "max_geometry_delimiter_candidates", "max_geometry_delimiter_segments",
        "max_geometry_delimiter_cell_scans",
    ):
        clean.pop(key, None)
    clean["record_rel_offsets"] = offsets; clean["record_leaf_sha256"] = leaves
    merkle = O._merkle_root(leaves)
    meta_raw = msgpack.packb(clean, use_bin_type=True); meta_comp = O.zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(source.HDR.pack(source.MAG, len(meta_comp), len(meta_raw), len(records), source.MAX_DECODE_UNIT,
                                     source.MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha)); stream.write(payload)
        stream.write(meta_comp)
        stream.write(source.FTR.pack(source.TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))
    return source


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as probe:
        magic = probe.read(8)
    if magic != O.MAG:
        return BASE.strong_verify(archive)
    meta, originals = O._decode_overlay_records(archive)
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-overlay-strict-verify-") as td:
        view = Path(td) / "source-view.cmpct"
        source = _write_source_verification_view(meta, originals, view)
        result = source.strong_verify(view)
    if result.get("tree_sha256") != meta.get("tree_sha256"):
        raise RuntimeError("Geometry overlay strict logical tree mismatch")
    return {
        "ok": True,
        "tree_sha256": result["tree_sha256"],
        "engine": "EntropyGraph-II-v029-GeometryOverlay-v1",
        "overlay_source_format": meta["overlay_source_format"],
        "records": len(originals),
        "transformed_records": sum(item is not None for item in meta["physical_geometry"]),
        "max_geometry_member_read_amplification": meta["max_geometry_member_read_amplification"],
    }


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-overlay-strict-") as td:
        temp = Path(td); base_path = temp / "v029.cmpct"; overlay_path = temp / "overlay.cmpct"
        base_stats = BASE.build(root, base_path)
        with base_path.open("rb") as probe:
            base_magic = probe.read(8)
        if _source_for_magic(base_magic) is None:
            shutil.copyfile(base_path, out)
            return {
                "selected": "v029-fallback-non-overlay-graph", "archive_bytes": out.stat().st_size,
                "v029_bytes": base_path.stat().st_size, "overlay_bytes": None, "saving_vs_v029_bytes": 0,
                "overlay_source_format": "inherited-fallback", "transformed_records": 0,
                "portfolio_create_s": time.perf_counter() - started, "v029": base_stats,
            }

        source_format, _source, base_meta, base_records = _read_source_records(base_path)
        users = O._record_member_lengths(base_meta, len(base_records))
        records = []; transforms = []; auditions = []
        for record_id, record in enumerate(base_records):
            chosen, transform, stats = O._audition_record(record_id, record, users[record_id])
            records.append(chosen); transforms.append(transform); auditions.append(stats)

        annotated_meta = dict(base_meta)
        annotated_meta["overlay_source_format"] = source_format
        write_stats = O._write_overlay(annotated_meta, records, transforms, overlay_path)
        verified = strong_verify(overlay_path)
        expected_tree = O.treehash(root)
        if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
            raise RuntimeError("Geometry overlay strict verification failed before selection")

        base_bytes = base_path.stat().st_size; overlay_bytes = overlay_path.stat().st_size
        if overlay_bytes < base_bytes:
            shutil.copyfile(overlay_path, out); selected = "geometry-overlay"
        else:
            shutil.copyfile(base_path, out); selected = "v029-fallback"
        transformed = [row for row in auditions if row["selected"] != "none"]
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v029_bytes": base_bytes,
            "overlay_bytes": overlay_bytes,
            "saving_vs_v029_bytes": base_bytes - out.stat().st_size,
            "raw_overlay_delta_vs_v029_bytes": overlay_bytes - base_bytes,
            "overlay_source_format": source_format,
            "transformed_records": len(transformed),
            "lane_records": sum(row["selected"] == "lane" for row in transformed),
            "delimiter_records": sum(row["selected"] == "delimiter" for row in transformed),
            "transform_payload_saving_bytes": sum(row["payload_saving_bytes"] for row in transformed),
            "max_selected_member_read_amplification": max((row["max_member_read_amplification"] for row in transformed), default=0.0),
            "overlay_meta_raw_bytes": write_stats["meta_raw_bytes"],
            "overlay_meta_comp_bytes": write_stats["meta_comp_bytes"],
            "portfolio_create_s": time.perf_counter() - started,
            "tree_sha256": expected_tree,
            "auditions": auditions,
            "v029": base_stats,
        }


if __name__ == "__main__":
    # The strict facade is benchmark-facing; the attempt-1 CLI remains useful for primitive debugging.
    O._main()
