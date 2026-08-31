from __future__ import annotations

"""A/B a locality-neutral operation-scoped decoded-record cache in the native G0-G4 reader.

Both CLIs consume the exact same canonical ML archive. The candidate changes only complete-operation
verify/extract ownership: decoded physical records may survive between logical members under the existing
64 MiB insertion-only ceiling, while each member keeps a fresh node cache and still charges every required
record to its own locality stats even on a shared-cache hit. Selective single-member reads retain the existing
fresh-cache behavior. The receipt binds itself to the exact repository HEAD that built both measured binaries.

The full terminal decision still requires all seven rounds. A separate checkpoint is persisted after every
completed round so a runner interruption preserves exact non-release diagnostic evidence instead of erasing
hours of work. Checkpoints can never authorize promotion or release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

from benchmarks import v030_release_performance as PERF
from benchmarks.v030_g04_ml_native_reader_oracle import _corrupt_first_physical_payload
from experiments import entropygraph_v030_native_reader_bridge as NATIVE
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROOT = Path(__file__).resolve().parents[1]
ROUNDS = 7
MIN_VERIFY_IMPROVEMENT = 0.10
MIN_EXTRACT_IMPROVEMENT = 0.10


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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


def _write_checkpoint(
    checkpoint: Path | None,
    *,
    source_commit: str,
    binary_sha256: dict[str, str],
    tree: str,
    built: dict,
    baseline_info: dict,
    candidate_info: dict,
    samples: dict[str, list[float]],
    completed_rounds: int,
) -> None:
    if checkpoint is None:
        return
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    medians = {
        key: (float(statistics.median(values)) if values else None)
        for key, values in samples.items()
    }
    verify_improvement = None
    extract_improvement = None
    if medians["baseline_verify"] is not None and medians["candidate_verify"] is not None:
        verify_improvement = 1.0 - medians["candidate_verify"] / max(medians["baseline_verify"], 1e-12)
    if medians["baseline_extract"] is not None and medians["candidate_extract"] is not None:
        extract_improvement = 1.0 - medians["candidate_extract"] / max(medians["baseline_extract"], 1e-12)
    payload = {
        "schema": "cmpct-v030-g04-ml-operation-record-cache-checkpoint-v1",
        "source_commit": source_commit,
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "diagnosis": "D2",
        "radicality": "R2",
        "rps": 86,
        "binary_sha256": binary_sha256,
        "shipping_build": built,
        "tree_sha256": tree,
        "same_public_info": baseline_info == candidate_info,
        "planned_rounds": ROUNDS,
        "completed_rounds": completed_rounds,
        "samples_s": samples,
        "provisional_medians_s": medians,
        "provisional_verify_improvement_fraction": verify_improvement,
        "provisional_extract_improvement_fraction": extract_improvement,
        "terminal_decision": None,
        "promotion_signal": False,
        "release_credit": False,
        "claim_boundary": "Interruption-safe diagnostic only. All seven rounds plus corruption rejection remain mandatory before any terminal decision.",
    }
    tmp = checkpoint.with_suffix(checkpoint.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(checkpoint)


def run(work_root: Path, baseline_cli: Path, candidate_cli: Path, checkpoint: Path | None = None) -> dict:
    for cli in (baseline_cli, candidate_cli):
        if not cli.is_file():
            raise RuntimeError(f"missing native CLI: {cli}")
    binary_sha256 = {
        "baseline": _file_sha256(baseline_cli),
        "candidate": _file_sha256(candidate_cli),
    }
    if binary_sha256["baseline"] == binary_sha256["candidate"]:
        raise RuntimeError("native A/B executables are byte-identical; candidate patch is not represented in the measured binary")

    source_commit = _source_commit()
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
    _write_checkpoint(
        checkpoint,
        source_commit=source_commit,
        binary_sha256=binary_sha256,
        tree=tree,
        built=built,
        baseline_info=baseline_info,
        candidate_info=candidate_info,
        samples=samples,
        completed_rounds=0,
    )
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
        _write_checkpoint(
            checkpoint,
            source_commit=source_commit,
            binary_sha256=binary_sha256,
            tree=tree,
            built=built,
            baseline_info=baseline_info,
            candidate_info=candidate_info,
            samples=samples,
            completed_rounds=round_index + 1,
        )

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
        "distinct_measured_binaries": binary_sha256["baseline"] != binary_sha256["candidate"],
        "same_archive_bytes": True,
        "same_public_info": baseline_info == candidate_info,
        "same_extracted_tree": True,
        "baseline_corruption_rejected": rejected["baseline"],
        "candidate_corruption_rejected": rejected["candidate"],
        "candidate_verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "candidate_extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    promotion = all(gate.values())
    terminal_decision = "PROMOTE_NEXT_PREREQUISITE" if promotion else "RETIRE_FAMILY"
    return {
        "schema": "cmpct-v030-g04-ml-operation-record-cache-ab-v5",
        "source_commit": source_commit,
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "diagnosis": "D2",
        "radicality": "R2",
        "rps": 86,
        "binary_sha256": binary_sha256,
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
            "terminal_decision_requires_all_rounds": True,
        },
        "gate": {**gate, "passed": promotion},
        "promotion_signal": promotion,
        "terminal_decision": terminal_decision,
        "next_if_promoted": "productize bounded operation-scoped record ownership, then re-earn selective locality/hostile/native/Android/runtime authority",
        "next_if_retired": "attack G0-G4 reconstruction/audition ownership rather than another record-cache threshold",
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
    p.add_argument("--checkpoint", type=Path, default=None)
    args = p.parse_args()
    result = run(args.work_root, args.baseline_cli, args.candidate_cli, args.checkpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_commit": result["source_commit"],
        "binary_sha256": result["binary_sha256"],
        "medians_s": result["medians_s"],
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "gate": result["gate"],
        "terminal_decision": result["terminal_decision"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
