#!/usr/bin/env python3
"""O34b: one-row retrospective product-byte attribution, not a promotion rerun.

This instrument isolates the hostile tiny-files fixture that independently falsified the
frozen compact-r24 promotion gate in O34.  It measures genuine r24, unchanged shipping
v0.30 and frozen compact candidate on ONE identical source tree in separate processes.
It cannot change the O34 verdict, and neither a green nor a losing result grants release
credit. Frozen corpus/candidate/comparator/evaluator sources are never edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

SUITE = "neutral_hostile_v1"
NAME = "08_many_tiny_files"
SOURCE = "b878f40a540162ab977776d7f90c3502d2749588"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prepare_one_exact_workload(root: Path) -> dict:
    # Import the authentic frozen experiment's corpus-source and repair functions.
    # This is NOT a new synthetic shortcut or a replacement workload.
    from benchmarks import v030_release_ablation_canonical as bench
    general = bench.GENERAL
    neutral = general.V029._load(
        general.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_o34b_exact_neutral",
    )
    repair = general.V029._load(
        general.V029.REPAIR_PATH, "cmpct_o34b_exact_repair",
    )
    repair.install_generation_hooks(neutral)
    root.mkdir(parents=True, exist_ok=True)
    neutral.corpus_tinyfiles(root)
    repair.normalize_root(root)

    workload = root / NAME
    expected = general._accepted_v029_rows()[(SUITE, NAME)]["tree_sha256"]
    actual = general._historical_treehash(workload)
    if actual != expected:
        raise RuntimeError(
            f"INVALID SOURCE CUSTODY: {SUITE}/{NAME} independent one-row "
            f"tree {actual} != frozen historical {expected}"
        )
    files = [p for p in workload.rglob("*") if p.is_file()]
    return {
        "suite": SUITE,
        "name": NAME,
        "historical_tree_sha256": actual,
        "accepted_historical_tree_sha256": expected,
        "regular_files": len(files),
        "logical_bytes": sum(p.stat().st_size for p in files),
    }


def _child(mode: str, workload: Path, archive: Path, result: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if mode == "genuine_r24":
        from cmpct.builder import Builder
        from cmpct.reader import CMPCT
        Builder(workload).build(archive)
        with CMPCT(archive) as reader:
            verified_count = reader.verify()
        ok = verified_count >= 0
        metadata = {"selected": "genuine-r24-builder", "format_revision": 24}
    else:
        # Separate *fresh* processes are vital. Candidate import deliberately patches
        # shared product-module globals, which would contaminate an in-process A/B.
        if mode == "shipping_v030":
            from experiments import entropygraph_v030_release_product as product
        elif mode == "frozen_compact":
            from experiments import entropygraph_v030_release_product_compact_r24 as product
        else:
            raise ValueError(mode)
        stats = dict(product.build(workload, archive))
        verified = dict(product.strong_verify(archive))
        ok = bool(verified.get("ok"))
        expected_semantic_tree = product.treehash(workload)
        if int(stats.get("format_revision", -1)) == 25:
            ok = ok and verified.get("tree_sha256") == expected_semantic_tree
        metadata = {
            "selected": str(stats.get("selected")),
            "format_revision": stats.get("format_revision"),
            "format_profile": stats.get("format_profile"),
            "r24_product_bytes": stats.get("r24_product_bytes"),
            "r25_product_bytes": stats.get("r25_product_bytes"),
            "r25_strictly_smaller_than_r24": stats.get("r25_strictly_smaller_than_r24"),
            "semantic_tree_sha256": expected_semantic_tree,
            "verifier_tree_sha256": verified.get("tree_sha256"),
        }
    if not ok:
        raise RuntimeError(f"{mode}: strong verification failed")
    row = {
        "mode": mode,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "verified": True,
        "elapsed_wall_s_one_observation_uncontrolled": time.perf_counter() - t0,
        **metadata,
    }
    result.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True), flush=True)


def _parent(work_root: Path, output: Path) -> None:
    import shutil
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = work_root / "source"
    input_identity = _prepare_one_exact_workload(source)
    workload = source / NAME

    rows = {}
    for mode in ("genuine_r24", "shipping_v030", "frozen_compact"):
        archive = work_root / "archives" / f"{mode}.cmpct"
        receipt = work_root / f"{mode}.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--child-mode", mode,
             "--source", str(workload), "--archive", str(archive),
             "--child-result", str(receipt)],
            check=True,
        )
        rows[mode] = json.loads(receipt.read_text())

    # Guard against any process mutating the benchmark source while comparing.
    from benchmarks import v030_release_generalization as general
    post = general._historical_treehash(workload)
    if post != input_identity["historical_tree_sha256"]:
        raise RuntimeError("INVALID COMPARISON: benchmark source changed during A/B")
    base, released, candidate = (rows[m]["archive_bytes"] for m in
                                 ("genuine_r24", "shipping_v030", "frozen_compact"))
    if candidate > base:
        verdict = ("LOSS_SHARED_WITH_SHIPPING_BASELINE" if released > base
                   else "LOSS_ABSENT_FROM_SHIPPING_BASELINE")
    else:
        verdict = "O34_NEGATIVE_NOT_REPRODUCED_ON_INDEPENDENT_ONE_ROW"
    payload = {
        "schema": "cmpct-o34b-retrospective-one-row-attribution-v1",
        "source_owner_sha": SOURCE,
        "original_o34_run": 40138113211,
        "full_frozen_promotion_decision": "NO_PROMOTION_FROM_O34_PRODUCT_BYTE_LOSS",
        "scope": "one historical-identity source tree, three fresh process archives",
        "input": input_identity,
        "rows": rows,
        "candidate_minus_genuine_r24_bytes": candidate - base,
        "shipping_minus_genuine_r24_bytes": released - base,
        "candidate_minus_shipping_bytes": candidate - released,
        "one_row_attribution": verdict,
        "notes": [
            "This post-hoc single row cannot replace the 15+15 frozen matrix.",
            "No uncontrolled one-run wall number grants a performance claim.",
            "All three physically complete archive sizes are counted.",
            "Shared loss is not necessarily caused by compact policy.",
        ],
        "release_credit": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--child-mode", choices=("genuine_r24", "shipping_v030", "frozen_compact"))
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--child-result", type=Path)
    a = p.parse_args()
    if a.child_mode is None:
        if a.work_root is None or a.output is None:
            p.error("--work-root and --output required")
        _parent(a.work_root, a.output)
    else:
        if None in (a.source, a.archive, a.child_result):
            p.error("--source, --archive and --child-result required for child")
        _child(a.child_mode, a.source, a.archive, a.child_result)


if __name__ == "__main__":
    main()
