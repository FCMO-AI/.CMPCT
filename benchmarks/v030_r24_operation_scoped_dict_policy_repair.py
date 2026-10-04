from __future__ import annotations

"""Exact repair validator for operation-scoped r24 dictionary-policy transport.

Implements the frozen contract in
``docs/v030-rnd/R25_R24_OPERATION_SCOPED_DICT_POLICY_REPAIR_PREREG.md``.
Diagnostic acceptance here is a prerequisite, not release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _stable_stats(stats: dict) -> dict:
    return {k: v for k, v in stats.items() if k not in {"encode_workers", "create_s"}}


def _verify(archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as P
    result = P.strong_verify(archive)
    if result.get("ok") is not True:
        raise RuntimeError(f"strong verification failed: {result!r}")
    return result


def _release_build(source: Path, archive: Path, workers: int | None) -> dict:
    from experiments import entropygraph_v030_release_product as P

    original = P.C.Builder
    if workers is not None:
        class WorkerBuilder(original):
            def __init__(self, *args, **kwargs):
                kwargs["workers"] = workers
                super().__init__(*args, **kwargs)
        P.C.Builder = WorkerBuilder
    try:
        stats = dict(P._locality_bounded_r24_build(source, archive))
    finally:
        P.C.Builder = original
    verification = _verify(archive)
    return {
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "tree_sha256": verification.get("tree_sha256"),
        "build_stats": stats,
        "stable_build_stats": _stable_stats(stats),
        "dictionary_state": stats.get("r24_dead_dictionary_elision"),
        "encode_workers": int(stats.get("encode_workers", -1)),
        "verification": verification,
    }


def _historical_source(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    # Deterministic ordinary text corpus large enough to train a dictionary. No .bin release policy.
    for i in range(24):
        lines = []
        for j in range(180):
            lines.append(f"service={i % 4};record={j:04d};shared-prefix=cmpct-historical-control;value={(i * 97 + j) % 1009:04d}\n")
        (root / f"control-{i:02d}.txt").write_text("".join(lines), encoding="utf-8")
    return root


def _historical_build(source: Path, archive: Path, unpatched: bool) -> dict:
    import cmpct.builder as B
    import cmpct.v030_worker_policy_capture as H

    current_train = B.Builder._train_dictionary
    current_encode = B.Builder._encode_candidate
    if unpatched:
        B.Builder._train_dictionary = H._ORIGINAL_TRAIN_DICTIONARY
        B.Builder._encode_candidate = H._ORIGINAL_ENCODE_CANDIDATE
    try:
        builder = B.Builder(source, workers=4, reproducible=True)
        stats = dict(builder.build(archive))
    finally:
        B.Builder._train_dictionary = current_train
        B.Builder._encode_candidate = current_encode
    verification = _verify(archive)
    return {
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "tree_sha256": verification.get("tree_sha256"),
        "build_stats": stats,
        "stable_build_stats": _stable_stats(stats),
        "dictionary_state": stats.get("r24_dead_dictionary_elision"),
        "encode_workers": int(stats.get("encode_workers", -1)),
        "verification": verification,
    }


def _worker(mode: str, source: Path, archive: Path) -> dict:
    if mode == "release4":
        return _release_build(source, archive, 4)
    if mode == "release1":
        return _release_build(source, archive, 1)
    if mode == "historical-repaired":
        return _historical_build(source, archive, False)
    if mode == "historical-unpatched":
        return _historical_build(source, archive, True)
    raise ValueError(mode)


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    done = subprocess.run(
        [sys.executable, __file__, "--worker-mode", mode, "--worker-source", str(source), "--worker-archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {done.stderr!r}")
    return json.loads(lines[-1])


def _identity(row: dict) -> tuple:
    return (
        int(row["archive_bytes"]), row["archive_sha256"], row["tree_sha256"],
        json.dumps(row["stable_build_stats"], sort_keys=True),
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    release_source = roots[TARGET]
    historical_source = _historical_source(work_root / "historical-source")
    archive_dir = work_root / "archives"; archive_dir.mkdir()

    rows = {
        "release4": _run_worker("release4", release_source, archive_dir / "release4.cmpct"),
        "release1": _run_worker("release1", release_source, archive_dir / "release1.cmpct"),
        "historical_repaired": _run_worker("historical-repaired", historical_source, archive_dir / "historical-repaired.cmpct"),
        "historical_unpatched": _run_worker("historical-unpatched", historical_source, archive_dir / "historical-unpatched.cmpct"),
    }

    all_verified = all(r["verification"].get("ok") is True for r in rows.values())
    release_exact = _identity(rows["release4"]) == _identity(rows["release1"])
    release_live = rows["release4"]["dictionary_state"] == rows["release1"]["dictionary_state"] == "dictionary-live"
    release_workers = rows["release4"]["encode_workers"] == 4 and rows["release1"]["encode_workers"] == 1
    historical_exact = _identity(rows["historical_repaired"]) == _identity(rows["historical_unpatched"])

    if not all_verified or not release_workers:
        decision = "INVALID_REPAIR_EVIDENCE"
    elif not historical_exact:
        decision = "REPAIR_CHANGES_HISTORICAL_POLICY"
    elif not release_exact or not release_live:
        decision = "REPAIR_FAILS_WORKER_IDENTITY"
    else:
        decision = "REPAIR_CAUSALLY_VALID"

    return {
        "schema": "cmpct-v030-r24-operation-scoped-dict-policy-repair-v1",
        "source_commit": _source_commit(),
        "target": list(TARGET),
        "rows": rows,
        "identity": {
            "all_strong_verified": all_verified,
            "release_worker_counts_exact": release_workers,
            "release_four_equals_one": release_exact,
            "release_dictionary_live": release_live,
            "historical_repaired_equals_unpatched": historical_exact,
        },
        "decision": decision,
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker-mode", choices=("release4", "release1", "historical-repaired", "historical-unpatched"))
    p.add_argument("--worker-source", type=Path)
    p.add_argument("--worker-archive", type=Path)
    a = p.parse_args()
    if a.worker_mode:
        print(json.dumps(_worker(a.worker_mode, a.worker_source, a.worker_archive), sort_keys=True, default=str))
        return
    evidence = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": evidence["decision"], "identity": evidence["identity"], "sizes": {k: v["archive_bytes"] for k, v in evidence["rows"].items()}}, indent=2))


if __name__ == "__main__":
    main()
