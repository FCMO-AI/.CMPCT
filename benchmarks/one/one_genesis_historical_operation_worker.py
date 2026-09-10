from __future__ import annotations

"""One-operation worker for fresh-process measurement of frozen historical products.

The worker receives executor-owned paths and a frozen checkout. It never generates the
Genesis corpus and never compares contenders. Each invocation performs exactly one product
operation so the parent can meter a clean process boundary.
"""

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from benchmarks.one.one_genesis_historical_adapter_probe import (
    SURFACES,
    _historical_corpus_modules_loaded,
    _module_from_path,
    _tree_digest,
)


def _checkout_sha(checkout: Path) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()


def _load(contender: str, checkout: Path):
    if contender not in SURFACES:
        raise RuntimeError(f"unsupported frozen contender: {contender!r}")
    expected_sha, relpath = SURFACES[contender]
    observed = _checkout_sha(checkout)
    if observed != expected_sha:
        raise RuntimeError(f"{contender}: checkout HEAD {observed} != frozen {expected_sha}")
    before = set(_historical_corpus_modules_loaded())
    module = _module_from_path(checkout.resolve(), relpath, f"cmpct_genesis_worker_{contender.replace('.', '_')}")
    loaded = sorted(set(_historical_corpus_modules_loaded()) - before)
    if loaded:
        raise RuntimeError(f"{contender}: direct product loaded historical corpus modules: {loaded}")
    return expected_sha, relpath, module


def run_operation(
    *,
    contender: str,
    checkout: Path,
    operation: str,
    source: Path | None,
    archive: Path,
    output_tree: Path | None,
) -> dict[str, Any]:
    expected_sha, relpath, module = _load(contender, checkout)
    receipt: dict[str, Any] = {
        "schema": "cmpct-one-genesis-historical-operation-worker-v1",
        "contender": contender,
        "source_sha": expected_sha,
        "surface": relpath,
        "operation": operation,
        "genesis_inputs_generated": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }

    if operation == "build":
        if source is None or not source.is_dir():
            raise RuntimeError("build requires an existing executor-owned source tree")
        before_digest = _tree_digest(source)
        stats = module.build(source, archive)
        if not archive.is_file():
            raise RuntimeError("build did not publish archive")
        after_digest = _tree_digest(source)
        if after_digest != before_digest:
            raise RuntimeError("historical build mutated executor-owned source tree")
        receipt.update(
            {
                "input_tree_sha256": before_digest,
                "archive_bytes": archive.stat().st_size,
                "selected_diagnostic_only": stats.get("selected") if isinstance(stats, dict) else None,
            }
        )
        return receipt

    if not archive.is_file():
        raise RuntimeError(f"{operation} requires an existing archive")

    if operation == "verify":
        verify = module.strong_verify(archive)
        if not isinstance(verify, dict) or verify.get("ok") is not True:
            raise RuntimeError(f"strong_verify failed: {verify!r}")
        receipt["verify_ok"] = True
        return receipt

    if operation == "extract":
        if output_tree is None:
            raise RuntimeError("extract requires --output-tree")
        if output_tree.exists():
            raise RuntimeError("extract output tree must not already exist")
        module.extract(archive, output_tree)
        if not output_tree.is_dir():
            raise RuntimeError("extract did not publish output tree")
        receipt["output_tree_sha256"] = _tree_digest(output_tree)
        return receipt

    raise RuntimeError(f"unsupported operation: {operation!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=sorted(SURFACES), required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--operation", choices=("build", "verify", "extract"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-tree", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = run_operation(
        contender=args.contender,
        checkout=args.checkout,
        operation=args.operation,
        source=args.source,
        archive=args.archive,
        output_tree=args.output_tree,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
