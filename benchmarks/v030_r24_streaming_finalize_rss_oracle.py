from __future__ import annotations

"""Byte-identical streaming-finalize oracle for the v0.30 r24 release floor.

The exact-head runtime gate shows Shifted at ~3.21x pack RSS versus accepted v0.29. The phase-RSS
decomposition localizes ~160 MiB of incremental peak to canonical r24 construction alone, while profile
capture is effectively free. The mature Builder holds raw candidates, all compressed results, every
serialized record, a joined data blob, and finally a second full archive concatenation at once.

This oracle changes none of those bytes or policies. It substitutes only a bounded record spool +
ordered bounded-future finalizer for the r24 floor inside fresh-process promoted-product builds, then
requires exact r24 and complete-product archive identity before considering RSS/time evidence.
"""

import argparse
import binascii
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import tempfile
import time
import zipfile

import msgpack

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
import cmpct.builder as B

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
ROUNDS = 2
SPOOL_MEMORY_BYTES = 1024 * 1024
MAX_IN_FLIGHT_FACTOR = 2


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


class StreamingFinalizeBuilder(B.Builder):
    """Same r24 grammar/policy, but never materialize the complete physical payload in RAM."""

    def build(self, out: Path):
        self.scan()
        self._build_micro_packs()
        self._prepare_deflate_reuse()
        self._train_dictionary()

        ordered_hashes = sorted(self.cands)
        blobs = []
        href = {}
        offset = 0

        def encode(h):
            c = self.cands[h]
            codec, comp, meta = self._encode_candidate(h, c)
            return h, len(c.raw), codec, comp, meta

        with tempfile.SpooledTemporaryFile(max_size=SPOOL_MEMORY_BYTES, mode="w+b") as spool:
            if self.encode_workers > 1 and len(ordered_hashes) > 1:
                worker_count = min(self.encode_workers, len(ordered_hashes))
                max_in_flight = max(worker_count, worker_count * MAX_IN_FLIGHT_FACTOR)
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=worker_count, thread_name_prefix="cmpct-encode-stream"
                ) as pool:
                    pending = {}
                    submit_index = 0
                    consume_index = 0
                    while submit_index < min(max_in_flight, len(ordered_hashes)):
                        h = ordered_hashes[submit_index]
                        pending[submit_index] = pool.submit(encode, h)
                        submit_index += 1
                    while consume_index < len(ordered_hashes):
                        h, raw_len, codec, comp, meta = pending.pop(consume_index).result()
                        if submit_index < len(ordered_hashes):
                            nh = ordered_hashes[submit_index]
                            pending[submit_index] = pool.submit(encode, nh)
                            submit_index += 1
                        rec = (
                            B.BHDR.pack(
                                B.BMAGIC,
                                codec,
                                0,
                                0,
                                raw_len,
                                len(comp),
                                len(meta),
                                binascii.crc32(self.cands[h].raw) & 0xFFFFFFFF,
                                h,
                            )
                            + meta
                            + comp
                        )
                        idx = len(blobs)
                        href[h] = idx
                        blobs.append([offset, raw_len, len(comp), codec, len(meta)])
                        spool.write(rec)
                        offset += len(rec)
                        self.cands[h].raw = b""
                        self.cands[h].deflates.clear()
                        consume_index += 1
            else:
                for h in ordered_hashes:
                    h, raw_len, codec, comp, meta = encode(h)
                    rec = (
                        B.BHDR.pack(
                            B.BMAGIC,
                            codec,
                            0,
                            0,
                            raw_len,
                            len(comp),
                            len(meta),
                            binascii.crc32(self.cands[h].raw) & 0xFFFFFFFF,
                            h,
                        )
                        + meta
                        + comp
                    )
                    idx = len(blobs)
                    href[h] = idx
                    blobs.append([offset, raw_len, len(comp), codec, len(meta)])
                    spool.write(rec)
                    offset += len(rec)
                    self.cands[h].raw = b""
                    self.cands[h].deflates.clear()

            def mapref(x):
                return href[bytes(x)]

            files = []
            for row in self.files:
                rel, k, mode, mt, size, h, storage = row
                if storage and storage[0] == B.S_BLOB:
                    storage = [B.S_BLOB, mapref(storage[1])]
                elif storage and storage[0] == B.S_CHUNKS:
                    storage = [B.S_CHUNKS, [mapref(x) for x in storage[1]]]
                elif storage and storage[0] == B.S_CDC:
                    storage = [B.S_CDC, [[ln, mapref(x)] for ln, x in storage[1]]]
                elif storage and storage[0] == B.S_SPARSE:
                    storage = [
                        B.S_SPARSE,
                        [[off, ln, [mapref(x) for x in refs]] for off, ln, refs in storage[1]],
                    ]
                elif storage and storage[0] == B.S_PACK:
                    storage = [B.S_PACK, mapref(storage[1]), storage[2], storage[3]]
                keep_hash = h if (storage and storage[0] in (B.S_CHUNKS, B.S_CDC, B.S_SPARSE)) else None
                files.append([rel, k, mode, mt, size, keep_hash, storage])

            recipes = []
            for skref, lens, payloads, vsha, vsize, vcrc in self.recipes:
                mapped = []
                for rawref, method, stream_hash, csize, level in payloads:
                    rawidx = mapref(rawref)
                    if method == zipfile.ZIP_STORED:
                        mapped.append([rawidx, method, 0, rawidx, csize, -1])
                        continue
                    if bytes(stream_hash) == self.canonical_deflate.get(bytes(rawref)):
                        mapped.append([rawidx, method, 0, rawidx, csize, level])
                    elif bytes(stream_hash) in self.secondary_stream_hashes:
                        mapped.append([rawidx, method, 1, mapref(stream_hash), csize, level])
                    else:
                        mapped.append([rawidx, method, 2, rawidx, csize, level])
                recipes.append([mapref(skref), lens, mapped, vsha, vsize, vcrc])

            owner_counts = {}
            for row in files:
                uid, gid, _ = self.meta_by_rel.get(row[0], (0, 0, {}))
                owner_counts[(uid, gid)] = owner_counts.get((uid, gid), 0) + 1
            common_owner = max(owner_counts, key=owner_counts.get) if owner_counts else (0, 0)
            owner_overrides = []
            xattrs = []
            for i, row in enumerate(files):
                uid, gid, xa = self.meta_by_rel.get(row[0], (*common_owner, {}))
                if (uid, gid) != common_owner:
                    owner_overrides.append([i, uid, gid])
                if xa:
                    xattrs.append([i, [[k, v] for k, v in sorted(xa.items())]])
            fsmeta = {"owner": list(common_owner), "owner_overrides": owner_overrides, "xattrs": xattrs}
            index = {
                "v": B.VERSION,
                "files": files,
                "blobs": blobs,
                "recipes": recipes,
                "dict_blob": (mapref(self.dict_hash) if self.dict_hash else None),
                "fsmeta": fsmeta,
                "features": [
                    "micro-solid-packs",
                    "nested-container-packs",
                    "transitive-pack-integrity",
                    "dedup",
                    "hardlinks",
                    "sparse-files",
                    "content-defined-chunking",
                    "chunk-seeking",
                    "parallel-chunks",
                    "zstd",
                    "zstd-dictionary",
                    "wavflac",
                    "deflate-reuse",
                    "virtual-zip-hybrid-recompress",
                    "crc32-fastpath",
                    "sha256",
                    "dual-index",
                    "transaction-journal",
                    "uid-gid",
                    "xattrs",
                ],
            }
            ib = msgpack.packb(index, use_bin_type=True)
            ic = B.zc(ib, 12)
            ih = B.sha(ib)
            data_bytes = spool.tell()
            header = B.HDR.pack(B.MAGIC, B.VERSION, 0, len(ic), len(ib), data_bytes, ih)
            footer = B.FTR.pack(B.FMAGIC, 0, 1, 0, 0, len(ic), len(ib), 0, ih)
            out = Path(out)
            spool.seek(0)
            with out.open("wb") as fh:
                fh.write(header)
                fh.write(ic)
                shutil.copyfileobj(spool, fh, length=1024 * 1024)
                fh.write(ic)
                fh.write(footer)

        return {
            "bytes": out.stat().st_size,
            "logical_bytes": sum(x[4] for x in files if x[1] != B.K_DIR),
            "unique_blobs": len(blobs),
            "logical_files": sum(x[1] != B.K_DIR for x in files),
            "recipes": len(recipes),
            "index_raw": len(ib),
            "index_comp": len(ic),
            "data_bytes": data_bytes,
            "encode_workers": self.encode_workers,
            "reproducible": self.reproducible,
        }


def _streaming_release_r24_build(base, root: Path, out: Path) -> dict:
    started = time.perf_counter()
    root = Path(root)
    out = Path(out)
    builder = StreamingFinalizeBuilder(root, deflate_reuse_min=base.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = base.R24_RELEASE_MICRO_MAX_FILE_BYTES
    default_target = int(builder.micro_pack_target)
    regular_files, largest_member = base._regular_user_shape(root)
    if largest_member > 0:
        builder.micro_pack_target = min(base.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)
    wide_single_file = regular_files == 1 and largest_member >= base.R24_RELEASE_WIDE_CHUNK_BYTES
    previous_wide = getattr(base._R24_CDC_POLICY, "wide_single_file", False)
    previous_medium_binary = getattr(base._R24_CDC_POLICY, "medium_binary_pack", False)
    base._R24_CDC_POLICY.wide_single_file = wide_single_file
    base._R24_CDC_POLICY.medium_binary_pack = True
    try:
        stats = dict(builder.build(out))
    finally:
        base._R24_CDC_POLICY.wide_single_file = previous_wide
        base._R24_CDC_POLICY.medium_binary_pack = previous_medium_binary
    return {
        **stats,
        "archive_bytes": out.stat().st_size,
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "verified_files": None,
        "verification_state": "deferred-to-selected-artifact",
        "create_s": time.perf_counter() - started,
        "micro_pack_target_default_bytes": default_target,
        "micro_pack_target_release_bytes": int(builder.micro_pack_target),
        "micro_pack_max_file_release_bytes": int(builder.micro_pack_max_file),
        "micro_pack_medium_binary_extension": base.R24_RELEASE_MEDIUM_BINARY_EXT,
        "micro_pack_medium_binary_policy": "shipping-r24-thread-local-existing-s-pack",
        "deflate_reuse_min_release_bytes": base.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
        "locality_selected_member_bytes": largest_member,
        "locality_ceiling": 8.0,
        "locality_pack_policy": "min-2mib-cache-cap-or-8x-largest-regular-member-plus-exact-deflate-retention",
        "regular_user_files": regular_files,
        "large_file_chunk_policy": "fixed-8mib" if wide_single_file else "mature-cdc",
        "large_file_chunk_admission": "one-regular-file-ge-8mib",
        "large_file_chunk_bytes": base.R24_RELEASE_WIDE_CHUNK_BYTES if wide_single_file else None,
        "release_byte_knobs": "environment-independent-r24-v4",
    }


def _worker(variant: str, operation: str, source: Path, work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product
    from experiments import entropygraph_v030_release_product_base as base

    if variant == "streaming":
        product._BASE_R24_BUILD = lambda root, out: _streaming_release_r24_build(base, root, out)
    elif variant != "shipping":
        raise ValueError(variant)

    baseline_rss = _rss_kib()
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    out = work_root / f"{variant}-{operation}.cmpct"
    started = time.perf_counter()
    if operation == "r24":
        stats = dict(product._locality_bounded_r24_build(source, out))
    elif operation == "full":
        stats = dict(product.build(source, out))
    else:
        raise ValueError(operation)
    wall_s = time.perf_counter() - started
    peak_rss = _rss_kib()

    verified = dict(product.strong_verify(out))
    if not verified.get("ok") or verified.get("tree_sha256") != product.treehash(source):
        raise RuntimeError(f"{variant}/{operation} failed verification: {verified!r}")
    return {
        "variant": variant,
        "operation": operation,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256_file(out),
        "tree_sha256": verified["tree_sha256"],
        "wall_s": wall_s,
        "baseline_rss_kib": baseline_rss,
        "operation_peak_rss_kib": peak_rss,
        "incremental_peak_rss_kib": max(0, peak_rss - baseline_rss),
        "build_stats": stats,
    }


def _run_worker(variant: str, operation: str, source: Path, work_root: Path) -> dict:
    import subprocess
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-variant",
            variant,
            "--worker-operation",
            operation,
            "--source",
            str(source),
            "--work-root",
            str(work_root),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def _ratio(num: float, den: float) -> float | None:
    return None if den <= 0 else num / den


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    accepted = GENERAL._accepted_v029_rows()
    rows = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        expected = str(accepted[(suite, name)]["tree_sha256"])
        if GENERAL._historical_treehash(source) != expected:
            raise RuntimeError(f"source drift for {suite}/{name}")
        reps = []
        orders = (("shipping", "streaming"), ("streaming", "shipping"))
        for rep, order in enumerate(orders):
            measured = {}
            for variant in order:
                measured[variant] = {}
                for operation in ("r24", "full"):
                    measured[variant][operation] = _run_worker(
                        variant,
                        operation,
                        source,
                        work_root / "arms" / f"{suite}-{name}-r{rep}-{variant}-{operation}",
                    )
            for operation in ("r24", "full"):
                a = measured["shipping"][operation]
                b = measured["streaming"][operation]
                if (a["archive_bytes"], a["archive_sha256"], a["tree_sha256"]) != (
                    b["archive_bytes"],
                    b["archive_sha256"],
                    b["tree_sha256"],
                ):
                    raise RuntimeError(f"byte/tree drift for {suite}/{name}/{operation}")
            reps.append(measured)

        med = {}
        for variant in ("shipping", "streaming"):
            med[variant] = {}
            for operation in ("r24", "full"):
                med[variant][operation] = {
                    "wall_s": statistics.median(r[variant][operation]["wall_s"] for r in reps),
                    "incremental_peak_rss_kib": statistics.median(
                        r[variant][operation]["incremental_peak_rss_kib"] for r in reps
                    ),
                }

        rows.append(
            {
                "target": f"{suite}/{name}",
                "repetitions": reps,
                "median": med,
                "full_rss_ratio_streaming_to_shipping": _ratio(
                    med["streaming"]["full"]["incremental_peak_rss_kib"],
                    med["shipping"]["full"]["incremental_peak_rss_kib"],
                ),
                "r24_rss_ratio_streaming_to_shipping": _ratio(
                    med["streaming"]["r24"]["incremental_peak_rss_kib"],
                    med["shipping"]["r24"]["incremental_peak_rss_kib"],
                ),
                "full_wall_ratio_streaming_to_shipping": _ratio(
                    med["streaming"]["full"]["wall_s"], med["shipping"]["full"]["wall_s"]
                ),
            }
        )

    shifted = next(r for r in rows if r["target"].endswith("/01_shifted_versions"))
    exact = all(
        rep["shipping"][operation]["archive_sha256"] == rep["streaming"][operation]["archive_sha256"]
        for row in rows
        for rep in row["repetitions"]
        for operation in ("r24", "full")
    )
    no_material_wall_regression = all(
        (r["full_wall_ratio_streaming_to_shipping"] or 99) <= 1.05 for r in rows
    )
    promotion_signal = bool(
        exact
        and no_material_wall_regression
        and shifted["full_rss_ratio_streaming_to_shipping"] is not None
        and shifted["full_rss_ratio_streaming_to_shipping"] <= 0.75
        and shifted["r24_rss_ratio_streaming_to_shipping"] is not None
        and shifted["r24_rss_ratio_streaming_to_shipping"] <= 0.50
    )
    return {
        "schema": "cmpct-v030-r24-streaming-finalize-rss-v1",
        "rounds": ROUNDS,
        "targets": [f"{s}/{n}" for s, n in TARGETS],
        "rows": rows,
        "contract": {
            "archive_bytes_changed": False,
            "r24_policy_changed": False,
            "selector_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "rss_release_threshold_changed": False,
            "bounded_encode_in_flight": True,
            "spool_memory_bytes": SPOOL_MEMORY_BYTES,
            "promotion_shifted_full_rss_max_ratio": 0.75,
            "promotion_shifted_r24_rss_max_ratio": 0.50,
            "maximum_full_wall_regression_ratio": 1.05,
        },
        "experiment_valid": exact,
        "promotion_signal": promotion_signal,
        "selector_change": False,
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss.json"))
    p.add_argument("--worker-variant", choices=("shipping", "streaming"))
    p.add_argument("--worker-operation", choices=("r24", "full"))
    p.add_argument("--source", type=Path)
    args = p.parse_args()
    if args.worker_variant:
        if args.source is None or args.worker_operation is None:
            raise SystemExit("worker requires --source and --worker-operation")
        print(
            json.dumps(
                _worker(args.worker_variant, args.worker_operation, args.source, args.work_root),
                separators=(",", ":"),
                default=str,
            )
        )
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": [
                    {
                        "target": r["target"],
                        "full_rss_ratio": r["full_rss_ratio_streaming_to_shipping"],
                        "r24_rss_ratio": r["r24_rss_ratio_streaming_to_shipping"],
                        "full_wall_ratio": r["full_wall_ratio_streaming_to_shipping"],
                    }
                    for r in result["rows"]
                ],
                "promotion_signal": result["promotion_signal"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("streaming-finalize experiment invalid")


if __name__ == "__main__":
    main()
