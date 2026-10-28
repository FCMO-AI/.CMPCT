from __future__ import annotations

"""Diagnose the 4-byte Office admission receipt drift without relaxing evidence.

Mission Lock
------------
The hosted locality-budget gate on 7aa73c9 observed the same exact admission
candidate at 5,903,390 B while the earlier accepted receipt recorded 5,903,394 B.
Deterministic stored bytes have zero tolerance, so the 4-byte difference is an
evidence/substrate defect until causally attributed.

This referee rebuilds the unchanged candidate, verifies the exact source tree, and
records each emitted component's byte length and SHA-256. The hosted workflow runs
this program twice in fresh Python processes. No codec, threshold, locality law,
admission rule, or product selector changes here.

Disproof / classification
------------------------
* Fresh-process component vectors differ: candidate construction is nondeterministic.
* Fresh-process vectors agree but differ from the frozen receipt: stable environment
  or dependency drift; isolate the changed component before resuming locality work.
* Vectors agree with the frozen receipt: the prior 4-byte observation was transient
  and must be reproduced before being dismissed.

A green workflow means attribution completed, not that v0.30 earned product credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as ADMIT
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-admission-reproducibility-referee-v1"
FROZEN_TOTAL = 5_903_394
FROZEN_COMPONENT_BYTES = {
    "manifest.json": 29_480,
    "auth.bin": 135,
    "streams.bin": 3_791_492,
    "base.cmpct": 2_061_133,
    "literal.bin": 21_154,
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "r4_admitrepro_neutral",
    )
    repair = V029._load(V029.REPAIR_PATH, "r4_admitrepro_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    expected = PRODUCT.treehash(source)

    out = work / "candidate"
    cand = ADMIT._build_candidate(source, out, work / "candidate-work")
    verify = SFV4.extract_candidate(out, work / "extract")
    if verify["tree_sha256"] != expected:
        raise RuntimeError("admission candidate tree mismatch")
    if cand["derived_file_count"] != 8:
        raise RuntimeError("admission candidate lost an exact derived view")

    names = sorted(p.name for p in out.iterdir() if p.is_file())
    component_bytes = {name: (out / name).stat().st_size for name in names}
    component_sha256 = {name: _sha256(out / name) for name in names}
    delta = {
        name: component_bytes.get(name, 0) - FROZEN_COMPONENT_BYTES.get(name, 0)
        for name in sorted(set(component_bytes) | set(FROZEN_COMPONENT_BYTES))
    }
    total = sum(component_bytes.values())

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "tree_sha256": expected,
        "stored_bytes": total,
        "frozen_receipt_bytes": FROZEN_TOTAL,
        "delta_vs_frozen_bytes": total - FROZEN_TOTAL,
        "component_bytes": component_bytes,
        "frozen_component_bytes": FROZEN_COMPONENT_BYTES,
        "component_delta_vs_frozen": delta,
        "component_sha256": component_sha256,
        "candidate": {
            "candidate_containers": cand["candidate_containers"],
            "admitted_containers": cand["admitted_containers"],
            "rejected_containers": cand["rejected_containers"],
            "stream_roots": cand["stream_roots"],
            "stream_raw_bytes": cand["stream_raw_bytes"],
            "derived_file_count": cand["derived_file_count"],
            "rejected_source_bytes_retained_in_base_input": cand[
                "rejected_source_bytes_retained_in_base_input"
            ],
        },
        "hypothesis": {
            "exact_tree": verify["tree_sha256"] == expected,
            "all_eight_derived_views_preserved": cand["derived_file_count"] == 8,
            "matches_frozen_total": total == FROZEN_TOTAL,
            "matches_frozen_component_sizes": component_bytes == FROZEN_COMPONENT_BYTES,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_admission_builder": True,
            "no_threshold_or_codec_change": True,
            "zero_byte_determinism_tolerance": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r4-office-admission-repro-work"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r4-office-admission-repro.json"),
    )
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "stored_bytes": d["stored_bytes"],
        "delta_vs_frozen_bytes": d["delta_vs_frozen_bytes"],
        "component_delta_vs_frozen": d["component_delta_vs_frozen"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
