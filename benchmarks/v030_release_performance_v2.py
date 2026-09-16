from __future__ import annotations

"""Final-authority binding for the frozen v0.30 paired runtime promotion gate.

The base runtime harness owns the exact workloads, balanced ordering and immutable 1.10 / 1.25 thresholds.
This adapter binds the v0.30 side to ``entropygraph_v030_release_product`` and checks that side in the canonical
r24/r25 user-tree identity domain.  v0.29 remains checked against the frozen historical content-tree identity.
The two hashes intentionally describe different evidence domains; neither is rewritten or substituted for the
other, and the timed operations/thresholds remain unchanged.

The fresh-process worker already emits the promoted product's build statistics after the pack timer stops.  This
adapter preserves those existing diagnostics in the durable runtime artifact.  They carry no release credit and
change no timed operation; their purpose is causal Forge diagnosis when a frozen runtime/RSS gate is red, so the
next intervention can attack the measured selected profile/cost instead of guessing from aggregate ratios.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as PRODUCT
from tools import check_v030_release_lock as RELEASE_LOCK

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_v2.py"


def _candidate_fingerprint() -> str:
    """Bind durable benchmark evidence to the exact release-critical source surface."""
    manifest = RELEASE_LOCK.load_manifest()
    fingerprint, _ = RELEASE_LOCK.fingerprint(manifest)
    return fingerprint


def _expected_tree_for_runtime_v2(engine: str, source: Path, historical_expected: str) -> str:
    if engine == "v030":
        return PRODUCT.treehash(source)
    return historical_expected


# The base harness deliberately exposes this identity hook so a canonical binding can retain the historical
# v0.29 substrate while proving v0.30 in the richer r24/r25 product identity domain.  This happens before timing starts.
B._expected_tree_for_engine = _expected_tree_for_runtime_v2


# Preserve worker-emitted pack diagnostics without modifying the base frozen gate or its timing boundary.  The
# subprocess has already stopped its operation clock before this wrapper sees the JSON result.
_BASE_RUN_WORKER = B._run_worker
_PACK_DIAGNOSTICS: list[dict] = []


def _run_worker_with_diagnostics(*args: str) -> dict:
    result = _BASE_RUN_WORKER(*args)
    if "--op" in args and args[args.index("--op") + 1] == "pack" and result.get("build_stats") is not None:
        def _arg(name: str) -> str | None:
            return args[args.index(name) + 1] if name in args else None

        _PACK_DIAGNOSTICS.append(
            {
                "engine": _arg("--engine"),
                "source": _arg("--source"),
                "archive": _arg("--archive"),
                "build_stats": result["build_stats"],
            }
        )
    return result


B._run_worker = _run_worker_with_diagnostics


def run(work_root: Path) -> dict:
    # Compute before timing orchestration so the evidence identity is fixed at invocation start.
    candidate_fingerprint = _candidate_fingerprint()
    _PACK_DIAGNOSTICS.clear()
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_v2.py"
    result["identity_binding"] = "v029-historical-content-tree + v030-canonical-user-tree"
    result["candidate_fingerprint"] = candidate_fingerprint
    result["diagnostics"] = {
        "release_credit": False,
        "timing_boundary_changed": False,
        "source": "worker-emitted post-pack build_stats",
        "pack_build_stats": list(_PACK_DIAGNOSTICS),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-performance-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-performance-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "candidate_fingerprint": result["candidate_fingerprint"],
                "totals": result["totals"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 release-product runtime promotion gate failed")


if __name__ == "__main__":
    main()
