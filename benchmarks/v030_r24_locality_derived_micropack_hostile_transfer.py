from __future__ import annotations

"""Hostile transfer referee for the locality-derived r24 micro-pack mechanism.

Mission: docs/V030_R24_LOCALITY_DERIVED_MICROPACK_HOSTILE_TRANSFER_2026-09-12.md
Research-only. The exact parent LocalityDerivedBuilder is reused unchanged.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_locality_derived_micropack_referee as BASE


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _deterministic_bytes(label: str, size: int) -> bytes:
    out = bytearray()
    counter = 0
    seed = label.encode("utf-8")
    while len(out) < size:
        out.extend(hashlib.sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:size])


def _structured(label: str, size: int) -> bytes:
    lines = []
    i = 0
    total = 0
    while total < size:
        line = (
            f'{{"kind":"record","family":"{label}","index":{i},'
            f'"enabled":{str(i % 3 != 0).lower()},"value":"item-{i % 17:02d}"}}\n'
        ).encode("utf-8")
        lines.append(line)
        total += len(line)
        i += 1
    return b"".join(lines)[:size]


def _build_corpora(root: Path) -> dict[str, Path]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    families: dict[str, Path] = {}

    balanced = root / "balanced_structured_text"
    for i in range(72):
        size = 768 + (i % 8) * 192
        _write(balanced / f"records_{i:03d}.txt", _structured(f"balanced-{i % 5}", size))
    families[balanced.name] = balanced

    skewed = root / "skewed_structured_text"
    sizes = [128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096, 6144, 8192]
    for i in range(78):
        size = sizes[i % len(sizes)]
        _write(skewed / f"shard_{i:03d}.txt", _structured(f"skewed-{i % 9}", size))
    families[skewed.name] = skewed

    incompressible = root / "incompressible_text_labeled"
    sizes = [256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096]
    for i in range(72):
        size = sizes[i % len(sizes)]
        _write(incompressible / f"noise_{i:03d}.txt", _deterministic_bytes(f"noise-{i}", size))
    families[incompressible.name] = incompressible

    dup = root / "duplicate_forest"
    roots = [_structured(f"duplicate-root-{j}", 512 + j * 128) for j in range(8)]
    for i in range(96):
        _write(dup / f"copy_{i:03d}.txt", roots[i % len(roots)])
    for i in range(16):
        _write(dup / f"unique_{i:03d}.txt", _structured(f"unique-{i}", 640 + i * 37))
    families[dup.name] = dup

    single = root / "singleton_buckets"
    singleton_rows = [
        ("only.txt", "txt"),
        ("only.md", "md"),
        ("only.json", "json"),
        ("only.py", "py"),
        ("only.yaml", "yaml"),
        ("only.toml", "toml"),
    ]
    for i, (name, label) in enumerate(singleton_rows):
        _write(single / name, _structured(label, 900 + i * 113))
    families[single.name] = single

    return families


def _one(source: Path, work: Path) -> dict:
    rows = BASE._build_variants(source, work)
    independent = rows["independent_r24"]
    derived = rows["derived_r24"]
    cc = rows["derived_c25cc01"]
    candidate = rows["derived_membership"]

    groups = list(derived.get("derived_groups", []))
    group_count = len(groups)
    group_members = sum(int(g["members"]) for g in groups)
    candidate_vs_independent = int(candidate["archive_bytes"]) - int(independent["archive_bytes"])
    candidate_vs_cc = int(candidate["archive_bytes"]) - int(cc["archive_bytes"])
    hostile_applicable = group_count > 0
    hostile_table = dict(candidate.get("hostile_fail_closed", {}))
    hostile_ok = bool(candidate.get("hostile_all_pass")) if hostile_applicable else True

    invariants = {
        "derived_locality_pass": bool(derived["locality"]["locality_pass"]),
        "derived_strong_tree_exact": bool(derived["strong_tree_exact"]),
        "independent_strong_tree_exact": bool(independent["strong_tree_exact"]),
        "candidate_strong_tree_exact": bool(candidate["strong_tree_exact"]),
        "candidate_payload_unchanged": bool(candidate["physical_payload_unchanged"]),
        "candidate_tail_recovery": bool(candidate["primary_corruption_tail_recovery"]),
        "candidate_hostile_fail_closed_when_applicable": hostile_ok,
    }

    return {
        "independent_r24_bytes": int(independent["archive_bytes"]),
        "derived_r24_bytes": int(derived["archive_bytes"]),
        "derived_c25cc01_bytes": int(cc["archive_bytes"]),
        "candidate_bytes": int(candidate["archive_bytes"]),
        "candidate_delta_vs_independent_bytes": candidate_vs_independent,
        "candidate_delta_vs_c25cc01_bytes": candidate_vs_cc,
        "derived_delta_vs_independent_bytes": int(derived["archive_bytes"]) - int(independent["archive_bytes"]),
        "derived_group_count": group_count,
        "derived_group_members": group_members,
        "max_member_amplification": float(derived["locality"]["max_member_amplification"]),
        "weighted_member_amplification": float(derived["locality"]["weighted_member_amplification"]),
        "max_decode_unit_bytes": int(derived["locality"]["max_decode_unit_bytes"]),
        "independent_build_cpu_s": float(independent["build_cpu_s"]),
        "independent_build_wall_s": float(independent["build_wall_s"]),
        "derived_build_cpu_s": float(derived["build_cpu_s"]),
        "derived_build_wall_s": float(derived["build_wall_s"]),
        "candidate_open_expand_cpu_s": float(candidate["median_open_expand_cpu_s"]),
        "candidate_open_expand_wall_s": float(candidate["median_open_expand_wall_s"]),
        "hostile_applicable": hostile_applicable,
        "hostile_fail_closed": hostile_table,
        "invariants": invariants,
        "invariants_pass": all(invariants.values()),
        "candidate_no_larger_than_independent": candidate_vs_independent <= 0,
        "candidate_strictly_smaller_than_independent": candidate_vs_independent < 0,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpora = _build_corpora(work_root / "corpora")
    rows = {
        name: _one(path, work_root / "work" / name)
        for name, path in corpora.items()
    }

    invariant_failures = [name for name, row in rows.items() if not row["invariants_pass"]]
    economic_losses = [
        name for name, row in rows.items()
        if row["candidate_delta_vs_independent_bytes"] > 0
    ]
    strict_transfer_wins = [
        name for name, row in rows.items()
        if row["derived_group_count"] > 0 and row["candidate_strictly_smaller_than_independent"]
    ]

    if invariant_failures:
        verdict = "RETIRE_LOCALITY_DERIVED_MICROPACK_TRANSFER"
    elif economic_losses:
        verdict = "LOCALITY_DERIVED_MICROPACK_NEEDS_ECONOMIC_ADMISSION"
    elif strict_transfer_wins:
        verdict = "LOCALITY_DERIVED_MICROPACK_GENERALIZES"
    else:
        verdict = "LOCALITY_DERIVED_MICROPACK_NEEDS_ECONOMIC_ADMISSION"

    return {
        "schema": "cmpct-v030-r24-locality-derived-micropack-hostile-transfer-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "locality_budget": BASE.LOCALITY_BUDGET,
        "families": rows,
        "invariant_failures": invariant_failures,
        "economic_losses": economic_losses,
        "strict_transfer_wins": strict_transfer_wins,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-locality-derived-micropack-hostile-work"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-locality-derived-micropack-hostile.json"),
    )
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    summary = {
        "verdict": result["verdict"],
        "invariant_failures": result["invariant_failures"],
        "economic_losses": result["economic_losses"],
        "strict_transfer_wins": result["strict_transfer_wins"],
        "deltas_vs_independent": {
            name: row["candidate_delta_vs_independent_bytes"]
            for name, row in result["families"].items()
        },
        "hostile_fail_closed": {
            name: row["hostile_fail_closed"]
            for name, row in result["families"].items()
            if row["hostile_applicable"]
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
