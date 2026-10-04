from __future__ import annotations

"""Shipping regression ratchet for the promoted r24 dead-dictionary post-pass.

v1/v2 were promotion evidence: build the then-shipping pre-elision r24 archive and apply the candidate transform.
After promotion, repeating that experiment through the public shipping builder applies the transform twice and must
naturally report zero further savings.  This v3 ratchet instead compares the preserved pre-elision semantic owner
(`P._BASE_R24_BUILD`) against today's shipping r24 wrapper, while retaining the exact v2 all-15 identity repair.

The comparison is evidence only.  Training and codec competition remain untouched, live-dictionary archives must
stay byte-identical, and ordinary external/generalization/final authorities remain decisive.
"""

import argparse
import json
import time
from pathlib import Path

from benchmarks import v030_r24_binary_dictionary_isolation_oracle as PRIOR
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from benchmarks import v030_r24_dead_dictionary_elision_oracle_v2 as V2
from experiments import entropygraph_v030_release_product as P


def _pre_elision_build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = dict(P._BASE_R24_BUILD(root, out))
    build_s = time.perf_counter() - started
    verify_started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - verify_started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"pre-elision r24 verification failed: {verified!r}")
    index, physical = CONTROL._read_index(out)
    return {
        "archive_bytes": int(physical["archive_bytes"]),
        "tree_sha256": verified["tree_sha256"],
        "complete_create_s": build_s + verify_s,
        "build_s": build_s,
        "verify_s": verify_s,
        "dict_blob_present": index.get("dict_blob") is not None,
        "unique_blobs": int(stats["unique_blobs"]),
    }


def _rename_promoted_domains(result: dict) -> dict:
    result = dict(result)
    result["schema"] = "cmpct-v030-r24-dead-dictionary-elision-v3-shipping-ratchet"
    result["ratchet"] = {
        "pre_elision_owner": "entropygraph_v030_release_product._BASE_R24_BUILD",
        "shipping_owner": "entropygraph_v030_release_product._locality_bounded_r24_build",
        "promotion_already_applied": True,
        "training_changed": False,
        "codec_competition_changed": False,
        "threshold_changed": False,
    }

    target = dict(result["target"])
    target["shipping_bytes"] = int(target.pop("candidate_bytes"))
    target["saving_bytes_vs_pre_elision"] = -int(target["delta_bytes"])
    target["shipping_dead_dictionary_elided"] = bool(target.pop("dead_dictionary_elided"))
    result["target"] = target

    all15 = dict(result["all15"])
    renamed = []
    for original in all15["rows"]:
        row = dict(original)
        row["pre_elision_bytes"] = int(row.pop("shipping_bytes"))
        row["shipping_bytes"] = int(row.pop("candidate_bytes"))
        row["pre_elision_tree_sha256"] = row.pop("shipping_tree_sha256")
        row["shipping_tree_sha256"] = row.pop("candidate_tree_sha256")
        row["saving_bytes_vs_pre_elision"] = -int(row["delta_bytes"])
        renamed.append(row)
    all15["rows"] = renamed
    all15["pre_elision_total_bytes"] = int(all15.pop("shipping_total_bytes"))
    all15["shipping_total_bytes"] = int(all15.pop("candidate_total_bytes"))
    gate = dict(all15["gate"])
    gate.pop("promotion_candidate", None)
    gate["shipping_regression_green"] = all(
        gate[key]
        for key in (
            "exact_workload_count",
            "canonical_shipping_candidate_tree_identity",
            "historical_source_digest_not_misused_as_product_digest",
            "zero_byte_regressions",
            "at_least_one_strict_improvement",
            "live_dictionaries_unchanged",
        )
    )
    all15["gate"] = gate
    result["all15"] = all15
    result["contract"] = {
        **result["contract"],
        "release_effect": "shipping regression ratchet; ordinary exact-head authorities remain decisive",
    }
    return result


def run(work_root: Path) -> dict:
    original = PRIOR._shipping_build
    PRIOR._shipping_build = _pre_elision_build
    try:
        return _rename_promoted_domains(V2.run(work_root))
    finally:
        PRIOR._shipping_build = original


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-dead-dict-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-dead-dict.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    all15 = result["all15"]
    print(
        json.dumps(
            {
                "target": result["target"],
                "gate": all15["gate"],
                "saving_total": all15["pre_elision_total_bytes"] - all15["shipping_total_bytes"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
