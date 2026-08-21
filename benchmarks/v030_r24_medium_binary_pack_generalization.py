from __future__ import annotations

"""Full frozen-suite A/B ratchet for the promoted r24 medium-binary S_PACK policy.

The focused promotion oracle proved strict size+complete-create wins on two hostile binary families and a byte
improvement on its negative control. This gate answers the broader release question: does extending the existing
r24 S_PACK encoder to <=256 KiB .bin/text-like members regress *any* frozen workload compared with the immediately
preceding shipping r24-v3 policy?

It does not compare research grammars and cannot authorize release. Both sides are canonical revision-24 bytes,
both are strongly verified, and every repaired/frozen workload must retain the same logical tree. Promotion is
fail-closed: a single larger candidate row is a red, even if aggregate bytes improve.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as P

OLD_MAX = 32 * 1024
NEW_MAX = 256 * 1024


def _build(root: Path, out: Path, *, promoted: bool) -> dict:
    old_max = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    old_medium = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
    try:
        P.R24_RELEASE_MICRO_MAX_FILE_BYTES = NEW_MAX if promoted else OLD_MAX
        P._R24_CDC_POLICY.medium_binary_pack = bool(promoted)
        stats = dict(P._locality_bounded_r24_build(root, out))
    finally:
        P.R24_RELEASE_MICRO_MAX_FILE_BYTES = old_max
        P._R24_CDC_POLICY.medium_binary_pack = old_medium
    verified = P.strong_verify(out)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 verification failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "tree_sha256": verified["tree_sha256"],
        "format_revision": int(verified["format_revision"]),
        "micro_pack_max_file_bytes": NEW_MAX if promoted else OLD_MAX,
        "medium_binary_pack": bool(promoted),
        "build_stats": stats,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_packgen_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_packgen_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_packgen_repair")
    repair.install_generation_hooks(neutral)

    roots = (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    )
    rows = []
    for suite, builder, root in roots:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = accepted[key]["tree_sha256"]
            with tempfile.TemporaryDirectory(prefix="cmpct-v030-packgen-", dir=work_root) as td:
                td_path = Path(td)
                baseline = _build(workload, td_path / "r24-v3.cmpct", promoted=False)
                candidate = _build(workload, td_path / "r24-v4.cmpct", promoted=True)
            same_tree = baseline["tree_sha256"] == candidate["tree_sha256"]
            # The accepted-v0.29 tree hash is a historical regular-file identity domain, whereas strong_verify
            # reports the canonical user-tree identity. Source continuity is already enforced by the frozen
            # generalization loader; here we compare the two canonical r24 artifacts directly.
            delta = int(candidate["archive_bytes"]) - int(baseline["archive_bytes"])
            row = {
                "suite": suite,
                "name": workload.name,
                "label": f"{suite}/{workload.name}",
                "frozen_source_tree_sha256": expected,
                "baseline": baseline,
                "candidate": candidate,
                "same_verified_tree": same_tree,
                "candidate_delta_bytes": delta,
                "no_byte_regression": delta <= 0,
            }
            rows.append(row)
            print(json.dumps({"label": row["label"], "delta": delta, "no_regression": delta <= 0}, separators=(",", ":")), flush=True)

    baseline_total = sum(int(row["baseline"]["archive_bytes"]) for row in rows)
    candidate_total = sum(int(row["candidate"]["archive_bytes"]) for row in rows)
    gate = {
        "exact_workload_count": len(rows) == 15,
        "all_verified_tree_equal": all(row["same_verified_tree"] for row in rows),
        "zero_r24_byte_regressions": all(row["no_byte_regression"] for row in rows),
        "aggregate_no_regression": candidate_total <= baseline_total,
        "at_least_one_material_improvement": any(row["candidate_delta_bytes"] < 0 for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-r24-medium-binary-pack-generalization-v1",
        "contract": {
            "workloads": 15,
            "baseline": "shipping r24-v3: 32 KiB micro-pack max; mature text hints only",
            "candidate": "shipping r24-v4: 256 KiB micro-pack max; thread-local .bin admission",
            "grammar": "canonical revision-24 S_PACK on both sides",
            "row_rule": "candidate archive bytes <= baseline archive bytes on every frozen workload",
        },
        "rows": rows,
        "totals": {
            "baseline_bytes": baseline_total,
            "candidate_bytes": candidate_total,
            "saving_bytes": baseline_total - candidate_total,
            "regressed_rows": sum(not row["no_byte_regression"] for row in rows),
            "improved_rows": sum(row["candidate_delta_bytes"] < 0 for row in rows),
        },
        "gate": gate,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack-generalization-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack-generalization.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("promoted medium-binary r24 policy regressed the frozen suite")


if __name__ == "__main__":
    main()
