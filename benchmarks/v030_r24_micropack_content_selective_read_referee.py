from __future__ import annotations

"""Selective-read referee for path-blind content-economic micro-packs.

Mission lock
============
Content-economic admission earned a large stored-byte win while preserving the
existing <=8x smallest-member locality law, but its Developer candidate exposed
a much larger absolute decode unit than the extension-bucket control.  The
falsifiable hypothesis here is that the larger legal unit does *not* create a
confirmed selective-read timing regression under the project's existing
same-runner confidence envelope.

Disproof is intentionally simple: on the same source tree and exact same fixed
range probes, content-economic is in product debt if its median cold read time
is >5% *and* >3 ms slower than the same-grammar independent control.  A debt
against the extension-bucket research control is also preserved separately.
The 8x locality law, archive semantics, integrity checks and probe set are never
weakened to make a result pass.

This remains research-only and grants no release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import time

from cmpct.codec import CODEC_RAW
from cmpct.reader import CMPCT

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder

ROUNDS = 5
MAX_PROBES = 32
RANGE_BYTES = 4096
RELATIVE_REGRESSION = 0.05
ABSOLUTE_REGRESSION_S = 0.003


def _build_variant(builder_cls, source: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    builder = builder_cls(source, deflate_reuse_min=0, workers=1)
    builder.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    archive = root / "base.cmpct"
    build = BASE._build_with(builder, archive)
    index, data = BASE._parse_r24(archive)
    locality = BASE._pack_locality(index)
    verify = BASE.PRODUCT.strong_verify(archive)
    if not verify.get("ok"):
        raise RuntimeError("strong verify failed")

    membership = root / "membership.cmpct"
    if getattr(builder, "_locality_derived_groups", []):
        wrapped = SAME._candidate(archive, membership, root)
    else:
        wrapped = SAME._noop_candidate(archive, len(data), verify)

    return {
        "archive": archive,
        "index": index,
        "r24_bytes": int(build["archive_bytes"]),
        "final_membership_bytes": int(wrapped["archive_bytes"]),
        "groups": len(getattr(builder, "_locality_derived_groups", [])),
        "locality_pass": bool(locality["locality_pass"]),
        "max_member_amplification": float(locality["max_member_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "strong_tree_exact": bool(verify.get("ok")),
        "physical_payload_exact": bool(wrapped["physical_payload_exact"]),
        "tail_recovery": bool(wrapped["primary_corruption_tail_recovery"]),
        "audit": dict(getattr(builder, "_content_economic_audit", {})),
    }


def _charge(index: dict, row: list, length: int) -> dict:
    storage = row[6]
    if storage[0] == BASE.R24.S_PACK:
        off, usize, csize, codec, mlen = index["blobs"][storage[1]]
        return {
            "storage": "pack",
            "decoded_context_bytes": int(usize),
            "compressed_payload_bytes_touched": int(csize),
        }
    if storage[0] == BASE.R24.S_BLOB:
        off, usize, csize, codec, mlen = index["blobs"][storage[1]]
        if int(codec) == int(CODEC_RAW):
            return {
                "storage": "raw_blob",
                "decoded_context_bytes": int(length),
                "compressed_payload_bytes_touched": int(length),
            }
        return {
            "storage": "compressed_blob",
            "decoded_context_bytes": int(usize),
            "compressed_payload_bytes_touched": int(csize),
        }
    return {
        "storage": f"other:{storage[0]}",
        "decoded_context_bytes": int(row[4]),
        "compressed_payload_bytes_touched": None,
    }


def _probes(source: Path, content: dict) -> list[dict]:
    rows = []
    for row in content["index"]["files"]:
        if row[1] != BASE.R24.K_FILE or row[4] <= 0 or not row[6] or row[6][0] != BASE.R24.S_PACK:
            continue
        charge = _charge(content["index"], row, min(RANGE_BYTES, int(row[4])))
        rows.append((int(charge["decoded_context_bytes"]), row[0], row))
    rows.sort(key=lambda item: (-item[0], item[1]))
    picked = rows[:MAX_PROBES]
    out = []
    for _, name, row in picked:
        size = int(row[4])
        length = min(RANGE_BYTES, size)
        start = max(0, (size - length) // 2)
        expected = (source / name).read_bytes()[start:start + length]
        out.append({
            "path": name,
            "start": start,
            "length": length,
            "expected_sha256": hashlib.sha256(expected).hexdigest(),
        })
    return out


def _time_variant(variant: dict, probes: list[dict]) -> dict:
    read_cpu_rounds = []
    read_wall_rounds = []
    open_cpu_rounds = []
    open_wall_rounds = []
    failures = []

    for _ in range(ROUNDS):
        read_cpu = read_wall = open_cpu = open_wall = 0.0
        for probe in probes:
            c0 = time.process_time(); w0 = time.perf_counter()
            archive = CMPCT(variant["archive"])
            open_cpu += time.process_time() - c0
            open_wall += time.perf_counter() - w0
            try:
                c0 = time.process_time(); w0 = time.perf_counter()
                got = archive.read_range(probe["path"], probe["start"], probe["length"])
                read_cpu += time.process_time() - c0
                read_wall += time.perf_counter() - w0
            finally:
                archive.close()
            if hashlib.sha256(got).hexdigest() != probe["expected_sha256"]:
                failures.append(probe["path"])
        read_cpu_rounds.append(read_cpu)
        read_wall_rounds.append(read_wall)
        open_cpu_rounds.append(open_cpu)
        open_wall_rounds.append(open_wall)

    charges = []
    by_name = {row[0]: row for row in variant["index"]["files"]}
    for probe in probes:
        row = by_name[probe["path"]]
        item = dict(probe)
        item.update(_charge(variant["index"], row, probe["length"]))
        charges.append(item)

    n = max(1, len(probes))
    read_wall_median = statistics.median(read_wall_rounds)
    read_cpu_median = statistics.median(read_cpu_rounds)
    return {
        "probe_count": len(probes),
        "rounds": ROUNDS,
        "read_cpu_s_rounds": read_cpu_rounds,
        "read_wall_s_rounds": read_wall_rounds,
        "open_cpu_s_rounds": open_cpu_rounds,
        "open_wall_s_rounds": open_wall_rounds,
        "median_read_cpu_s": read_cpu_median,
        "median_read_wall_s": read_wall_median,
        "median_read_cpu_ms_per_probe": read_cpu_median * 1000.0 / n,
        "median_read_wall_ms_per_probe": read_wall_median * 1000.0 / n,
        "median_open_cpu_s": statistics.median(open_cpu_rounds),
        "median_open_wall_s": statistics.median(open_wall_rounds),
        "correctness_failures": sorted(set(failures)),
        "sum_decoded_context_bytes": sum(int(x["decoded_context_bytes"]) for x in charges),
        "max_decoded_context_bytes": max((int(x["decoded_context_bytes"]) for x in charges), default=0),
        "sum_compressed_payload_bytes_touched": sum(int(x["compressed_payload_bytes_touched"] or 0) for x in charges),
        "charges": charges,
    }


def _confirmed_regression(candidate: dict, base: dict) -> dict:
    c = float(candidate["median_read_wall_s"])
    b = float(base["median_read_wall_s"])
    delta = c - b
    relative = (c / b - 1.0) if b > 0 else 0.0
    confirmed = delta > ABSOLUTE_REGRESSION_S and relative > RELATIVE_REGRESSION
    return {
        "candidate_wall_s": c,
        "base_wall_s": b,
        "delta_wall_s": delta,
        "relative": relative,
        "confirmed_regression": confirmed,
    }


def _one(source: Path, root: Path) -> dict:
    variants = {
        "independent": _build_variant(SAME.NoMicroPackBuilder, source, root / "independent"),
        "extension": _build_variant(BASE.LocalityDerivedBuilder, source, root / "extension"),
        "content_economic": _build_variant(ContentEconomicBuilder, source, root / "content_economic"),
    }
    probes = _probes(source, variants["content_economic"])
    if not probes:
        return {
            "skipped_no_content_packs": True,
            "variants": {name: {k: v for k, v in arm.items() if k not in {"archive", "index"}} for name, arm in variants.items()},
        }

    timings = {name: _time_variant(arm, probes) for name, arm in variants.items()}
    invariants = {
        "all_locality": all(v["locality_pass"] for v in variants.values()),
        "all_tree_exact": all(v["strong_tree_exact"] for v in variants.values()),
        "content_payload_exact": variants["content_economic"]["physical_payload_exact"],
        "content_tail_recovery": variants["content_economic"]["tail_recovery"],
        "all_reads_exact": all(not t["correctness_failures"] for t in timings.values()),
        "content_amp_at_most_8x": variants["content_economic"]["max_member_amplification"] <= BASE.LOCALITY_BUDGET + 1e-9,
    }
    clean_variants = {name: {k: v for k, v in arm.items() if k not in {"archive", "index"}} for name, arm in variants.items()}
    return {
        "skipped_no_content_packs": False,
        "probe_policy": "up to 32 content-economic packed regular files ordered by descending decoded-context bytes; midpoint range <=4096 B",
        "probes": probes,
        "variants": clean_variants,
        "timings": timings,
        "content_vs_independent": _confirmed_regression(timings["content_economic"], timings["independent"]),
        "content_vs_extension": _confirmed_regression(timings["content_economic"], timings["extension"]),
        "invariants": invariants,
        "invariants_pass": all(invariants.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    origin = work_root / "origin"
    ATTR._build_sources(origin)
    # Developer is the causal blocker: prior evidence exposed a 540,072 B legal
    # decode unit here while extension buckets stayed near 17 KiB.  Tiny Files
    # is included as the strongest density win and a second shape control.
    sources = {
        "origin_developer": origin / "01_developer_repository",
        "origin_tiny_files": origin / "08_many_tiny_files",
    }
    rows = {name: _one(source, work_root / "work" / name) for name, source in sources.items()}
    invariant_failures = [name for name, row in rows.items() if not row.get("skipped_no_content_packs") and not row["invariants_pass"]]
    independent_timing_debt = [name for name, row in rows.items() if not row.get("skipped_no_content_packs") and row["content_vs_independent"]["confirmed_regression"]]
    extension_timing_debt = [name for name, row in rows.items() if not row.get("skipped_no_content_packs") and row["content_vs_extension"]["confirmed_regression"]]

    if invariant_failures:
        verdict = "RETIRE_CONTENT_ECONOMIC_SELECTIVE_READ"
    elif independent_timing_debt:
        verdict = "CONTENT_ECONOMIC_SELECTIVE_READ_REHABILITATION_REQUIRED"
    elif extension_timing_debt:
        verdict = "CONTENT_ECONOMIC_SELECTIVE_READ_SAFE_WITH_EXTENSION_DEBT"
    else:
        verdict = "CONTENT_ECONOMIC_SELECTIVE_READ_SURVIVES"

    return {
        "schema": "cmpct-v030-r24-micropack-content-selective-read-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "locality_budget": BASE.LOCALITY_BUDGET,
        "timing_regression_confidence": {
            "relative": RELATIVE_REGRESSION,
            "absolute_s": ABSOLUTE_REGRESSION_S,
            "rule": "confirmed only when candidate slowdown exceeds both thresholds",
        },
        "rss_credit": False,
        "rss_note": "This mechanism referee intentionally does not claim RSS: build state and repeated readers share one process. A fresh-process RSS gate is required before promotion.",
        "sources": rows,
        "invariant_failures": invariant_failures,
        "timing_debt_vs_independent": independent_timing_debt,
        "timing_debt_vs_extension": extension_timing_debt,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-micropack-content-selective-read-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-micropack-content-selective-read.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "invariant_failures": result["invariant_failures"],
        "timing_debt_vs_independent": result["timing_debt_vs_independent"],
        "timing_debt_vs_extension": result["timing_debt_vs_extension"],
        "sources": {
            name: {
                "skipped": row.get("skipped_no_content_packs", False),
                "content_max_decode": row.get("variants", {}).get("content_economic", {}).get("max_decode_unit_bytes"),
                "independent_ms_per_probe": row.get("timings", {}).get("independent", {}).get("median_read_wall_ms_per_probe"),
                "extension_ms_per_probe": row.get("timings", {}).get("extension", {}).get("median_read_wall_ms_per_probe"),
                "content_ms_per_probe": row.get("timings", {}).get("content_economic", {}).get("median_read_wall_ms_per_probe"),
            }
            for name, row in result["sources"].items()
        },
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
