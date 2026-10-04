from __future__ import annotations

"""Prove compact-control composition against the *current shipping* r24 product.

Shipping v0.30 now performs post-selection dead-dictionary elision.  The older compact-control
research independently showed that two authenticated r24 index copies contain avoidable path/stat/
size framing while leaving physical payload records untouched.  This oracle answers the only useful
question before productizing a new compact-control profile: do those two independent savings compose
on today's product, and do they do so without a single projected byte regression across the frozen
15-workload corpus?

The oracle does not emit release bytes and cannot authorize promotion.  It rebuilds genuine current
shipping r24 for every workload, strongly verifies it, round-trips the compact index back to the exact
shipping index, and prices two compact authenticated control copies while preserving the complete
shipping payload span.  For encrypted-like it additionally remeasures ZIP/Deflate-9 and solid
Zstd-19 in rotated rounds and requires the conservative creation boundary (shipping r24 build +
strong verify + post-build transform) to beat both competitors before reporting four-way potential.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CC
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 5
TARGET = "07_incompressible_and_encrypted_like"


def _build_all(root: Path) -> dict[str, Path]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    # Use the same frozen 15-workload builder as release performance evidence rather than spelling
    # workload names here.  The import is intentionally local because the benchmark module is heavy.
    from benchmarks import v030_release_performance as PERF

    built = PERF._build_corpora(root)
    return {name: path for (_family, name), path in built.items()}


def _shipping_r24(source: Path, archive: Path) -> dict:
    stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    compact = CC._compact_once(archive)
    if not compact["semantic_index_roundtrip_exact"]:
        raise RuntimeError("compact-control semantic roundtrip failed")
    return {
        "shipping_bytes": int(archive.stat().st_size),
        "projected_bytes": int(compact["projected_two_copy_archive_bytes"]),
        "saving_bytes": int(archive.stat().st_size) - int(compact["projected_two_copy_archive_bytes"]),
        "tree_sha256": verified.get("tree_sha256"),
        "dead_dictionary_elision": stats.get("r24_dead_dictionary_elision"),
        "dead_dictionary_saving_bytes": int(stats.get("r24_dead_dictionary_saving_bytes", 0)),
        "compact_index_comp_bytes_per_copy": int(compact["compact_index_comp_bytes_per_copy"]),
        "shipping_index_comp_bytes_per_copy": int(compact["index_comp_bytes_per_copy"]),
        "compact_transform_s": float(compact["compact_transform_s"]),
        "payload_records_unchanged": bool(compact["physical_payload_records_unchanged"]),
        "two_control_copies": bool(compact["two_authenticated_control_copies_retained"]),
    }


def _all15(work_root: Path) -> dict:
    roots = _build_all(work_root / "corpus")
    rows = []
    aggregate_shipping = 0
    aggregate_projected = 0
    improved = 0
    regressions = []
    for name in sorted(roots):
        out = work_root / "all15" / f"{name}.cmpct"
        out.parent.mkdir(parents=True, exist_ok=True)
        row = _shipping_r24(roots[name], out)
        row["workload"] = name
        aggregate_shipping += row["shipping_bytes"]
        aggregate_projected += row["projected_bytes"]
        if row["projected_bytes"] < row["shipping_bytes"]:
            improved += 1
        elif row["projected_bytes"] > row["shipping_bytes"]:
            regressions.append(name)
        rows.append(row)
    return {
        "rows": rows,
        "workloads": len(rows),
        "aggregate_shipping_bytes": aggregate_shipping,
        "aggregate_projected_bytes": aggregate_projected,
        "aggregate_saving_bytes": aggregate_shipping - aggregate_projected,
        "improved_workloads": improved,
        "regressions": regressions,
        "zero_projected_byte_regressions": not regressions,
        "all_semantics_preserved": all(r["payload_records_unchanged"] and r["two_control_copies"] for r in rows),
    }


def _target(work_root: Path) -> dict:
    target_root = work_root / "target-corpus"
    shutil.rmtree(target_root, ignore_errors=True)
    target_root.mkdir(parents=True)
    NEUTRAL.corpus_incompressible(target_root)
    source = target_root / TARGET
    samples = []
    for rep in range(ROUNDS):
        order = ["cmpct", "zip", "zstd"]
        order = order[rep % 3 :] + order[: rep % 3]
        current = {}
        for name in order:
            if name == "cmpct":
                out = work_root / "target" / f"r{rep}.cmpct"
                out.parent.mkdir(parents=True, exist_ok=True)
                import time

                started = time.perf_counter()
                row = _shipping_r24(source, out)
                base_elapsed = time.perf_counter() - started
                current[name] = {
                    **row,
                    # _shipping_r24 includes the post-build compact transform after strong verification.
                    # This deliberately overcharges a future integrated writer.
                    "conservative_create_s": base_elapsed,
                }
            elif name == "zip":
                current[name] = EXT._zip(
                    source,
                    work_root / "target" / f"r{rep}.zip",
                    work_root / "target" / f"zip-out-{rep}",
                )
            else:
                zw = work_root / "target" / f"zstd-work-{rep}"
                zw.mkdir(parents=True, exist_ok=True)
                current[name] = EXT._tar_zstd(
                    source,
                    work_root / "target" / f"r{rep}.tar.zst",
                    work_root / "target" / f"zstd-out-{rep}",
                    zw,
                )
        samples.append(current)

    projected = {int(s["cmpct"]["projected_bytes"]) for s in samples}
    shipping = {int(s["cmpct"]["shipping_bytes"]) for s in samples}
    zip_sizes = {int(s["zip"]["archive_bytes"]) for s in samples}
    zstd_sizes = {int(s["zstd"]["archive_bytes"]) for s in samples}
    projected_bytes = next(iter(projected))
    zip_bytes = next(iter(zip_sizes))
    zstd_bytes = next(iter(zstd_sizes))
    cmpct_s = statistics.median(float(s["cmpct"]["conservative_create_s"]) for s in samples)
    zip_s = statistics.median(float(s["zip"]["create_s"]) for s in samples)
    zstd_s = statistics.median(float(s["zstd"]["create_s"]) for s in samples)
    return {
        "rounds": ROUNDS,
        "shipping_size_deterministic": len(shipping) == 1,
        "projected_size_deterministic": len(projected) == 1,
        "competitor_sizes_deterministic": len(zip_sizes) == 1 and len(zstd_sizes) == 1,
        "shipping_bytes": next(iter(shipping)),
        "projected_bytes": projected_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "median_conservative_cmpct_create_s": cmpct_s,
        "median_zip_create_s": zip_s,
        "median_zstd19_create_s": zstd_s,
        "smaller_than_zip": projected_bytes < zip_bytes,
        "smaller_than_zstd19": projected_bytes < zstd_bytes,
        "faster_than_zip": cmpct_s < zip_s,
        "faster_than_zstd19": cmpct_s < zstd_s,
        "strict_four_way_potential": projected_bytes < zip_bytes and projected_bytes < zstd_bytes and cmpct_s < zip_s and cmpct_s < zstd_s,
        "dead_dictionary_elision_observed": any(int(s["cmpct"]["dead_dictionary_saving_bytes"]) > 0 for s in samples),
        "compact_control_saving_bytes": next(iter(shipping)) - projected_bytes,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    all15 = _all15(work_root)
    target = _target(work_root)
    gate = {
        "all_15_workloads_executed": all15["workloads"] == 15,
        "zero_projected_byte_regressions": all15["zero_projected_byte_regressions"],
        "all_semantics_preserved": all15["all_semantics_preserved"],
        "strict_improvement_exists": all15["improved_workloads"] > 0,
        "encrypted_like_dead_dictionary_elision_observed": target["dead_dictionary_elision_observed"],
        "encrypted_like_compact_control_adds_saving": target["compact_control_saving_bytes"] > 0,
        "encrypted_like_strict_four_way_potential": target["strict_four_way_potential"],
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-r24-compact-control-composition-v1",
        "all15": all15,
        "encrypted_like": target,
        "gate": gate,
        "claim_boundary": (
            "Research-only composition proof. Projected compact-control bytes are not canonical r24 and cannot "
            "satisfy release authority. A green result only authorizes building a bounded canonical compact-control "
            "profile with reader/recovery/native/Android parity and then rerunning the ordinary 15-workload gate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control-composition-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control-composition.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all15": {k: v for k, v in result["all15"].items() if k != "rows"}, "encrypted_like": result["encrypted_like"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("r24 compact-control composition did not earn productization")


if __name__ == "__main__":
    main()
