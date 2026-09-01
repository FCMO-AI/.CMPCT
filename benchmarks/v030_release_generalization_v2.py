from __future__ import annotations

"""Final-authority binding for the frozen v0.30 15-workload compression gate.

The base harness owns every corpus identity and threshold.  This adapter only swaps the measured implementation
to ``entropygraph_v030_authoritative`` (shared attempt-5 construction, strict streamed reader, metadata-only
PrefixGraph locality and bounded encoder-family admission).  It is therefore impossible for this file to make
the release gate easier without changing the base contract itself.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_generalization as B
from experiments import entropygraph_v030_authoritative as AUTH
from tools import check_v030_release_lock as RELEASE_LOCK

B.RC = AUTH


def _candidate_fingerprint() -> str:
    """Bind durable benchmark evidence to the exact release-critical source surface."""
    manifest = RELEASE_LOCK.load_manifest()
    fingerprint, _ = RELEASE_LOCK.fingerprint(manifest)
    return fingerprint


def run(work_root: Path) -> dict:
    # Compute before the expensive run so the evidence identity is fixed at invocation start.
    candidate_fingerprint = _candidate_fingerprint()
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_authoritative.py"
    result["release_facade"] = "cmpct-v030-authoritative-v2"
    result["candidate_fingerprint"] = candidate_fingerprint
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-generalization-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-generalization-v2.json"))
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
        raise SystemExit("v0.30 authoritative-v2 compression/generalization gate failed")


if __name__ == "__main__":
    main()
