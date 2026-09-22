from __future__ import annotations

"""Compatibility entrypoint for the logs inverse-edge sidecar-pack oracle.

The accepted v0.29 row schema exposes ``accepted_v029_bytes``. The first research implementation accidentally
looked for the obsolete generic ``archive_bytes`` key after candidate construction, which made the evidence lane
abort before writing its JSON. Keep the research mechanism byte-for-byte unchanged and adapt only that evidence
row at the call boundary so the oracle can measure what it was designed to measure.

This adapter is deliberately narrow and research-only. It cannot alter thresholds, candidate bytes, timing,
locality accounting or extraction verification.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_logs_inverse_edge_oracle as BASE
from benchmarks import v030_logs_inverse_edge_sidecar_pack_oracle as ORACLE


def run(work_root: Path) -> dict:
    original = BASE._build_target_root

    def compatible_root(path: Path):
        workload, accepted = original(path)
        accepted = dict(accepted)
        accepted["archive_bytes"] = int(accepted["accepted_v029_bytes"])
        return workload, accepted

    BASE._build_target_root = compatible_root
    try:
        return ORACLE.run(work_root)
    finally:
        BASE._build_target_root = original


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-sidecar-pack-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-sidecar-pack.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
