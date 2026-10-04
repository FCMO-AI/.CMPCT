from __future__ import annotations

"""High-compression-level continuation of the exact logs inverse-edge oracle.

The base inverse-edge result is already a strict size+creation win over ZIP and solid Zstd-19, but its level-9
candidate remains roughly 160 KiB above the immutable accepted-v0.29 byte floor while retaining substantial
creation-time headroom versus ZIP. Before adding a new representation, this oracle asks whether spending some of
that time budget on the *same exact inverse-edge grammar* closes the historical byte floor.

All source planning, exact edge discovery/decompression, compression, metadata and archive-write time remain
charged by the base oracle. Every candidate is fully extracted and exact-tree verified, and <=8x/8 MiB locality
remains mandatory. Ties are failures. Research only; a win still requires canonical grammar/recovery and
Python/native/Android parity before selector promotion.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_logs_inverse_edge_oracle as BASE

LEVELS = (9, 12, 15, 17, 19)


def run(work_root: Path) -> dict:
    previous = BASE.LEVELS
    try:
        BASE.LEVELS = LEVELS
        result = BASE.run(work_root)
    finally:
        BASE.LEVELS = previous
    result = dict(result)
    result["schema"] = "cmpct-v030-logs-inverse-edge-high-level-oracle-v1"
    result["claim_boundary"] = "research-only high-level sweep of exact inverse-edge grammar; not canonical r25"
    result["levels"] = list(LEVELS)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-inverse-high-level-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-inverse-high-level.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
