from __future__ import annotations

"""Superseding r24 streaming-finalize RSS oracle bound to the reusable semantic owner.

V1 embeds an older StreamingFinalizeBuilder. V2 deliberately reuses its frozen corpus, ordering,
measurement and decision logic while replacing only that legacy embedded class with the exact reusable
productization implementation. See docs/v030-rnd/R25_R24_STREAMING_FINALIZE_RSS_V2_PREREG.md.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from benchmarks import v030_r24_streaming_finalize_rss_oracle as V1
from experiments import entropygraph_v030_r24_streaming_finalize as STREAM

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r24-streaming-finalize-rss-v2"
OWNER_MODULE = "experiments.entropygraph_v030_r24_streaming_finalize"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _owner_receipt() -> dict:
    module_path = Path(STREAM.__file__).resolve()
    if STREAM.StreamingFinalizeBuilder.__module__ != OWNER_MODULE:
        raise RuntimeError("reusable streaming semantic-owner drift")
    if int(STREAM.SPOOL_MEMORY_BYTES) != 1024 * 1024:
        raise RuntimeError("streaming spool contract drift")
    if int(STREAM.MAX_IN_FLIGHT_FACTOR) != 1:
        raise RuntimeError("streaming in-flight contract drift")
    return {
        "class_module": STREAM.StreamingFinalizeBuilder.__module__,
        "class_name": STREAM.StreamingFinalizeBuilder.__name__,
        "module_path": str(module_path.relative_to(ROOT)),
        "module_sha256": _sha256_file(module_path),
        "spool_memory_bytes": int(STREAM.SPOOL_MEMORY_BYTES),
        "max_in_flight_factor": int(STREAM.MAX_IN_FLIGHT_FACTOR),
    }


def _run_worker(variant: str, operation: str, source: Path, work_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-variant",
            variant,
            "--worker-operation",
            operation,
            "--source",
            str(source),
            "--work-root",
            str(work_root),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    # Preserve every v1 measurement/decision rule; repair only which implementation the streaming arm owns.
    V1.StreamingFinalizeBuilder = STREAM.StreamingFinalizeBuilder
    V1._run_worker = _run_worker
    result = V1.run(work_root)
    result["schema"] = SCHEMA
    result["supersedes_interpretation_of"] = "cmpct-v030-r24-streaming-finalize-rss-v1"
    result["semantic_owner"] = _owner_receipt()
    result["contract"]["semantic_owner_changed_from_v1_legacy_duplicate"] = True
    result["contract"]["max_in_flight_factor"] = int(STREAM.MAX_IN_FLIGHT_FACTOR)
    result["release_credit"] = False
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss-v2-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss-v2.json"))
    p.add_argument("--worker-variant", choices=("shipping", "streaming"))
    p.add_argument("--worker-operation", choices=("r24", "full"))
    p.add_argument("--source", type=Path)
    args = p.parse_args()

    V1.StreamingFinalizeBuilder = STREAM.StreamingFinalizeBuilder
    if args.worker_variant:
        if args.source is None or args.worker_operation is None:
            raise SystemExit("worker requires --source and --worker-operation")
        row = V1._worker(args.worker_variant, args.worker_operation, args.source, args.work_root)
        row["semantic_owner"] = _owner_receipt() if args.worker_variant == "streaming" else None
        print(json.dumps(row, separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "semantic_owner": result["semantic_owner"],
                "rows": [
                    {
                        "target": row["target"],
                        "full_rss_ratio": row["full_rss_ratio_streaming_to_shipping"],
                        "r24_rss_ratio": row["r24_rss_ratio_streaming_to_shipping"],
                        "full_wall_ratio": row["full_wall_ratio_streaming_to_shipping"],
                    }
                    for row in result["rows"]
                ],
                "promotion_signal": result["promotion_signal"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("streaming-finalize v2 experiment invalid")


if __name__ == "__main__":
    main()
