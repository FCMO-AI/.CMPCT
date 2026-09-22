from __future__ import annotations

"""Same-input Office density referee: repaired v0.30 admission vs frozen v0.29.

Mission Lock
============
The earlier Office admission receipt appeared 50,632 B below a historical v0.29 number,
but subsequent zero-byte determinism checks proved that freshly generated filesystem
mtimes and admission-pruning directory mtimes leaked into the candidate bytes.  That
makes cross-run byte subtraction scientifically weaker than a same-input comparison.

This referee generates the Office source once, canonicalizes only the *benchmark input*
filesystem mtimes to a fixed epoch, and gives that exact tree to both contenders.  The
v0.30 diagnostic admission candidate restores surviving staging-directory metadata from
the input after pruning, preserving filesystem fidelity instead of recording harness
execution time.  Frozen v0.29 executes in a separate process from its exact checkout and
fails closed if any loaded ``cmpct`` module escapes that checkout.

Falsifiable hypothesis
----------------------
On one identical Office input, the repaired admission mechanism remains smaller than the
frozen v0.29 product while reconstructing the exact regular-file tree and preserving all
eight derived views.  Two v0.30 builds from that same input must also be byte-identical.

A density loss is a scientific FAIL, not a workflow/infrastructure error.  This referee
still grants no locality or release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_admission_mtime_causality_referee as MTIME
from benchmarks import v030_r4_office_admission_staging_metadata_referee as STAGE
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as ADMIT
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-admission-same-input-v029-v1"
HISTORICAL_V029_OFFICE_BYTES = 5_954_026
HISTORICAL_ADMISSION_BYTES = 5_903_394


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_source(work: Path) -> Path:
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "r4_sameinput_neutral",
    )
    repair = V029._load(V029.REPAIR_PATH, "r4_sameinput_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    MTIME._fix_mtimes(source)
    return source


def _build_current(source: Path, out: Path, work: Path) -> tuple[dict, dict]:
    original_build = ADMIT.PRODUCT.build
    observed: dict[str, int] = {}

    def wrapped_build(staging: Path, archive: Path, *args, **kwargs):
        observed["restored_directories"] = STAGE._restore_surviving_directory_metadata(source, staging)
        return original_build(staging, archive, *args, **kwargs)

    ADMIT.PRODUCT.build = wrapped_build
    try:
        cpu0 = time.process_time()
        wall0 = time.perf_counter()
        cand = ADMIT._build_candidate(source, out, work)
        cpu = time.process_time() - cpu0
        wall = time.perf_counter() - wall0
    finally:
        ADMIT.PRODUCT.build = original_build

    verify = SFV4.extract_candidate(out, work.parent / f"extract-{out.name}")
    expected = PRODUCT.treehash(source)
    if verify["tree_sha256"] != expected:
        raise RuntimeError("repaired admission candidate tree mismatch")
    if cand["derived_file_count"] != 8:
        raise RuntimeError("repaired admission candidate lost an exact derived view")
    files = sorted(p for p in out.iterdir() if p.is_file())
    receipt = {
        "stored_bytes": sum(p.stat().st_size for p in files),
        "component_bytes": {p.name: p.stat().st_size for p in files},
        "component_sha256": {p.name: _sha256(p) for p in files},
        "create_cpu_s": cpu,
        "create_wall_s": wall,
        "hosted_process_peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)),
        "restored_directories": int(observed["restored_directories"]),
        "derived_file_count": cand["derived_file_count"],
        "admitted_containers": cand["admitted_containers"],
        "rejected_containers": cand["rejected_containers"],
        "stream_roots": cand["stream_roots"],
        "stream_raw_bytes": cand["stream_raw_bytes"],
        "tree_sha256": expected,
        "exact": True,
    }
    return cand, receipt


def _run_v029(worker: Path, checkout: Path, source: Path, work: Path) -> dict:
    archive = work / "v029.cmpct"
    output = work / "v029.json"
    env = os.environ.copy()
    # Do not let the modern editable package win resolution in the child.  The worker
    # also prepends and audits the frozen checkout itself, so this is defense in depth.
    env.pop("PYTHONPATH", None)
    subprocess.run(
        [
            sys.executable,
            str(worker.resolve()),
            "--checkout", str(checkout.resolve()),
            "--source", str(source.resolve()),
            "--archive", str(archive.resolve()),
            "--output", str(output.resolve()),
        ],
        check=True,
        env=env,
    )
    return json.loads(output.read_text())


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source = _build_source(work)
    source_rows = MTIME._metadata_rows(source)
    source_meta_sha = MTIME._metadata_digest(source_rows)
    source_tree = PRODUCT.treehash(source)

    _cand_a, current_a = _build_current(source, work / "current-a", work / "current-a-work")
    _cand_b, current_b = _build_current(source, work / "current-b", work / "current-b-work")
    current_deterministic = (
        current_a["component_bytes"] == current_b["component_bytes"]
        and current_a["component_sha256"] == current_b["component_sha256"]
    )
    if not current_deterministic:
        raise RuntimeError("repaired current candidate is not deterministic on one exact input")

    frozen = _run_v029(worker, v029_checkout, source, work / "frozen")
    if not frozen.get("source_sealed") or frozen.get("frozen_source_sha") != "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d":
        raise RuntimeError("frozen v0.29 source seal missing")
    if not frozen.get("reconstruction_exact"):
        raise RuntimeError("frozen v0.29 reconstruction was not exact")

    delta = current_a["stored_bytes"] - int(frozen["stored_bytes"])
    hypothesis = {
        "one_identical_input_tree": True,
        "current_candidate_byte_deterministic": current_deterministic,
        "current_exact": current_a["exact"],
        "all_eight_derived_views_preserved": current_a["derived_file_count"] == 8,
        "frozen_v029_source_sealed": bool(frozen["source_sealed"]),
        "frozen_v029_exact": bool(frozen["reconstruction_exact"]),
        "current_smaller_than_frozen_v029_same_input": delta < 0,
    }
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": {
            "tree_sha256": source_tree,
            "filesystem_metadata_sha256": source_meta_sha,
            "filesystem_rows": len(source_rows),
            "fixed_epoch_ns": MTIME.FIXED_EPOCH_NS,
        },
        "current_admission": current_a,
        "current_repeat": {
            "stored_bytes": current_b["stored_bytes"],
            "component_sha256": current_b["component_sha256"],
        },
        "frozen_v029": frozen,
        "same_input_delta_bytes_current_minus_v029": delta,
        "same_input_margin_if_current_wins": -delta,
        "historical_context_only": {
            "old_v029_office_bytes": HISTORICAL_V029_OFFICE_BYTES,
            "old_admission_bytes": HISTORICAL_ADMISSION_BYTES,
            "old_margin_bytes": HISTORICAL_V029_OFFICE_BYTES - HISTORICAL_ADMISSION_BYTES,
            "authoritative_for_this_referee": False,
        },
        "hypothesis": hypothesis,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_input_same_filesystem_metadata": True,
            "frozen_v029_executes_own_source_package": True,
            "loaded_cmpct_modules_fail_closed_outside_frozen_checkout": True,
            "current_product_builder_unchanged": True,
            "filesystem_fidelity_weakened": False,
            "admission_thresholds_or_codecs_changed": False,
            "hosted_current_rss_is_not_fresh_process_attribution": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-same-input-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument(
        "--worker",
        type=Path,
        default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"),
    )
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-same-input-v029.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "current_bytes": d["current_admission"]["stored_bytes"],
        "frozen_v029_bytes": d["frozen_v029"]["stored_bytes"],
        "delta_current_minus_v029": d["same_input_delta_bytes_current_minus_v029"],
        "current_cpu_s": d["current_admission"]["create_cpu_s"],
        "current_wall_s": d["current_admission"]["create_wall_s"],
        "v029_cpu_s": d["frozen_v029"]["create_cpu_s"],
        "v029_wall_s": d["frozen_v029"]["create_wall_s"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
