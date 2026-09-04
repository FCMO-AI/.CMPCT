from __future__ import annotations

"""Research-only byte ownership decomposition for the encrypted-like semantic root.

Two exact experiments already killed the current locality-safe physical family and the combined
salvage-header + distributed-blob-table family. This oracle does not try another metadata tweak.
It identifies which *remaining semantic facts* dominate the authenticated root so the next design
can move the right ownership boundary into locality-scoped physical groups instead of guessing.

For each compact-root field, the oracle measures its standalone MessagePack size and the compressed
root delta when that field is replaced by its neutral empty value. Ablations are diagnostic only;
they are intentionally not valid archives. The complete unmodified compact root is still expanded
and checked byte-semantically against the source index.
"""

import argparse
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"
NEUTRAL = {"p": [], "d": [0, 0], "f": [], "b": [], "r": [], "z": None, "m": {}}


def _compressed(root: dict, features: list) -> tuple[int, int, int]:
    envelope = {"x": features, "c": root}
    raw = msgpack.packb(envelope, use_bin_type=True)
    level, comp = PROFILE._compress_control(raw)
    return len(raw), len(comp), int(level)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)
    candidate = work_root / "cmpct" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError("locality-safe strategy unexpectedly ineligible")

    index, _data, _physical = PROFILE._source_r24_parts(candidate)
    compact = CONTROL._compact_index(index)
    expanded = CONTROL._expand_index(compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("baseline compact semantic root does not roundtrip exactly")

    baseline_raw, baseline_comp, baseline_level = _compressed(compact, list(index["features"]))
    fields = []
    for key in ("p", "d", "f", "b", "r", "z", "m"):
        standalone_raw = len(msgpack.packb(compact[key], use_bin_type=True))
        ablated = dict(compact)
        ablated[key] = NEUTRAL[key]
        ablated_raw, ablated_comp, ablated_level = _compressed(ablated, list(index["features"]))
        fields.append({
            "field": key,
            "standalone_msgpack_bytes": standalone_raw,
            "ablated_root_raw_bytes": ablated_raw,
            "ablated_root_compressed_bytes": ablated_comp,
            "compressed_marginal_bytes": baseline_comp - ablated_comp,
            "ablated_level": ablated_level,
        })

    fields.sort(key=lambda x: (-int(x["compressed_marginal_bytes"]), x["field"]))
    return {
        "schema": "cmpct-v030-c25cc01-semantic-root-ablation-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "tree_sha256": row["tree_sha256"],
        "locality": row["locality"],
        "baseline": {
            "raw_bytes": baseline_raw,
            "compressed_bytes": baseline_comp,
            "level": baseline_level,
            "exact_semantic_roundtrip": True,
        },
        "fields_by_compressed_marginal": fields,
        "dominant_field": fields[0]["field"] if fields else None,
        "dominant_field_compressed_marginal_bytes": fields[0]["compressed_marginal_bytes"] if fields else 0,
        "gate": {
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Diagnostic semantic-root byte attribution only. Ablated roots are not archives and are not claimed "
            "decodable. The result selects which ownership boundary deserves the next locality-safe physical-grammar "
            "experiment; it grants no selector or release credit."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-root-ablation-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-root-ablation.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
