from __future__ import annotations

"""Extended selective-effort frontier above the historical level-19 EntropyGraph floor.

Accepted v0.29 office/analytics bytes effectively inherit the historical high-effort EntropyGraph frontier.  A
compression-effort upper bound that stops at level 19 therefore cannot answer the most useful question: whether a
small number of high-yield physical packs can use Zstd 20-22 to pay the new canonical-filesystem metadata tax while
remaining inside ZIP creation time.

This front door keeps v2's timing-correct baseline and exact model, but expands final-pack choices to
1/3/6/9/12/15/19/20/21/22. Probe/audition calls remain capped at level 1.  No shipping compressor setting changes.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v2 as V2

EXTENDED_LEVELS = (1, 3, 6, 9, 12, 15, 19, 20, 21, 22)


def run(work_root: Path) -> dict:
    old_levels = V1.LEVELS
    V1.LEVELS = EXTENDED_LEVELS
    try:
        result = dict(V2.run(work_root))
    finally:
        V1.LEVELS = old_levels
    result["schema"] = "cmpct-v030-federated-selective-effort-v3"
    result["levels"] = list(EXTENDED_LEVELS)
    result["claim_boundary"] = (
        "research-only C25EG01 final-pack effort frontier. Levels 20-22 are explored only to test whether a "
        "small high-yield subset can pay canonical metadata overhead above the historical level-19/v0.29 floor. "
        "Probe effort, candidate defaults, selector, v0.29 floor, ZIP/Zstd thresholds, locality, native/Android "
        "support and release authority are unchanged."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("federated selective-effort v3 measurement invalid")


if __name__ == "__main__":
    main()
