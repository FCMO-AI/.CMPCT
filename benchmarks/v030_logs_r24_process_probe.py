from __future__ import annotations

"""Run the unchanged canonical-v2 gate with only the Logs r24 ownership probe substituted in its fresh worker."""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance_v2 as V2


V2.B.WORKER = V2.B.ROOT / "benchmarks" / "v030_logs_r24_process_worker_probe.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-r24-process-probe-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-r24-process-probe.json"))
    args = parser.parse_args()
    result = V2.run(args.work_root)
    result["probe"] = {
        "question": "does child-owning only the Logs selector r24 control close residual parent RSS?",
        "product_credit": False,
        "thresholds_changed": False,
        "candidate_bytes_changed_intentionally": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("Logs r24 process ownership probe did not clear unchanged canonical-v2 gate")


if __name__ == "__main__":
    main()
