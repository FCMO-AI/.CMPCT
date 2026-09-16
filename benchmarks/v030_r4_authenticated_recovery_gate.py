from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import traceback

from benchmarks import v030_r4_authenticated_recovery_reader as C

SCHEMA = "cmpct-v030-r4-authenticated-recovery-gate-v1"


def run(work: Path) -> dict:
    t0 = time.perf_counter()
    try:
        c = C.run(work)
        return {
            "schema": SCHEMA,
            "source_commit": os.environ.get("EVIDENCE_HEAD"),
            "experiment_completed": True,
            "candidate_exception": None,
            "candidate": c,
            "scientific_pass": bool(c["hypothesis"]["archive_rooted_auth_and_single_chunk_recovery_preserve_locality_and_density"]),
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
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-auth-recovery-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-auth-recovery-gate.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
