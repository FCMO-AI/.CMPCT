from __future__ import annotations

"""Durable execution wrapper for the preregistered lazy-interval reader candidate.

The candidate itself stays frozen once result-bearing CI begins. This wrapper converts an implementation
exception into an explicit negative receipt instead of losing the artifact. A wrapper PASS means only that
the experiment completed and was recorded; scientific support is the candidate hypothesis field.
"""

import argparse
import json
import os
from pathlib import Path
import time
import traceback

from benchmarks import v030_r4_deflate_lazy_interval_reader as CANDIDATE

SCHEMA = "cmpct-v030-r4-deflate-lazy-interval-gate-v1"


def run(work: Path) -> dict:
    t0 = time.perf_counter()
    try:
        result = CANDIDATE.run(work)
        return {
            "schema": SCHEMA,
            "source_commit": os.environ.get("EVIDENCE_HEAD"),
            "experiment_completed": True,
            "candidate_exception": None,
            "candidate": result,
            "scientific_pass": bool(
                result["hypothesis"]["lazy_interval_reader_preserves_8x_path_without_full_page_materialization"]
            ),
            "elapsed_wall_s": time.perf_counter() - t0,
            "contract": {"diagnostic_only": True, "release_credit": False, "candidate_frozen": True},
        }
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "source_commit": os.environ.get("EVIDENCE_HEAD"),
            "experiment_completed": True,
            "candidate_exception": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback_tail": traceback.format_exc().splitlines()[-24:],
            },
            "candidate": None,
            "scientific_pass": False,
            "elapsed_wall_s": time.perf_counter() - t0,
            "contract": {"diagnostic_only": True, "release_credit": False, "candidate_frozen": True},
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-lazy-interval-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-lazy-interval-gate.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
