from __future__ import annotations

"""Full 15-workload research falsifier for content-driven ZIP virtualization.

This is not a release gate. It compares the unchanged shipping Builder against the
research-only ContentZipBuilder on the exact repaired Genesis/v0.29 workload identities.
The existing S_VZIP reader grammar is unchanged. The candidate must preserve the full
logical tree, exact selective reads for every VZIP file, and cleanly avoid regressions.
"""

import argparse
import json
import os
import shutil
import time
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments.v030_r4_content_zip_builder import ContentZipBuilder
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT

RANGE = 4096


def _build(cls, root: Path, archive: Path) -> tuple[dict, float, float]:
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    stats = dict(cls(root).build(archive))
    return stats, time.process_time() - cpu0, time.perf_counter() - wall0


def _verify(archive: Path, source: Path, out: Path) -> dict:
    expected = PRODUCT.treehash(source)
    shutil.rmtree(out, ignore_errors=True)
    checks: list[dict] = []
    with CMPCT(archive) as ar:
        virtual = [row[0] for row in ar.files if row[1] == 0 and row[6] and row[6][0] == S_VZIP]
        for name in virtual:
            raw = (source / name).read_bytes()
            ln = min(RANGE, len(raw))
            starts = sorted({0, max(0, len(raw) // 2 - ln // 2), max(0, len(raw) - ln)})
            for start in starts:
                cpu0 = time.process_time()
                got = ar.read_range(name, start, ln)
                cpu = time.process_time() - cpu0
                if got != raw[start : start + ln]:
                    raise RuntimeError(f"exact VZIP range mismatch: {name} {start}+{ln}")
                checks.append({"name": name, "start": start, "length": ln, "cpu_s": cpu})
        cpu0 = time.process_time()
        ar.extractall(out, metadata=True)
        extract_cpu = time.process_time() - cpu0
    got_tree = PRODUCT.treehash(out)
    if got_tree != expected:
        raise RuntimeError(f"extracted tree mismatch {got_tree} != {expected}")
    return {
        "tree_sha256": got_tree,
        "vzip_files": virtual,
        "vzip_file_count": len(virtual),
        "range_checks": checks,
        "extract_cpu_s": extract_cpu,
    }


def _measure(suite: str, source: Path, outdir: Path, accepted: dict) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    baseline_archive = outdir / "baseline.cmpct"
    candidate_archive = outdir / "candidate.cmpct"
    bstats, bcpu, bwall = _build(Builder, source, baseline_archive)
    cstats, ccpu, cwall = _build(ContentZipBuilder, source, candidate_archive)
    bverify = _verify(baseline_archive, source, outdir / "baseline-out")
    cverify = _verify(candidate_archive, source, outdir / "candidate-out")
    baseline_bytes = baseline_archive.stat().st_size
    candidate_bytes = candidate_archive.stat().st_size
    v029 = int(accepted[(suite, source.name)]["accepted_v029_bytes"])
    saving = baseline_bytes - candidate_bytes
    return {
        "suite": suite,
        "name": source.name,
        "logical_bytes": sum(p.stat().st_size for p in source.rglob("*") if p.is_file()),
        "accepted_v029_bytes": v029,
        "baseline": {
            "archive_bytes": baseline_bytes,
            "create_cpu_s": bcpu,
            "create_wall_s": bwall,
            "builder_stats": bstats,
            **bverify,
        },
        "candidate": {
            "archive_bytes": candidate_bytes,
            "create_cpu_s": ccpu,
            "create_wall_s": cwall,
            "builder_stats": cstats,
            **cverify,
        },
        "saving_vs_baseline_bytes": saving,
        "saving_vs_baseline_pct": saving / max(1, baseline_bytes) * 100.0,
        "saving_vs_v029_bytes": v029 - candidate_bytes,
        "create_cpu_delta_s": ccpu - bcpu,
        "create_wall_delta_s": cwall - bwall,
        "tree_match": bverify["tree_sha256"] == cverify["tree_sha256"],
        "selective_exact": len(cverify["range_checks"]) == 3 * cverify["vzip_file_count"],
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_content_zip_matrix_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_content_zip_matrix_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_content_zip_matrix_repair")
    repair.install_generation_hooks(neutral)

    rows: list[dict] = []
    for label, generator, root in (
        ("neutral_hostile_v1", neutral, work / "neutral"),
        ("resemblance_hostile_v1", hostile, work / "resemblance"),
    ):
        generator.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            row = _measure(label, source, work / "rows" / label / source.name, accepted)
            rows.append(row)
            print(json.dumps({
                "suite": label,
                "name": source.name,
                "baseline": row["baseline"]["archive_bytes"],
                "candidate": row["candidate"]["archive_bytes"],
                "saving": row["saving_vs_baseline_bytes"],
                "vzip": row["candidate"]["vzip_file_count"],
                "cpu_delta": row["create_cpu_delta_s"],
            }), flush=True)

    if len(rows) != 15:
        raise RuntimeError(f"expected 15 workloads, got {len(rows)}")
    if any(not row["tree_match"] for row in rows):
        raise RuntimeError("candidate tree mismatch")
    if any(not row["selective_exact"] for row in rows):
        raise RuntimeError("candidate selective-read mismatch")

    baseline_total = sum(row["baseline"]["archive_bytes"] for row in rows)
    candidate_total = sum(row["candidate"]["archive_bytes"] for row in rows)
    v029_total = sum(row["accepted_v029_bytes"] for row in rows)
    cpu_base = sum(row["baseline"]["create_cpu_s"] for row in rows)
    cpu_candidate = sum(row["candidate"]["create_cpu_s"] for row in rows)
    total_saving = baseline_total - candidate_total
    regressed = [f"{r['suite']}/{r['name']}" for r in rows if r["candidate"]["archive_bytes"] > r["baseline"]["archive_bytes"]]
    improved = [f"{r['suite']}/{r['name']}" for r in rows if r["candidate"]["archive_bytes"] < r["baseline"]["archive_bytes"]]
    vzip_rows = [f"{r['suite']}/{r['name']}" for r in rows if r["candidate"]["vzip_file_count"]]
    return {
        "schema": "cmpct-v030-r4-content-zip-full-matrix-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "rows": rows,
        "totals": {
            "workloads": len(rows),
            "baseline_bytes": baseline_total,
            "candidate_bytes": candidate_total,
            "accepted_v029_bytes": v029_total,
            "saving_vs_baseline_bytes": total_saving,
            "saving_vs_baseline_pct": total_saving / max(1, baseline_total) * 100.0,
            "saving_vs_v029_bytes": v029_total - candidate_total,
            "baseline_create_cpu_s": cpu_base,
            "candidate_create_cpu_s": cpu_candidate,
            "create_cpu_delta_s": cpu_candidate - cpu_base,
            "improved_rows": len(improved),
            "regressed_rows": len(regressed),
            "improved_row_names": improved,
            "regressed_row_names": regressed,
            "vzip_rows": vzip_rows,
        },
        "hypothesis": {
            "all_trees_exact": all(r["tree_match"] for r in rows),
            "all_vzip_ranges_exact": all(r["selective_exact"] for r in rows),
            "zero_byte_regressions": not regressed,
            "aggregate_strict_win": candidate_total < baseline_total,
            "closes_at_least_50pct_of_gap_to_v029": total_saving >= max(0, baseline_total - v029_total) * 0.5,
            "supported_for_hardening": (
                not regressed
                and candidate_total < baseline_total
                and all(r["tree_match"] and r["selective_exact"] for r in rows)
            ),
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "shipping_builder_changed": False,
            "format_changed": False,
            "reader_changed": False,
            "same_physical_workloads": True,
            "accepted_v029_is_context_only": True,
        },
        "next_if_supported": "add hostile parser/resource/recovery tests, measure repeated create/read/RSS and selective amplification, then test a shipping-Builder patch behind exact no-regression gates",
        "next_if_falsified": "preserve row-level negative; narrow discovery/admission or representation before any shipping integration",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-content-zip-matrix-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-content-zip-matrix.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"totals": result["totals"], "hypothesis": result["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
