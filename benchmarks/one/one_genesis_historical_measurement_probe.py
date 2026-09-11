from __future__ import annotations

"""Synthetic pre-gate measurement probe for the frozen v0.29/v0.30 product surfaces.

The Genesis gate needs one measurement vocabulary, but the historical contenders must not
regenerate or substitute the frozen 15-workload exam.  This probe therefore exercises only
an externally-created synthetic transfer tree and records the costs that can be measured
without changing historical reader semantics.

It is deliberately *not* a Genesis gate runner: it never imports the frozen corpus
generators, never touches the 15-workload matrix, and performs no comparison, scoring, or
winner selection.  Missing historical capabilities are reported as ``unavailable`` rather
than synthetic zeroes.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any

from benchmarks.one.one_genesis_historical_adapter_probe import (
    SURFACES,
    _historical_corpus_modules_loaded,
    _module_from_path,
    _tree_digest,
    _write_transfer_tree,
)
from benchmarks.one.one_genesis_v030_selective_adapter_probe import normalize_member_stats


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _timed(callable_obj, *args):
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    result = callable_obj(*args)
    return result, time.process_time() - cpu0, time.perf_counter() - wall0


def _unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "reason": reason}


def _selective_probe(module: Any, archive: Path, source: Path, contender: str) -> dict[str, Any]:
    if contender != "v0.30":
        return _unavailable("frozen v0.29 direct product surface has no proven selective-member reader")
    if not callable(getattr(module, "list_members", None)) or not callable(getattr(module, "read_member_with_stats", None)):
        return _unavailable("frozen v0.30 selective facade is absent")

    listed = module.list_members(archive)
    if not isinstance(listed, list):
        raise RuntimeError("v0.30 list_members() did not return a list")
    members = sorted(
        row["path"] for row in listed
        if isinstance(row, dict) and row.get("kind") == "file" and isinstance(row.get("path"), str)
    )
    expected = sorted(path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file())
    if members != expected:
        raise RuntimeError("v0.30 selective member listing differs from external input")

    rows: list[dict[str, Any]] = []
    directly_measured = True
    for member in members:
        expected_bytes = (source / member).read_bytes()
        (returned, stats), cpu_s, wall_s = _timed(module.read_member_with_stats, archive, member)
        returned = bytes(returned)
        if returned != expected_bytes:
            raise RuntimeError(f"v0.30 selective reconstruction mismatch for {member}")
        normalized = normalize_member_stats(member_bytes=expected_bytes, stats=stats)
        directly_measured = directly_measured and normalized["locality_measurement_state"] == "directly-measured"
        rows.append(
            {
                "path": member,
                "requested_bytes": len(expected_bytes),
                "cpu_s": cpu_s,
                "wall_s": wall_s,
                "locality": normalized,
            }
        )

    return {
        "status": "measured-reader-latency-only" if not directly_measured else "measured-with-direct-locality",
        "members": rows,
        "direct_locality_available_for_all_members": directly_measured,
        "warning": (
            None
            if directly_measured
            else "reader latency is measured, but decoded/touched locality remains unavailable and must not be inferred"
        ),
    }


def measure(contender: str, checkout: Path, work_root: Path) -> dict[str, Any]:
    if contender not in SURFACES:
        raise RuntimeError(f"unsupported frozen contender: {contender!r}")
    expected_sha, relpath = SURFACES[contender]
    checkout = checkout.resolve()
    observed_sha = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if observed_sha != expected_sha:
        raise RuntimeError(f"{contender}: checkout HEAD {observed_sha} != frozen {expected_sha}")

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    source = work_root / "external-transfer-tree"
    archive = work_root / f"{contender.replace('.', '')}.cmpct"
    extracted = work_root / "extracted"
    _write_transfer_tree(source)
    source_digest = _tree_digest(source)
    files, logical_bytes = _tree_stats(source)

    before_modules = set(_historical_corpus_modules_loaded())
    module = _module_from_path(checkout, relpath, f"cmpct_genesis_measurement_probe_{contender.replace('.', '_')}")
    for required in ("build", "strong_verify", "extract"):
        if not callable(getattr(module, required, None)):
            raise RuntimeError(f"{contender}: frozen surface lacks callable {required}()")

    build_stats, create_cpu_s, create_wall_s = _timed(module.build, source, archive)
    if not archive.is_file():
        raise RuntimeError(f"{contender}: build did not publish an archive")
    archive_bytes = archive.stat().st_size

    verify, verify_cpu_s, verify_wall_s = _timed(module.strong_verify, archive)
    if not isinstance(verify, dict) or verify.get("ok") is not True:
        raise RuntimeError(f"{contender}: strong_verify failed: {verify!r}")

    _, read_cpu_s, read_wall_s = _timed(module.extract, archive, extracted)
    if _tree_digest(extracted) != source_digest:
        raise RuntimeError(f"{contender}: extracted transfer tree differs from external input")
    if _tree_digest(source) != source_digest:
        raise RuntimeError(f"{contender}: frozen product mutated executor-owned input")

    selective = _selective_probe(module, archive, source, contender)
    newly_loaded = sorted(set(_historical_corpus_modules_loaded()) - before_modules)
    if newly_loaded:
        raise RuntimeError(f"{contender}: direct product loaded historical corpus modules: {newly_loaded}")

    selected = build_stats.get("selected") if isinstance(build_stats, dict) else None
    return {
        "schema": "cmpct-one-genesis-historical-measurement-probe-v1",
        "claim_boundary": "synthetic external-tree measurement compatibility only; no Genesis workload, comparison, scoring, or winner selection",
        "contender": contender,
        "source_sha": expected_sha,
        "surface": relpath,
        "synthetic": True,
        "genesis_inputs_used": False,
        "historical_generalization_harness_invoked": False,
        "historical_corpus_modules_newly_loaded": newly_loaded,
        "input": {
            "files": files,
            "logical_bytes": logical_bytes,
            "tree_sha256": source_digest,
        },
        "stored_bytes": archive_bytes,
        "creation": {
            "measured": True,
            "cpu_s": create_cpu_s,
            "wall_s": create_wall_s,
            "peak_rss_bytes": _unavailable("not yet isolated in a fresh measurement process"),
        },
        "verification": {"measured": True, "cpu_s": verify_cpu_s, "wall_s": verify_wall_s, "ok": True},
        "whole_read": {"measured": True, "cpu_s": read_cpu_s, "wall_s": read_wall_s, "exact": True},
        "selective_access": selective,
        "selected_diagnostic_only": selected,
        "semantics": {
            "exact": True,
            "integrity": True,
            "recovery": _unavailable("synthetic probe does not establish historical recovery semantics"),
            "portable": _unavailable("single Linux hosted probe cannot establish portability"),
        },
        "reader_burden": _unavailable("historical implementation burden is authority metadata, not inferred from this runtime probe"),
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=sorted(SURFACES), required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.contender, args.checkout, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "contender": result["contender"],
        "stored_bytes": result["stored_bytes"],
        "genesis_inputs_used": result["genesis_inputs_used"],
        "scoring_executed": result["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
