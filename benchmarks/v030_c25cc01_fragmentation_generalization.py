from __future__ import annotations

"""Independent unseen generalization for the C25CC01 fragmentation-refined admission rule.

This campaign tests a specific research hypothesis: that physical fragmentation of the completed r24 candidate
(>=40 physical blob records and >=8 non-pack members on top of the original compact-control predicate) separates
C25CC01 cases with enough ZIP CPU margin from nearly-solid counterexamples.

A scientifically valid run may falsify that hypothesis.  Such a result is durable negative evidence, not a CI setup
failure and not permission to weaken the strict four-way release contract.  No workload identity is a policy input,
and this lane never changes the shipping selector or earns release credit.
"""

import argparse
import json
from pathlib import Path
import random
import shutil

from benchmarks import v030_c25cc01_fragmentation_admission_oracle as FRAG


def _bytes(seed: int, n: int) -> bytes:
    return random.Random(seed).randbytes(n)


def _write_fragmented_entropy(root: Path, *, seed: int, tiny_files: int, tiny_size: int, slab_files: int, slab_size: int, bulk_size: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "reservoir.dat").write_bytes(_bytes(seed, bulk_size))
    slabs = root / "segments"; slabs.mkdir()
    for i in range(slab_files):
        n = slab_size + ((i * 4093) % (64 * 1024))
        (slabs / f"segment-{i:03d}.dat").write_bytes(_bytes(seed + 50_000 + i * 6151, n))
    crumbs = root / "fragments"; crumbs.mkdir()
    for i in range(tiny_files):
        n = tiny_size + ((i * 53) % max(1, tiny_size // 2))
        (crumbs / f"fragment-{i:05d}.dat").write_bytes(_bytes(seed + 1_000_000 + i * 7919, n))


def _write_nearly_solid_entropy(root: Path, *, seed: int, files: int, tiny_size: int, bulk_size: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "bulk.dat").write_bytes(_bytes(seed, bulk_size))
    tiny = root / "tiny"; tiny.mkdir()
    for i in range(files):
        n = tiny_size + ((i * 29) % max(1, tiny_size // 3))
        (tiny / f"member-{i:05d}.dat").write_bytes(_bytes(seed + 2_000_000 + i * 3571, n))


def _write_compressible_fragmented(root: Path, *, seed: int, tiny_files: int, slab_files: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    repeated = (b"CMPCT-fragment-control-" * 8192)[:192 * 1024]
    slabs = root / "segments"; slabs.mkdir()
    for i in range(slab_files):
        prefix = _bytes(seed + i, 64)
        (slabs / f"segment-{i:03d}.dat").write_bytes(prefix + repeated)
    tiny = root / "tiny"; tiny.mkdir()
    common = (b"control-record\n" * 512)[:4096]
    for i in range(tiny_files):
        (tiny / f"member-{i:05d}.dat").write_bytes(common + bytes((i & 0xFF,)))


def _cases(root: Path) -> tuple[dict[str, Path], set[str], set[str]]:
    cases: dict[str, Path] = {}
    positive_specs = {
        "fragmented_entropy_a": dict(seed=27101, tiny_files=1280, tiny_size=3584, slab_files=48, slab_size=384 * 1024, bulk_size=4 * 1024 * 1024),
        "fragmented_entropy_b": dict(seed=38203, tiny_files=1460, tiny_size=2816, slab_files=56, slab_size=320 * 1024, bulk_size=6 * 1024 * 1024),
        "fragmented_entropy_c": dict(seed=49307, tiny_files=1080, tiny_size=4608, slab_files=44, slab_size=448 * 1024, bulk_size=3 * 1024 * 1024),
    }
    for name, kwargs in positive_specs.items():
        dst = root / name; _write_fragmented_entropy(dst, **kwargs); cases[name] = dst
    nearly_solid = root / "nearly_solid_entropy"
    _write_nearly_solid_entropy(nearly_solid, seed=60409, files=1450, tiny_size=3072, bulk_size=8 * 1024 * 1024)
    cases["nearly_solid_entropy"] = nearly_solid
    compressible = root / "compressible_fragmented"
    _write_compressible_fragmented(compressible, seed=71513, tiny_files=1250, slab_files=48)
    cases["compressible_fragmented"] = compressible
    return cases, set(positive_specs), {"nearly_solid_entropy", "compressible_fragmented"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    cases, expected_positive, expected_negative = _cases(args.work_root / "sources")
    rows = [FRAG._measure_case(f"independent/{name}", cases[name], args.work_root, compare=True) for name in sorted(cases)]
    by_name = {row["label"].split("/", 1)[1]: row for row in rows}
    admitted = [row for row in rows if row["refined_admitted"]]
    counterexamples = [row["label"] for row in admitted if row.get("strict_four_way_win") is not True]
    positive_green = {name for name in expected_positive if by_name[name]["refined_admitted"] is True and by_name[name].get("strict_four_way_win") is True}
    negative_rejected = {name for name in expected_negative if by_name[name]["refined_admitted"] is False}

    experiment_valid = (
        len(rows) == 5
        and all(row["payload_unchanged"] and row["two_control_copies"] for row in rows)
        and FRAG.MIN_PHYSICAL_BLOB_RECORDS == 40
        and FRAG.MIN_NON_PACK_MEMBERS == 8
    )
    hypothesis_supported = (
        len(positive_green) >= 2
        and not counterexamples
        and negative_rejected == expected_negative
    )
    gate = {
        "exact_case_count": len(rows) == 5,
        "integrity_preserved": all(row["payload_unchanged"] and row["two_control_copies"] for row in rows),
        "refined_constants_unchanged": FRAG.MIN_PHYSICAL_BLOB_RECORDS == 40 and FRAG.MIN_NON_PACK_MEMBERS == 8,
        "experiment_valid": bool(experiment_valid),
        "hypothesis_supported": bool(hypothesis_supported),
        "promotion_signal": bool(hypothesis_supported),
        "release_credit": False,
        "passed": bool(experiment_valid),
    }
    result = {
        "schema": "cmpct-v030-c25cc01-fragmentation-generalization-v2",
        "contract": {
            "base_predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "additional_candidate_inputs": ["physical_blob_records", "non_pack_members"],
            "min_physical_blob_records": FRAG.MIN_PHYSICAL_BLOB_RECORDS,
            "min_non_pack_members": FRAG.MIN_NON_PACK_MEMBERS,
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "minimum_independent_positive_admissions": 2,
            "selector_change": False,
            "release_credit": False,
        },
        "expected_positive": sorted(expected_positive),
        "expected_negative": sorted(expected_negative),
        "positive_green": sorted(positive_green),
        "counterexamples": counterexamples,
        "rows": rows,
        "gate": gate,
        "conclusion": (
            "fragmentation hypothesis supported" if hypothesis_supported else
            "fragmentation hypothesis falsified; preserve counterexamples and do not promote this rule"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"positive_green": result["positive_green"], "counterexamples": counterexamples, "gate": gate}, indent=2), flush=True)
    if not experiment_valid:
        raise SystemExit("C25CC01 fragmentation generalization experiment was invalid")


if __name__ == "__main__":
    main()
