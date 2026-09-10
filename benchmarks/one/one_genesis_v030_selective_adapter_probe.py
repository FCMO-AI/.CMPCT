from __future__ import annotations

"""Pre-Genesis probe for the frozen v0.30 selective-read product surface.

Comparator-preservation only.  The exact frozen product receives a synthetic external
input tree, publishes a real archive, and is required to reconstruct every regular member
exactly through both selective APIs.  The probe records whether the historical facade
actually exports direct locality accounting; it does not manufacture missing counters.
It never touches the 15 Genesis workloads and performs no comparison or scoring.
"""

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from benchmarks.one.one_genesis_gate_executor_preflight import V030_SHA
from benchmarks.one.one_genesis_historical_adapter_probe import (
    _historical_corpus_modules_loaded,
    _module_from_path,
    _tree_digest,
    _write_transfer_tree,
)

MODULE = "experiments/entropygraph_v030_release_product.py"


def normalize_member_stats(*, member_bytes: bytes, stats: Any) -> dict[str, Any]:
    if not isinstance(stats, dict):
        raise RuntimeError("v0.30 selective stats must be an object")
    logical = stats.get("logical_bytes")
    if not isinstance(logical, int) or isinstance(logical, bool) or logical != len(member_bytes):
        raise RuntimeError("v0.30 selective logical_bytes must equal returned member bytes")

    decoded = stats.get("decoded_context_bytes")
    amplification = stats.get("decoded_context_amplification")
    if decoded is None:
        if amplification is not None:
            raise RuntimeError("v0.30 selective amplification cannot be measured when decoded context is unavailable")
        locality_state = "external-instrumentation-required"
    else:
        if not isinstance(decoded, int) or isinstance(decoded, bool) or decoded < len(member_bytes):
            raise RuntimeError("v0.30 decoded_context_bytes must cover returned member bytes")
        if not isinstance(amplification, (int, float)) or isinstance(amplification, bool) or amplification < 0:
            raise RuntimeError("v0.30 measured decoded_context_amplification must be non-negative")
        expected = 0.0 if len(member_bytes) == 0 else decoded / len(member_bytes)
        if abs(float(amplification) - expected) > 1e-9:
            raise RuntimeError("v0.30 decoded-context amplification is internally inconsistent")
        locality_state = "directly-measured"

    return {
        "logical_bytes": logical,
        "decoded_context_bytes": decoded,
        "decoded_context_amplification": amplification,
        "format_profile": stats.get("format_profile"),
        "locality_accounting": stats.get("locality_accounting"),
        "locality_measurement_state": locality_state,
        "raw_stats": stats,
    }


def probe(*, v030_repo: Path, work_root: Path) -> dict[str, Any]:
    v030_repo = v030_repo.resolve()
    observed_sha = subprocess.check_output(["git", "-C", str(v030_repo), "rev-parse", "HEAD"], text=True).strip()
    if observed_sha != V030_SHA:
        raise RuntimeError(f"v0.30 checkout HEAD {observed_sha} != frozen {V030_SHA}")

    work_root.mkdir(parents=True, exist_ok=True)
    source = work_root / "external-transfer-tree"
    archive = work_root / "v030-transfer.cmpct"
    if source.exists() or archive.exists():
        raise RuntimeError("refusing to reuse existing selective-probe inputs or archive")
    _write_transfer_tree(source)
    source_digest = _tree_digest(source)

    before_modules = set(_historical_corpus_modules_loaded())
    product = _module_from_path(v030_repo, MODULE, "cmpct_genesis_v030_selective_product")
    for required in ("build", "strong_verify", "list_members", "read_member", "read_member_with_stats"):
        if not callable(getattr(product, required, None)):
            raise RuntimeError(f"frozen v0.30 product lacks callable {required}()")

    build_stats = product.build(source, archive)
    if not archive.is_file():
        raise RuntimeError("v0.30 build did not publish an archive path")
    verified = product.strong_verify(archive)
    if not isinstance(verified, dict) or verified.get("ok") is not True:
        raise RuntimeError(f"v0.30 strong_verify rejected synthetic transfer archive: {verified!r}")

    listed = product.list_members(archive)
    if not isinstance(listed, list):
        raise RuntimeError("v0.30 list_members must return a list")
    file_members = sorted(
        row["path"] for row in listed
        if isinstance(row, dict) and row.get("kind") == "file" and isinstance(row.get("path"), str)
    )
    expected_members = sorted(path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file())
    if file_members != expected_members:
        raise RuntimeError(f"v0.30 regular-member listing mismatch: expected={expected_members!r} actual={file_members!r}")

    rows: list[dict[str, Any]] = []
    states: set[str] = set()
    for member in expected_members:
        expected = (source / member).read_bytes()
        plain = bytes(product.read_member(archive, member))
        with_stats, stats = product.read_member_with_stats(archive, member)
        with_stats = bytes(with_stats)
        if plain != expected or with_stats != expected:
            raise RuntimeError(f"v0.30 selective reconstruction mismatch for {member}")
        normalized = normalize_member_stats(member_bytes=expected, stats=stats)
        states.add(normalized["locality_measurement_state"])
        rows.append({"path": member, "logical_bytes": len(expected), "stats": normalized})

    if _tree_digest(source) != source_digest:
        raise RuntimeError("frozen v0.30 selective probe mutated executor-owned input tree")
    newly_loaded = sorted(set(_historical_corpus_modules_loaded()) - before_modules)
    if newly_loaded:
        raise RuntimeError(f"direct frozen product unexpectedly loaded historical corpus modules: {newly_loaded}")

    return {
        "schema": "cmpct-one-genesis-v030-selective-adapter-probe-v2",
        "claim_boundary": "frozen v0.30 selective API exactness and accounting availability on synthetic external input only; not Genesis performance evidence or scoring",
        "frozen_v030_sha": V030_SHA,
        "module": MODULE,
        "synthetic": True,
        "genesis_inputs_used": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
        "archive_bytes_diagnostic_only": archive.stat().st_size,
        "selected_diagnostic_only": build_stats.get("selected") if isinstance(build_stats, dict) else None,
        "locality_measurement_states": sorted(states),
        "direct_locality_available_for_all_members": states == {"directly-measured"},
        "members": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v030-repo", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(v030_repo=args.v030_repo, work_root=args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "members": len(result["members"]),
        "direct_locality_available_for_all_members": result["direct_locality_available_for_all_members"],
        "locality_measurement_states": result["locality_measurement_states"],
        "genesis_inputs_used": result["genesis_inputs_used"],
        "scoring_executed": result["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
