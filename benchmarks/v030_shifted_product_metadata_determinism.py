from __future__ import annotations

"""Frozen D2 causal check for Shifted cross-run product-byte drift.

Evidence-only. It changes no production or release behavior.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_SHIFTED_PRODUCT_METADATA_DETERMINISM_PREREG.md"
FIXED_MTIME_NS = 1_767_225_600_000_000_000
REPETITIONS = 3


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _metadata_manifest(root: Path) -> dict:
    h = hashlib.sha256()
    mtimes: list[int] = []
    entries = [root, *sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix())]
    for path in entries:
        st = path.lstat()
        rel = "." if path == root else path.relative_to(root).as_posix()
        raw = rel.encode("utf-8")
        h.update(len(raw).to_bytes(4, "little")); h.update(raw)
        h.update(int(st.st_mode).to_bytes(4, "little", signed=False))
        h.update(int(st.st_mtime_ns).to_bytes(8, "little", signed=True))
        mtimes.append(int(st.st_mtime_ns))
    return {
        "sha256": h.hexdigest(),
        "entries": len(entries),
        "mtime_min_ns": min(mtimes),
        "mtime_max_ns": max(mtimes),
        "unique_mtimes": len(set(mtimes)),
    }


def _fix_mtimes(root: Path) -> None:
    # Set descendants first and root last so directory mtimes cannot be perturbed by later traversal work.
    paths = sorted([root, *root.rglob("*")], key=lambda p: len(p.relative_to(root).parts), reverse=True)
    for path in paths:
        os.utime(path, ns=(FIXED_MTIME_NS, FIXED_MTIME_NS), follow_symlinks=False)
    for path in [root, *root.rglob("*")]:
        if int(path.lstat().st_mtime_ns) != FIXED_MTIME_NS:
            raise RuntimeError(f"mtime normalization did not stick: {path}")


def _one(work_root: Path, arm: str, rep: int, expected_historical: str) -> dict:
    corpus_root = work_root / f"{arm}-r{rep}" / "corpus"
    roots = PERF._build_corpora(corpus_root)
    source = roots[TARGET]
    historical_before = GENERAL._historical_treehash(source)
    if historical_before != expected_historical:
        raise RuntimeError(f"historical Shifted identity drift before metadata arm: {historical_before}")
    if arm == "fixed-mtime":
        _fix_mtimes(source)
    elif arm != "fresh":
        raise RuntimeError(f"unknown arm: {arm}")
    historical_after = GENERAL._historical_treehash(source)
    if historical_after != expected_historical:
        raise RuntimeError("metadata arm changed the accepted historical content-tree identity")

    metadata = _metadata_manifest(source)
    product_tree = str(PRODUCT.treehash(source))
    archive = work_root / f"{arm}-r{rep}" / "selected.cmpct"
    archive.parent.mkdir(parents=True, exist_ok=True)
    stats = dict(PRODUCT.build(source, archive))
    verify = dict(PRODUCT.strong_verify(archive))
    if not verify.get("ok") or str(verify.get("tree_sha256") or "") != product_tree:
        raise RuntimeError(f"selected product strong verification failed for {arm}/r{rep}")
    return {
        "arm": arm,
        "rep": rep,
        "historical_tree_sha256": historical_after,
        "product_tree_sha256": product_tree,
        "metadata": metadata,
        "selected_archive_bytes": archive.stat().st_size,
        "selected_archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "r24_product_bytes": int(stats.get("r24_product_bytes", -1)),
        "r25_product_bytes": int(stats.get("r25_product_bytes", -1)),
        "verified_tree_sha256": verify.get("tree_sha256"),
        "strong_verify_ok": bool(verify.get("ok")),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    expected_historical = str(accepted[TARGET]["tree_sha256"])
    rows: list[dict] = []
    failures: list[str] = []
    try:
        for arm in ("fresh", "fixed-mtime"):
            for rep in range(REPETITIONS):
                rows.append(_one(work_root, arm, rep, expected_historical))
    except Exception as exc:
        failures.append(f"{type(exc).__name__}:{exc}")

    def vals(arm: str, key: str) -> set:
        return {row[key] for row in rows if row["arm"] == arm}

    fresh = [row for row in rows if row["arm"] == "fresh"]
    fixed = [row for row in rows if row["arm"] == "fixed-mtime"]
    valid = (
        not failures
        and len(fresh) == REPETITIONS
        and len(fixed) == REPETITIONS
        and all(row["historical_tree_sha256"] == expected_historical for row in rows)
        and all(row["strong_verify_ok"] and row["verified_tree_sha256"] == row["product_tree_sha256"] for row in rows)
        and all(row["r24_product_bytes"] > 0 for row in rows)
        and all(row["metadata"]["mtime_min_ns"] == FIXED_MTIME_NS and row["metadata"]["mtime_max_ns"] == FIXED_MTIME_NS for row in fixed)
    )
    decision = "INVALID_EXPERIMENT"
    if valid:
        fresh_product_trees = vals("fresh", "product_tree_sha256")
        fresh_r24_bytes = vals("fresh", "r24_product_bytes")
        fixed_product_trees = vals("fixed-mtime", "product_tree_sha256")
        fixed_r24_bytes = vals("fixed-mtime", "r24_product_bytes")
        fixed_metadata = {row["metadata"]["sha256"] for row in fixed}
        supported = (
            len(fresh_product_trees) > 1
            and len(fresh_r24_bytes) > 1
            and len(fixed_product_trees) == 1
            and len(fixed_r24_bytes) == 1
            and len(fixed_metadata) == 1
        )
        decision = "SHIFTED_MTIME_METADATA_CAUSAL_SUPPORTED" if supported else "SHIFTED_MTIME_METADATA_NOT_SUFFICIENT"

    return {
        "schema": "cmpct-v030-shifted-product-metadata-determinism-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "target": list(TARGET),
        "expected_historical_tree_sha256": expected_historical,
        "fixed_mtime_ns": FIXED_MTIME_NS,
        "repetitions_per_arm": REPETITIONS,
        "rows": rows,
        "experiment_valid": valid,
        "failures": failures,
        "decision": decision,
        "release_credit": False,
        "observed_sets": {
            "fresh_product_trees": sorted(vals("fresh", "product_tree_sha256")) if fresh else [],
            "fresh_r24_product_bytes": sorted(vals("fresh", "r24_product_bytes")) if fresh else [],
            "fresh_metadata_manifests": sorted({row["metadata"]["sha256"] for row in fresh}),
            "fixed_product_trees": sorted(vals("fixed-mtime", "product_tree_sha256")) if fixed else [],
            "fixed_r24_product_bytes": sorted(vals("fixed-mtime", "r24_product_bytes")) if fixed else [],
            "fixed_metadata_manifests": sorted({row["metadata"]["sha256"] for row in fixed}),
        },
        "contract": {
            "historical_content_identity_must_not_change": True,
            "metadata_intervention": "atime+mtime only",
            "fixed_mtime_ns": FIXED_MTIME_NS,
            "release_thresholds_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-product-metadata-determinism-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-product-metadata-determinism.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"experiment_valid": data["experiment_valid"], "decision": data["decision"], "observed_sets": data["observed_sets"]}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("Shifted metadata determinism experiment invalid")


if __name__ == "__main__":
    main()
