from __future__ import annotations

"""Research-only compact-control frontier for r24-shaped payloads.

The shipping encrypted-like row is already cheap to build as canonical r24, but remains only a few tens of
kilobytes larger than solid Zstd-19. Revision 24 stores the same compressed MessagePack index at both the head and
tail for recovery. This oracle asks a narrow question before inventing another compressor: can a semantically
identical, columnar/prefix-delta control plane recover enough bytes while retaining *two* authenticated control
copies and the exact existing physical payload records?

This does not emit a shipping r24 archive and cannot authorize release. A positive result is a productization
signal for a bounded r25 compact-control profile; a negative result proves that r24 control framing is not enough.
Creation timing is deliberately conservative: it charges shipping r24 build + mandatory strong verification + a
post-build decode/re-encode of the control plane. A production writer would replace, rather than add, that work.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

import msgpack

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import v030_external_competitors as EXT
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 5
LEVELS = (1, 3, 6, 9, 12, 19)
TARGET_NAME = "07_incompressible_and_encrypted_like"
DIAGNOSTIC_NAME = "08_many_tiny_files"


def _common_prefix(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _mode(values: list[int], default: int = 0) -> int:
    if not values:
        return default
    counts = Counter(values)
    return min(((-count, value) for value, count in counts.items()))[1]


def _derived_size(index: dict, kind: int, storage, prior_sizes: dict[str, int]) -> int | None:
    if kind == R24.K_DIR:
        return 0
    if kind == R24.K_HARDLINK:
        if not storage or not storage[0]:
            return None
        return prior_sizes.get(str(storage[0]))
    if not storage:
        return None
    tag = int(storage[0])
    blobs = index["blobs"]
    if tag == R24.S_BLOB:
        return int(blobs[int(storage[1])][1])
    if tag == R24.S_PACK:
        return int(storage[3])
    if tag == R24.S_CHUNKS:
        return sum(int(blobs[int(ref)][1]) for ref in storage[1])
    if tag == R24.S_CDC:
        return sum(int(row[0]) for row in storage[1])
    if tag == R24.S_VZIP:
        return int(index["recipes"][int(storage[1])][4])
    return None


def _compact_index(index: dict) -> dict:
    files = index["files"]
    default_mode = _mode([int(row[2]) for row in files])
    default_mtime = _mode([int(row[3]) for row in files])
    paths = []
    rows = []
    previous = ""
    path_to_index: dict[str, int] = {}
    prior_sizes: dict[str, int] = {}

    for file_index, row in enumerate(files):
        rel, kind, mode, mtime, size, digest, storage = row
        rel = str(rel)
        prefix = _common_prefix(previous, rel)
        paths.append([prefix, rel[prefix:]])
        previous = rel
        path_to_index[rel] = file_index

        mode_override = None if int(mode) == default_mode else int(mode)
        mtime_delta = int(mtime) - default_mtime
        kind = int(kind)

        if kind == R24.K_DIR:
            encoded = [kind, mode_override, mtime_delta]
        elif kind == R24.K_HARDLINK:
            owner = str(storage[0])
            if owner not in path_to_index:
                raise RuntimeError(f"hardlink owner must precede alias: {rel!r} -> {owner!r}")
            encoded = [kind, mode_override, mtime_delta, path_to_index[owner]]
        else:
            derived = _derived_size(index, kind, storage, prior_sizes)
            explicit_size = None if derived == int(size) else int(size)
            tag = int(storage[0]) if storage else -1
            keep_digest = digest if tag in (R24.S_CHUNKS, R24.S_CDC, R24.S_SPARSE) else None
            encoded = [kind, mode_override, mtime_delta, storage, explicit_size, keep_digest]
        rows.append(encoded)
        prior_sizes[rel] = int(size)

    # v/features are profile constants in the research grammar. The remaining fields are retained verbatim.
    return {
        "p": paths,
        "d": [default_mode, default_mtime],
        "f": rows,
        "b": index["blobs"],
        "r": index["recipes"],
        "z": index.get("dict_blob"),
        "m": index["fsmeta"],
    }


def _expand_index(compact: dict, *, version: int, features: list) -> dict:
    default_mode, default_mtime = compact["d"]
    files = []
    previous = ""
    prior_paths: list[str] = []
    prior_sizes: dict[str, int] = {}
    shell = {
        "v": version,
        "files": files,
        "blobs": compact["b"],
        "recipes": compact["r"],
        "dict_blob": compact.get("z"),
        "fsmeta": compact["m"],
        "features": features,
    }
    for path_row, encoded in zip(compact["p"], compact["f"], strict=True):
        prefix, suffix = int(path_row[0]), str(path_row[1])
        if prefix < 0 or prefix > len(previous):
            raise RuntimeError("invalid compact path prefix")
        rel = previous[:prefix] + suffix
        previous = rel
        kind = int(encoded[0])
        mode = default_mode if encoded[1] is None else int(encoded[1])
        mtime = int(default_mtime) + int(encoded[2])
        if kind == R24.K_DIR:
            size, digest, storage = 0, None, None
        elif kind == R24.K_HARDLINK:
            owner_index = int(encoded[3])
            if owner_index < 0 or owner_index >= len(prior_paths):
                raise RuntimeError("invalid compact hardlink owner")
            owner = prior_paths[owner_index]
            size = prior_sizes[owner]
            digest, storage = None, [owner]
        else:
            storage = encoded[3]
            derived = _derived_size(shell, kind, storage, prior_sizes)
            size = int(encoded[4]) if encoded[4] is not None else derived
            if size is None:
                raise RuntimeError(f"compact row cannot derive logical size: {rel}")
            tag = int(storage[0]) if storage else -1
            digest = encoded[5] if tag in (R24.S_CHUNKS, R24.S_CDC, R24.S_SPARSE) else None
        files.append([rel, kind, mode, mtime, int(size), digest, storage])
        prior_paths.append(rel)
        prior_sizes[rel] = int(size)
    return shell


def _read_index(archive: Path) -> tuple[dict, dict]:
    payload = archive.read_bytes()
    if len(payload) < R24.HDR.size + R24.FTR.size:
        raise RuntimeError("truncated r24 archive")
    magic, version, flags, primary_cbytes, raw_bytes, data_bytes, index_sha = R24.HDR.unpack_from(payload, 0)
    if magic != R24.MAGIC or int(version) != R24.VERSION:
        raise RuntimeError("not canonical r24")
    start = R24.HDR.size
    primary = payload[start : start + int(primary_cbytes)]
    raw = R24.zd(primary, int(raw_bytes))
    if R24.sha(raw) != index_sha:
        raise RuntimeError("r24 index SHA mismatch")
    index = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    footer_off = len(payload) - R24.FTR.size
    tail_start = footer_off - int(primary_cbytes)
    if payload[tail_start:footer_off] != primary:
        raise RuntimeError("r24 primary/tail control copies are not byte-identical")
    return index, {
        "archive_bytes": len(payload),
        "index_raw_bytes": int(raw_bytes),
        "index_comp_bytes_per_copy": int(primary_cbytes),
        "data_bytes": int(data_bytes),
        "fixed_framing_bytes": R24.HDR.size + R24.FTR.size,
    }


def _compact_once(archive: Path) -> dict:
    started = time.perf_counter()
    index, physical = _read_index(archive)
    compact = _compact_index(index)
    packed = msgpack.packb(compact, use_bin_type=True)
    candidates = []
    for level in LEVELS:
        tick = time.perf_counter()
        compressed = R24.zc(packed, level)
        compress_s = time.perf_counter() - tick
        candidates.append((len(compressed), compress_s, level, compressed))
    best = min(candidates, key=lambda row: (row[0], row[2]))
    compact_bytes, compress_s, level, _compressed = best
    expanded = _expand_index(compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("compact control does not expand byte-semantically to the shipping r24 index")
    transform_s = time.perf_counter() - started
    projected = physical["archive_bytes"] - 2 * physical["index_comp_bytes_per_copy"] + 2 * compact_bytes
    return {
        **physical,
        "compact_index_raw_bytes": len(packed),
        "compact_index_comp_bytes_per_copy": compact_bytes,
        "compact_level": level,
        "compact_compress_s": compress_s,
        "compact_transform_s": transform_s,
        "saving_per_control_copy_bytes": physical["index_comp_bytes_per_copy"] - compact_bytes,
        "projected_two_copy_archive_bytes": projected,
        "two_authenticated_control_copies_retained": True,
        "physical_payload_records_unchanged": True,
        "semantic_index_roundtrip_exact": True,
    }


def _verified_r24(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = PRODUCT._locality_bounded_r24_build(root, out)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = PRODUCT.strong_verify(out)
    verify_s = time.perf_counter() - started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    return {
        "build_s": build_s,
        "verify_s": verify_s,
        "complete_create_s": build_s + verify_s,
        "tree_sha256": verified.get("tree_sha256"),
        "stats": stats,
    }


def _build_sources(root: Path) -> dict[str, Path]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    NEUTRAL.corpus_incompressible(root)
    NEUTRAL.corpus_tinyfiles(root)
    return {
        TARGET_NAME: root / TARGET_NAME,
        DIAGNOSTIC_NAME: root / DIAGNOSTIC_NAME,
    }


def _measure_target(source: Path, work: Path) -> dict:
    rows = []
    for rep in range(ROUNDS):
        order = ["cmpct", "zip", "zstd"]
        order = order[rep % 3 :] + order[: rep % 3]
        current = {}
        for name in order:
            if name == "cmpct":
                archive = work / f"target-{rep}.cmpct"
                r24 = _verified_r24(source, archive)
                compact = _compact_once(archive)
                current[name] = {
                    **r24,
                    **compact,
                    # Deliberately overcharge by adding a post-build transform to the already-complete r24 boundary.
                    "conservative_projected_create_s": r24["complete_create_s"] + compact["compact_transform_s"],
                }
            elif name == "zip":
                current[name] = EXT._zip(source, work / f"target-{rep}.zip", work / f"zip-out-{rep}")
            else:
                zw = work / f"zstd-work-{rep}"
                zw.mkdir(parents=True, exist_ok=True)
                current[name] = EXT._tar_zstd(
                    source,
                    work / f"target-{rep}.tar.zst",
                    work / f"zstd-out-{rep}",
                    zw,
                )
        rows.append(current)
    first = rows[0]["cmpct"]
    projected_sizes = {int(row["cmpct"]["projected_two_copy_archive_bytes"]) for row in rows}
    source_trees = {row["cmpct"]["tree_sha256"] for row in rows}
    zip_sizes = {int(row["zip"]["archive_bytes"]) for row in rows}
    zstd_sizes = {int(row["zstd"]["archive_bytes"]) for row in rows}
    projected_create = statistics.median(float(row["cmpct"]["conservative_projected_create_s"]) for row in rows)
    zip_create = statistics.median(float(row["zip"]["create_s"]) for row in rows)
    zstd_create = statistics.median(float(row["zstd"]["create_s"]) for row in rows)
    projected_bytes = next(iter(projected_sizes))
    zip_bytes = next(iter(zip_sizes))
    zstd_bytes = next(iter(zstd_sizes))
    four_way = projected_bytes < zip_bytes and projected_bytes < zstd_bytes and projected_create < zip_create and projected_create < zstd_create
    return {
        "rounds": ROUNDS,
        "shipping_r24_bytes": int(first["archive_bytes"]),
        "shipping_index_comp_bytes_per_copy": int(first["index_comp_bytes_per_copy"]),
        "compact_index_comp_bytes_per_copy": int(first["compact_index_comp_bytes_per_copy"]),
        "saving_per_control_copy_bytes": int(first["saving_per_control_copy_bytes"]),
        "projected_two_copy_archive_bytes": projected_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "median_conservative_projected_create_s": projected_create,
        "median_zip_create_s": zip_create,
        "median_zstd19_create_s": zstd_create,
        "semantic_index_roundtrip_exact": all(row["cmpct"]["semantic_index_roundtrip_exact"] for row in rows),
        "two_authenticated_control_copies_retained": all(row["cmpct"]["two_authenticated_control_copies_retained"] for row in rows),
        "physical_payload_records_unchanged": all(row["cmpct"]["physical_payload_records_unchanged"] for row in rows),
        "projected_size_deterministic": len(projected_sizes) == 1,
        "tree_deterministic": len(source_trees) == 1,
        "comparator_sizes_deterministic": len(zip_sizes) == 1 and len(zstd_sizes) == 1,
        "strict_four_way_potential": four_way,
        "samples": [
            {
                "cmpct_projected_create_s": float(row["cmpct"]["conservative_projected_create_s"]),
                "zip_create_s": float(row["zip"]["create_s"]),
                "zstd_create_s": float(row["zstd"]["create_s"]),
            }
            for row in rows
        ],
    }


def _measure_diagnostic(source: Path, work: Path) -> dict:
    archive = work / "diagnostic.cmpct"
    verified = _verified_r24(source, archive)
    compact = _compact_once(archive)
    return {
        "tree_sha256": verified["tree_sha256"],
        "shipping_r24_bytes": compact["archive_bytes"],
        "shipping_index_comp_bytes_per_copy": compact["index_comp_bytes_per_copy"],
        "compact_index_comp_bytes_per_copy": compact["compact_index_comp_bytes_per_copy"],
        "saving_per_control_copy_bytes": compact["saving_per_control_copy_bytes"],
        "projected_two_copy_archive_bytes": compact["projected_two_copy_archive_bytes"],
        "semantic_index_roundtrip_exact": compact["semantic_index_roundtrip_exact"],
        "two_authenticated_control_copies_retained": compact["two_authenticated_control_copies_retained"],
    }


def run(work_root: Path) -> dict:
    sources = _build_sources(work_root / "sources")
    work = work_root / "work"
    work.mkdir(parents=True, exist_ok=True)
    target = _measure_target(sources[TARGET_NAME], work / "target")
    diagnostic_dir = work / "tiny"
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    diagnostic = _measure_diagnostic(sources[DIAGNOSTIC_NAME], diagnostic_dir)
    gate = {
        "target_semantic_roundtrip_exact": target["semantic_index_roundtrip_exact"],
        "target_two_recovery_copies_retained": target["two_authenticated_control_copies_retained"],
        "target_payload_records_unchanged": target["physical_payload_records_unchanged"],
        "target_measurement_deterministic": target["projected_size_deterministic"] and target["tree_deterministic"] and target["comparator_sizes_deterministic"],
        "experiment_valid": False,
        "target_strict_four_way_potential": target["strict_four_way_potential"],
    }
    gate["experiment_valid"] = all(value for key, value in gate.items() if key != "target_strict_four_way_potential")
    return {
        "schema": "cmpct-v030-r24-compact-control-oracle-v1",
        "contract": {
            "claim_boundary": "research-only exact control-plane lower-cost proof; no shipping grammar or reader promotion",
            "target": f"neutral_hostile_v1/{TARGET_NAME}",
            "diagnostic": f"neutral_hostile_v1/{DIAGNOSTIC_NAME}",
            "control_copies": 2,
            "payload_records": "exact shipping r24 physical records, unchanged",
            "semantic_proof": "compact control expands exactly to the shipping r24 logical index",
            "timing": f"{ROUNDS} rotated rounds; conservative CMPCT time = shipping r24 build + mandatory verification + post-build compact transform",
            "levels": list(LEVELS),
            "release_effect": "none; a win only authorizes work on a bounded canonical r25 compact-control profile",
        },
        "target": target,
        "diagnostic": diagnostic,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control.json"))
    args = parser.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target": result["target"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("r24 compact-control experiment invalid")


if __name__ == "__main__":
    main()
