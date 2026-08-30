from __future__ import annotations

"""A/B a locality-neutral operation-scoped decoded-record cache in the native G0-G4 reader.

Both CLIs consume the exact same canonical ML archive. The candidate changes only complete-operation
verify/extract ownership: decoded physical records may survive between logical members under the existing
64 MiB insertion-only ceiling, while each member keeps a fresh node cache and still charges every required
record to its own locality stats even on a shared-cache hit. Selective single-member reads retain the existing
fresh-cache behavior.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from benchmarks.v030_g04_ml_native_reader_oracle import _corrupt_first_physical_payload
from experiments import entropygraph_v030_native_reader_bridge as NATIVE
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 7
MIN_VERIFY_IMPROVEMENT = 0.10
MIN_EXTRACT_IMPROVEMENT = 0.10


def _verify(cli: Path, archive: Path) -> float:
    started = time.perf_counter()
    receipt = NATIVE.verify_g04(cli, archive)
    elapsed = time.perf_counter() - started
    if not receipt.get("ok") or receipt.get("profile") != NATIVE.CANONICAL_G04_PROFILE:
        raise RuntimeError("native verify receipt drift")
    return elapsed


def _extract(cli: Path, archive: Path, destination: Path) -> float:
    shutil.rmtree(destination, ignore_errors=True)
    started = time.perf_counter()
    receipt = NATIVE.extract_g04(
        cli,
        archive,
        destination,
        max_output_bytes=RR.MAX_DECLARED_LOGICAL_BYTES,
    )
    elapsed = time.perf_counter() - started
    if not receipt.get("ok") or not receipt.get("transactional_native_extract"):
        raise RuntimeError("native extraction receipt drift")
    return elapsed


def run(work_root: Path, baseline_cli: Path, candidate_cli: Path) -> dict:
    for cli in (baseline_cli, candidate_cli):
        if not cli.is_file():
            raise RuntimeError(f"missing native CLI: {cli}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != tree:
            raise RuntimeError("shipping verification failed before native A/B")

    baseline_info = NATIVE.info_g04(baseline_cli, archive)
    candidate_info = NATIVE.info_g04(candidate_cli, archive)
    if baseline_info != candidate_info:
        raise RuntimeError("candidate changed native public archive info")

    samples = {"baseline_verify": [], "candidate_verify": [], "baseline_extract": [], "candidate_extract": []}
    for round_index in range(ROUNDS):
        candidate_first = bool(round_index % 2)
        order = (("candidate", candidate_cli), ("baseline", baseline_cli)) if candidate_first else (("baseline", baseline_cli), ("candidate", candidate_cli))
        for label, cli in order:
            samples[f"{label}_verify"].append(_verify(cli, archive))
            dest = work_root / f"{label}-extract-{round_index}"
            samples[f"{label}_extract"].append(_extract(cli, archive, dest))
            if PRODUCT.treehash(dest) != tree:
                raise RuntimeError(f"{label} extraction tree identity drift")
            shutil.rmtree(dest, ignore_errors=True)

    corrupt = work_root / "ml-corrupt.cmpct"
    _corrupt_first_physical_payload(archive, corrupt)
    rejected = {}
    for label, cli in (("baseline", baseline_cli), ("candidate", candidate_cli)):
        try:
            NATIVE.verify_g04(cli, corrupt)
        except NATIVE.NativeReaderError:
            rejected[label] = True
        else:
            rejected[label] = False

    medians = {key: float(statistics.median(values)) for key, values in samples.items()}
    verify_improvement = 1.0 - medians["candidate_verify"] / max(medians["baseline_verify"], 1e-12)
    extract_improvement = 1.0 - medians["candidate_extract"] / max(medians["baseline_extract"], 1e-12)
    gate = {
        "same_archive_bytes": True,
        "same_public_info": baseline_info == candidate_info,
        "same_extracted_tree": True,
        "baseline_corruption_rejected": rejected["baseline"],
        "candidate_corruption_rejected": rejected["candidate"],
        "candidate_verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "candidate_extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    return {
        "schema": "cmpct-v030-g04-ml-operation-record-cache-ab-v2",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "tree_sha256": tree,
        "rounds": ROUNDS,
        "samples_s": samples,
        "medians_s": medians,
        "verify_improvement_fraction": verify_improvement,
        "extract_improvement_fraction": extract_improvement,
        "corruption_rejected": rejected,
        "contract": {
            "record_cache_limit_bytes": 64 * 1024 * 1024,
            "node_cache_scope": "fresh per member",
            "member_locality_charged_on_shared_record_hit": True,
            "selective_member_cache_scope": "fresh per member",
            "complete_verify_cache_scope": "one bounded cache per verify operation",
            "complete_extract_cache_scope": "one bounded cache per extract operation",
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
        },
        "gate": {**gate, "passed": all(gate.values())},
        "promotion_signal": all(gate.values()),
        "release_credit": False,
        "claim_boundary": (
            "Research-only native A/B. A pass authorizes productizing bounded operation-scoped decoded-record "
            "ownership for complete G0-G4 verify and extract. It does not authorize native dispatch or release "
            "credit until exact selective locality, hostile/fuzz, native/Android and runtime authority is re-earned."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline-cli", type=Path, required=True)
    p.add_argument("--candidate-cli", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-operation-record-cache-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-operation-record-cache.json"))
    args = p.parse_args()
    result = run(args.work_root, args.baseline_cli, args.candidate_cli)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "medians_s": result["medians_s"],
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "gate": result["gate"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
