from __future__ import annotations

"""Zero-group determinism ablation for locality-derived micro-packing.

The current-fingerprint 15-workload transfer found exactly one execution blocker:
resemblance-hostile deflate_family emitted zero locality-derived groups but the
independent and derived r24 artifacts were not byte-identical.  A zero-group
candidate has earned no right to change physical bytes.  This referee separates:

1. ordinary Builder nondeterminism;
2. LocalityDerivedBuilder nondeterminism;
3. a stable cross-builder semantic/physical difference despite zero groups;
4. host-owned metadata as the source of any difference (reproducible-mode control).

Research-only.  No canonical policy is changed.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from benchmarks import resemblance_hostile_corpus_v1 as RESEMBLANCE
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from cmpct import builder as BUILDER
from experiments import entropygraph_v030_release_product as PRODUCT


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_byte_diff(a: bytes, b: bytes) -> int | None:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else None


def _first_value_diff(a: Any, b: Any, path: str = "$") -> dict | None:
    if type(a) is not type(b):
        return {"path": path, "kind": "type", "a": type(a).__name__, "b": type(b).__name__}
    if isinstance(a, dict):
        ka = sorted(a)
        kb = sorted(b)
        if ka != kb:
            return {"path": path, "kind": "keys", "a": [str(x) for x in ka], "b": [str(x) for x in kb]}
        for key in ka:
            d = _first_value_diff(a[key], b[key], f"{path}.{key}")
            if d is not None:
                return d
        return None
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return {"path": path, "kind": "length", "a": len(a), "b": len(b)}
        for i, (av, bv) in enumerate(zip(a, b)):
            d = _first_value_diff(av, bv, f"{path}[{i}]")
            if d is not None:
                return d
        return None
    if a != b:
        def safe(v: Any) -> Any:
            if isinstance(v, bytes):
                return {"bytes_len": len(v), "sha256": hashlib.sha256(v).hexdigest()}
            return v
        return {"path": path, "kind": "value", "a": safe(a), "b": safe(b)}
    return None


def _build(source: Path, out: Path, *, derived: bool, reproducible: bool) -> dict:
    cls = BASE.LocalityDerivedBuilder if derived else BUILDER.Builder
    builder = cls(
        source,
        deflate_reuse_min=0,
        workers=1,
        reproducible=reproducible,
        reproducible_epoch_ns=0,
    )
    if derived:
        builder.micro_pack_max_file = PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES
    else:
        builder.micro_pack_max_file = 0
    stats = BASE._build_with(builder, out)
    index, data = BASE._parse_r24(out)
    verify = PRODUCT.strong_verify(out)
    groups = list(getattr(builder, "_locality_derived_groups", []))
    return {
        "path": str(out),
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "data_bytes": len(data),
        "data_sha256": hashlib.sha256(data).hexdigest(),
        "index": index,
        "data": data,
        "strong_tree_exact": bool(verify.get("ok")),
        "tree_sha256": verify.get("tree_sha256"),
        "group_count": len(groups),
        "group_members": sum(int(g["members"]) for g in groups),
        "build_cpu_s": float(stats["build_cpu_s"]),
        "build_wall_s": float(stats["build_wall_s"]),
    }


def _compare(a: dict, b: dict) -> dict:
    ba = Path(a["path"]).read_bytes()
    bb = Path(b["path"]).read_bytes()
    return {
        "archive_equal": ba == bb,
        "archive_delta_bytes": len(bb) - len(ba),
        "first_byte_diff": _first_byte_diff(ba, bb),
        "index_equal": a["index"] == b["index"],
        "first_index_diff": _first_value_diff(a["index"], b["index"]),
        "data_equal": a["data"] == b["data"],
        "first_data_diff": _first_byte_diff(a["data"], b["data"]),
        "tree_equal": a["tree_sha256"] == b["tree_sha256"],
        "a_sha256": a["archive_sha256"],
        "b_sha256": b["archive_sha256"],
    }


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in {"index", "data", "path"}}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus_root = work_root / "corpus"
    manifest = RESEMBLANCE.build(corpus_root)
    source = corpus_root / "04_deflate_family"
    ident = next(r for r in manifest["workloads"] if r["name"] == "04_deflate_family")

    builds: dict[str, dict] = {}
    for mode, derived, reproducible in (
        ("independent_a", False, False),
        ("independent_b", False, False),
        ("derived_a", True, False),
        ("derived_b", True, False),
        ("independent_repro", False, True),
        ("derived_repro", True, True),
    ):
        builds[mode] = _build(source, work_root / f"{mode}.cmpct", derived=derived, reproducible=reproducible)

    comparisons = {
        "independent_repeat": _compare(builds["independent_a"], builds["independent_b"]),
        "derived_repeat": _compare(builds["derived_a"], builds["derived_b"]),
        "cross_default": _compare(builds["independent_a"], builds["derived_a"]),
        "cross_reproducible": _compare(builds["independent_repro"], builds["derived_repro"]),
    }

    zero_groups = builds["derived_a"]["group_count"] == 0 and builds["derived_repro"]["group_count"] == 0
    exact_trees = all(bool(r["strong_tree_exact"]) for r in builds.values())
    same_tree = len({str(r["tree_sha256"]) for r in builds.values()}) == 1

    if not zero_groups or not exact_trees or not same_tree:
        verdict = "ZERO_GROUP_MECHANISM_INVARIANT_FAILURE"
    elif not comparisons["independent_repeat"]["archive_equal"] or not comparisons["derived_repeat"]["archive_equal"]:
        verdict = "BASE_OR_DERIVED_BUILD_NONDETERMINISTIC"
    elif comparisons["cross_reproducible"]["archive_equal"] and not comparisons["cross_default"]["archive_equal"]:
        verdict = "ZERO_GROUP_DIFF_HOST_METADATA_ONLY"
    elif not comparisons["cross_default"]["archive_equal"]:
        verdict = "ZERO_GROUP_DERIVED_SIDE_EFFECT"
    else:
        verdict = "ZERO_GROUP_NOOP_CONFIRMED"

    return {
        "schema": "cmpct-v030-r24-zero-group-determinism-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "workload_identity": {
            "name": ident["name"],
            "files": int(ident["files"]),
            "logical_bytes": int(ident["logical_bytes"]),
            "tree_sha256": str(ident["tree_sha256"]),
        },
        "builds": {k: _public(v) for k, v in builds.items()},
        "comparisons": comparisons,
        "zero_groups": zero_groups,
        "all_strong_tree_exact": exact_trees,
        "same_tree": same_tree,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zero-group-determinism-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zero-group-determinism.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
