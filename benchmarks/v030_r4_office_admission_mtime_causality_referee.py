from __future__ import annotations

"""Test whether fresh-generation filesystem mtimes cause the Office admission byte drift.

Mission Lock
============
The exact admission candidate previously measured 5,903,394 B, then 5,903,390 B,
and two fresh generations in one hosted job produced 5,903,390 B and 5,903,392 B.
The logical-content tree hash was identical, but canonical CMPCT preserves filesystem
mtime. The neutral/hostile repair canonicalizes timestamps *inside* Office/PDF/ZIP
bytes; it does not currently canonicalize filesystem mtimes.

Hypothesis
----------
Fresh generator filesystem mtimes are the sole cause of the byte drift in base.cmpct.

Disproof test
-------------
Generate the Office workload twice in independent roots. First build the unchanged
candidate from each root. Then set only filesystem mtimes (files/directories/links)
to one fixed epoch and rebuild. The hypothesis is falsified if fixed-mtime builds do
not become byte-identical while source contents remain identical.

This is diagnostic evidence only. It does not authorize changing benchmark identity,
filesystem-fidelity semantics, the product builder, selector thresholds, or locality.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as ADMIT
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-admission-mtime-causality-v1"
FIXED_EPOCH_NS = 1_577_836_800_000_000_000  # 2020-01-01T00:00:00Z


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _metadata_rows(root: Path) -> list[dict]:
    rows = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        st = path.lstat()
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "mode": stat.S_IMODE(st.st_mode),
            "kind": "symlink" if stat.S_ISLNK(st.st_mode) else ("dir" if stat.S_ISDIR(st.st_mode) else "file"),
            "size": int(st.st_size),
            "mtime_ns": int(st.st_mtime_ns),
            "uid": int(getattr(st, "st_uid", 0)),
            "gid": int(getattr(st, "st_gid", 0)),
        })
    return rows


def _metadata_digest(rows: list[dict]) -> str:
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _fix_mtimes(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        try:
            os.utime(path, ns=(FIXED_EPOCH_NS, FIXED_EPOCH_NS), follow_symlinks=False)
        except (NotImplementedError, OSError):
            if not path.is_symlink():
                raise
    os.utime(root, ns=(FIXED_EPOCH_NS, FIXED_EPOCH_NS), follow_symlinks=False)


def _build_source(work: Path, label: str) -> Path:
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        f"r4_admitmtime_neutral_{label}",
    )
    repair = V029._load(V029.REPAIR_PATH, f"r4_admitmtime_repair_{label}")
    repair.install_generation_hooks(neutral)
    corpus = work / f"neutral-{label}"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    return corpus / "02_office_workspace"


def _build_candidate(source: Path, work: Path, label: str) -> dict:
    out = work / f"candidate-{label}"
    shutil.rmtree(out, ignore_errors=True)
    cand = ADMIT._build_candidate(source, out, work / f"candidate-work-{label}")
    verify = SFV4.extract_candidate(out, work / f"extract-{label}")
    tree = PRODUCT.treehash(source)
    if verify["tree_sha256"] != tree:
        raise RuntimeError(f"candidate tree mismatch for {label}")
    component_bytes = {p.name: p.stat().st_size for p in sorted(out.iterdir()) if p.is_file()}
    component_sha256 = {p.name: _sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    return {
        "tree_sha256": tree,
        "stored_bytes": sum(component_bytes.values()),
        "component_bytes": component_bytes,
        "component_sha256": component_sha256,
        "candidate_containers": cand["candidate_containers"],
        "admitted_containers": cand["admitted_containers"],
        "rejected_containers": cand["rejected_containers"],
        "stream_roots": cand["stream_roots"],
        "derived_file_count": cand["derived_file_count"],
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    a = _build_source(work, "a")
    b = _build_source(work, "b")

    content_a = PRODUCT.treehash(a)
    content_b = PRODUCT.treehash(b)
    meta_a = _metadata_rows(a)
    meta_b = _metadata_rows(b)
    before = {
        "a": _build_candidate(a, work, "a-before"),
        "b": _build_candidate(b, work, "b-before"),
    }

    _fix_mtimes(a)
    _fix_mtimes(b)
    fixed_meta_a = _metadata_rows(a)
    fixed_meta_b = _metadata_rows(b)
    after = {
        "a": _build_candidate(a, work, "a-fixed"),
        "b": _build_candidate(b, work, "b-fixed"),
    }

    same_content_before = content_a == content_b
    metadata_diff_before = _metadata_digest(meta_a) != _metadata_digest(meta_b)
    fixed_metadata_equal = _metadata_digest(fixed_meta_a) == _metadata_digest(fixed_meta_b)
    fixed_bytes_equal = after["a"]["component_sha256"] == after["b"]["component_sha256"]
    fixed_sizes_equal = after["a"]["component_bytes"] == after["b"]["component_bytes"]
    causal_pass = same_content_before and metadata_diff_before and fixed_metadata_equal and fixed_bytes_equal and fixed_sizes_equal

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "fixed_epoch_ns": FIXED_EPOCH_NS,
        "content_tree_sha256": {"a": content_a, "b": content_b},
        "metadata": {
            "before_sha256": {"a": _metadata_digest(meta_a), "b": _metadata_digest(meta_b)},
            "after_sha256": {"a": _metadata_digest(fixed_meta_a), "b": _metadata_digest(fixed_meta_b)},
            "mtime_mismatch_paths_before": sum(
                1 for ra, rb in zip(meta_a, meta_b)
                if ra["path"] == rb["path"] and ra["mtime_ns"] != rb["mtime_ns"]
            ),
            "rows": len(meta_a),
        },
        "before": before,
        "after_fixed_mtime": after,
        "hypothesis": {
            "same_logical_content_before": same_content_before,
            "filesystem_metadata_differs_before": metadata_diff_before,
            "fixed_metadata_equal": fixed_metadata_equal,
            "fixed_candidate_component_sizes_equal": fixed_sizes_equal,
            "fixed_candidate_byte_identical": fixed_bytes_equal,
            "mtime_causality_supported": causal_pass,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "benchmark_identity_change_authorized": False,
            "filesystem_fidelity_unchanged": True,
            "selector_thresholds_unchanged": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-admission-mtime-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-admission-mtime.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "before_bytes": {k: v["stored_bytes"] for k, v in d["before"].items()},
        "fixed_bytes": {k: v["stored_bytes"] for k, v in d["after_fixed_mtime"].items()},
        "mtime_mismatch_paths_before": d["metadata"]["mtime_mismatch_paths_before"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))
    if not d["hypothesis"]["mtime_causality_supported"]:
        raise SystemExit("mtime-only causality hypothesis falsified")


if __name__ == "__main__":
    main()
