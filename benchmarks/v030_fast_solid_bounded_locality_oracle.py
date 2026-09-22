from __future__ import annotations

"""Frozen R4 transfer oracle for compact inline-solid under bounded decoded context.

See docs/v030-rnd/R25_FAST_SOLID_BOUNDED_LOCALITY_V2_PREREG.md.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as B
from benchmarks import v030_fast_solid_inline_oracle as PARENT
from benchmarks import v030_release_generalization as GENERAL

MAGIC = b"C30BLD2\0"
HEADER = struct.Struct("<8sQ32s")
MAX_AMP = 8.0
MAX_UNIT = 8 * 1024 * 1024
FROZEN = {
    "neutral_hostile_v1/07_incompressible_and_encrypted_like": ("inline-ext", 12, 0),
    "neutral_hostile_v1/08_many_tiny_files": ("inline-path", 15, 0),
    "neutral_hostile_v1/10_large_mixed_binary": ("inline-ext", 6, 0),
    "resemblance_hostile_v1/01_shifted_versions": ("inline-path", 15, 0),
    "resemblance_hostile_v1/02_false_neighbors": ("inline-ext", 3, 0),
    "resemblance_hostile_v1/05_incompressible": ("inline-ext", 1, 0),
}


def _build_units(rows: list[dict]) -> list[bytes]:
    units: list[bytes] = []
    current: list[dict] = []
    total = minimum = 0

    def flush() -> None:
        nonlocal current, total, minimum
        if not current:
            return
        unit_id = len(units)
        payload = b"".join(row["raw"] for row in current)
        offset = 0
        for row in current:
            row["segments"].append([unit_id, offset, row["size"]])
            offset += row["size"]
        units.append(payload)
        current, total, minimum = [], 0, 0

    for row in rows:
        row["segments"] = []
        size = row["size"]
        if size == 0:
            flush()
            continue
        if size > MAX_UNIT:
            flush()
            offset = 0
            while offset < size:
                piece = row["raw"][offset : offset + MAX_UNIT]
                unit_id = len(units)
                units.append(piece)
                row["segments"].append([unit_id, 0, len(piece)])
                offset += len(piece)
            continue
        if not current:
            current, total, minimum = [row], size, size
            continue
        next_total = total + size
        next_minimum = min(minimum, size)
        if next_total <= MAX_UNIT and next_total <= int(MAX_AMP * next_minimum):
            current.append(row)
            total, minimum = next_total, next_minimum
        else:
            flush()
            current, total, minimum = [row], size, size
    flush()
    return units


def _write(stage: Path, archive: Path, variant: str, level: int, threads: int) -> dict:
    started = time.perf_counter()
    rows = []
    previous = ""
    for path in PARENT._ordered_files(stage, variant):
        raw = path.read_bytes()
        rel = path.relative_to(stage).as_posix()
        prefix = PARENT._common_prefix(previous, rel)
        rows.append({
            "prefix": prefix,
            "suffix": rel[prefix:],
            "raw": raw,
            "size": len(raw),
            "sha": hashlib.sha256(raw).digest(),
        })
        previous = rel

    raw_units = _build_units(rows)
    frames = []
    unit_meta = []
    for payload in raw_units:
        frame = zstd.ZstdCompressor(level=level, threads=threads).compress(payload)
        frames.append(frame)
        unit_meta.append([len(payload), len(frame), hashlib.sha256(payload).digest()])

    entries = []
    max_amp = 1.0
    for row in rows:
        if row["size"]:
            context = sum(len(raw_units[segment[0]]) for segment in row["segments"])
            max_amp = max(max_amp, context / row["size"])
        entries.append([row["prefix"], row["suffix"], row["segments"], row["size"], row["sha"]])

    index = msgpack.packb(
        ["cmpct-fast-solid-bounded-v2", variant, level, entries, unit_meta],
        use_bin_type=True,
    )
    archive.write_bytes(HEADER.pack(MAGIC, len(index), hashlib.sha256(index).digest()) + index + b"".join(frames))
    return {
        "variant": variant,
        "level": level,
        "threads": threads,
        "archive_bytes": archive.stat().st_size,
        "create_s": time.perf_counter() - started,
        "members": len(entries),
        "units": len(unit_meta),
        "index_bytes": len(index),
        "max_decoded_context_amplification": max_amp,
        "max_unit_raw_bytes": max((len(payload) for payload in raw_units), default=0),
    }


def _extract(archive: Path, dst: Path) -> float:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short bounded-inline archive")
    magic, index_len, expected_index_sha = HEADER.unpack(raw[: HEADER.size])
    if magic != MAGIC:
        raise RuntimeError("bad bounded-inline magic")
    index_end = HEADER.size + int(index_len)
    if index_end > len(raw):
        raise RuntimeError("bounded-inline index outside archive")
    index = raw[HEADER.size:index_end]
    if hashlib.sha256(index).digest() != expected_index_sha:
        raise RuntimeError("bounded-inline index identity mismatch")
    head = msgpack.unpackb(index, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 5 or head[0] != "cmpct-fast-solid-bounded-v2":
        raise RuntimeError("bad bounded-inline index")
    _, variant, level, entries, units = head
    if variant not in PARENT.VARIANTS or not isinstance(level, int):
        raise RuntimeError("bad bounded-inline profile")

    pos = index_end
    decoded = []
    for unit in units:
        if not isinstance(unit, list) or len(unit) != 3:
            raise RuntimeError("bad bounded-inline unit")
        raw_len, comp_len, expected_sha = unit
        if raw_len < 0 or raw_len > MAX_UNIT or comp_len < 0 or pos + comp_len > len(raw):
            raise RuntimeError("bad bounded-inline unit bounds")
        payload = zstd.ZstdDecompressor().decompress(raw[pos : pos + comp_len], max_output_size=max(1, raw_len))
        pos += comp_len
        if len(payload) != raw_len or hashlib.sha256(payload).digest() != expected_sha:
            raise RuntimeError("bounded-inline unit identity mismatch")
        decoded.append(payload)
    if pos != len(raw):
        raise RuntimeError("trailing bounded-inline bytes")

    dst.mkdir(parents=True, exist_ok=True)
    previous = ""
    seen = set()
    max_amp = 1.0
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 5:
            raise RuntimeError("bad bounded-inline member")
        prefix, suffix, segments, length, expected_sha = entry
        if not isinstance(prefix, int) or not isinstance(suffix, str) or not isinstance(segments, list):
            raise RuntimeError("bad bounded-inline member types")
        if prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad bounded-inline path prefix")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe/duplicate bounded-inline path")
        pieces = []
        context = 0
        for segment in segments:
            if not isinstance(segment, list) or len(segment) != 3 or not all(isinstance(v, int) for v in segment):
                raise RuntimeError("bad bounded-inline segment")
            unit_id, offset, span = segment
            if unit_id < 0 or unit_id >= len(decoded):
                raise RuntimeError("bad bounded-inline unit id")
            unit = decoded[unit_id]
            if offset < 0 or span < 0 or offset + span > len(unit):
                raise RuntimeError("bad bounded-inline member span")
            pieces.append(unit[offset : offset + span])
            context += len(unit)
        member = b"".join(pieces)
        if len(member) != length or hashlib.sha256(member).digest() != expected_sha:
            raise RuntimeError("bounded-inline member identity mismatch")
        if length:
            max_amp = max(max_amp, context / length)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(member)
        previous = rel
        seen.add(rel)
    return max_amp


def _one(label: str, source: Path, work: Path) -> dict:
    variant, level, threads = FROZEN[label]
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-bounded-inline-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")
        candidate = _write(stage, root / "candidate.bin", variant, level, threads)
        observed_amp = _extract(root / "candidate.bin", root / "candidate-out")
        B._verify_extracted(root / "candidate-out", expected_tree, "bounded-inline")
        if abs(observed_amp - candidate["max_decoded_context_amplification"]) > 1e-12:
            raise RuntimeError("bounded-inline locality accounting mismatch")
        gates = {
            "tree_verified": True,
            "member_and_unit_integrity_verified": True,
            "locality_le_8x": observed_amp <= MAX_AMP,
            "decode_unit_le_8mib": candidate["max_unit_raw_bytes"] <= MAX_UNIT,
            "beats_zip_size": candidate["archive_bytes"] < zip_result["archive_bytes"],
            "beats_zstd19_size": candidate["archive_bytes"] < zstd_result["archive_bytes"],
            "beats_zip_create": candidate["create_s"] < zip_result["create_s"],
            "beats_zstd19_create": candidate["create_s"] < zstd_result["create_s"],
        }
        gates["supported"] = all(gates.values())
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": candidate["members"],
            "logical_bytes": sum(path.stat().st_size for path in B._files(stage)),
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidate": candidate,
            "gates": gates,
            "decision": f"FAST_SOLID_BOUNDED_LOCALITY_ROW_{'SUPPORTED' if gates['supported'] else 'NOT_SUPPORTED'}:{label}",
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_bounded_inline_neutral")
    resemblance = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_bounded_inline_resemblance")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_bounded_inline_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", resemblance, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            label = f"{suite}/{workload.name}"
            if label not in FROZEN:
                continue
            key = (suite, workload.name)
            if B._tree(workload) != accepted[key]["tree_sha256"]:
                raise RuntimeError(f"bounded-inline source drift: {label}")
            row = _one(label, workload, work_root)
            rows.append(row)
            c = row["candidate"]
            print(json.dumps({
                "label": label,
                "decision": row["decision"],
                "candidate": [c["archive_bytes"], c["create_s"], c["units"], c["index_bytes"], c["max_decoded_context_amplification"], c["max_unit_raw_bytes"]],
                "zip": [row["zip"]["archive_bytes"], row["zip"]["create_s"]],
                "zstd19": [row["tar_zstd19"]["archive_bytes"], row["tar_zstd19"]["create_s"]],
            }, separators=(",", ":")), flush=True)
    if len(rows) != len(FROZEN):
        raise RuntimeError(f"expected {len(FROZEN)} frozen rows, got {len(rows)}")
    supported = [row for row in rows if row["gates"]["supported"]]
    return {
        "schema": "cmpct-v030-fast-solid-bounded-locality-oracle-v2",
        "claim_boundary": "research-only R4 product-survival oracle; no release credit",
        "rows": rows,
        "summary": {
            "tested_rows": len(rows),
            "supported_rows": len(supported),
            "supported_labels": [row["label"] for row in supported],
            "tested_logical_bytes": sum(row["logical_bytes"] for row in rows),
            "supported_logical_bytes": sum(row["logical_bytes"] for row in supported),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-bounded-inline-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-bounded-inline.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
