from __future__ import annotations

"""Authoritative entrypoint for the frozen v0.30 15-workload gate.

The underlying ``v030_release_generalization`` module owns the immutable corpus identities, v0.29 row floors and
687,783-byte release hurdle.  This adapter binds that single-sourced harness to
``experiments.entropygraph_v030_release`` so the measurement includes the release-path G0-G4 streamed
publication rehabilitation rather than the earlier research builder.

The durable JSON also embeds the exact release-critical content fingerprint computed by the strict release-lock
front door.  This does not grant release credit by itself; it makes a genuinely green artifact eligible to serve
as evidence for a receipt on the same frozen fingerprint instead of relying on an artifact filename or CI SHA.

Footnote: this file may change *which byte-identical implementation* is measured, but it must never modify the
frozen thresholds.  Any threshold change belongs in the underlying contract and requires an explicit policy
change, not a benchmark-adapter convenience.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_generalization as B
from experiments import entropygraph_v030_release as RELEASE
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

# The harness resolves RC globals at runtime; bind it once before any corpus work starts.
B.RC = RELEASE


def run(work_root: Path) -> dict:
    result = B.run(work_root)
    result = dict(result)
    result["engine"] = "experiments/entropygraph_v030_release.py"
    result["release_facade"] = "cmpct-v030-authoritative-integration-v1"
    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)
    result["candidate_fingerprint"] = fingerprint
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_fingerprint": result["candidate_fingerprint"], "totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 integrated compression/generalization gate failed")


if __name__ == "__main__":
    main()
