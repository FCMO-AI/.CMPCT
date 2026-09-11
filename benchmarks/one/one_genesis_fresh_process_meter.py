from __future__ import annotations

"""Fail-closed fresh-process CPU/RSS meter for Genesis adapter operations.

This module measures exactly one child process per observation.  It intentionally reports
only the direct child's resource boundary unless that worker explicitly folds descendants
into its own receipt; a future adapter must not call direct-child RSS "process-tree RSS".
The parent uses wait4 so setup/teardown performed inside the worker cannot disappear from
CPU accounting merely because the driver process is long-lived.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence


def _rss_bytes_from_wait4(ru_maxrss: int) -> int:
    # Linux reports ru_maxrss in KiB. Genesis hosted authority is Linux; reject other
    # platforms rather than silently changing units.
    if sys.platform != "linux":
        raise RuntimeError("fresh-process RSS meter currently has Linux-only unit authority")
    return int(ru_maxrss) * 1024


def measure_command(argv: Sequence[str], *, receipt_path: Path | None = None) -> dict[str, Any]:
    if not argv:
        raise ValueError("meter requires a non-empty command")
    wall0 = time.perf_counter()
    proc = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL)
    pid, status, usage = os.wait4(proc.pid, 0)
    wall_s = time.perf_counter() - wall0
    if pid != proc.pid:
        raise RuntimeError("wait4 returned an unexpected pid")
    returncode = os.waitstatus_to_exitcode(status)
    # Popen did not reap via wait(); mirror the observed state so its destructor does not
    # attempt a second wait. This is private state but stable across supported CPython 3.x.
    proc.returncode = returncode
    result: dict[str, Any] = {
        "schema": "cmpct-one-genesis-fresh-process-meter-v1",
        "argv": list(argv),
        "returncode": returncode,
        "wall_s": wall_s,
        "cpu_user_s": float(usage.ru_utime),
        "cpu_system_s": float(usage.ru_stime),
        "cpu_total_s": float(usage.ru_utime + usage.ru_stime),
        "peak_rss_bytes": _rss_bytes_from_wait4(usage.ru_maxrss),
        "resource_scope": "direct-child-process",
        "descendant_resource_scope": "unavailable-unless-worker-receipt-proves-folding",
    }
    if receipt_path is not None:
        if not receipt_path.is_file():
            result["worker_receipt"] = {"status": "unavailable", "reason": "worker receipt was not published"}
        else:
            result["worker_receipt"] = json.loads(receipt_path.read_text(encoding="utf-8"))
    if returncode != 0:
        raise RuntimeError(json.dumps({"error": "metered command failed", "measurement": result}, sort_keys=True))
    return result


def _self_test_worker(mode: str, receipt: Path) -> int:
    # The worker is intentionally fresh. `memory` creates a large live allocation so hosted
    # falsifiers can prove RSS is non-zero without pretending the exact number is portable.
    if mode == "memory":
        blob = bytearray(32 * 1024 * 1024)
        for offset in range(0, len(blob), 4096):
            blob[offset] = offset & 0xFF
        checksum = sum(blob[::4096])
    elif mode == "cpu":
        value = 0
        for i in range(2_000_000):
            value = (value * 1664525 + i + 1013904223) & 0xFFFFFFFF
        checksum = value
    else:
        raise ValueError(mode)
    receipt.write_text(json.dumps({"mode": mode, "checksum": checksum}, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test-worker", choices=("memory", "cpu"))
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test_worker:
        if args.receipt is None:
            parser.error("--self-test-worker requires --receipt")
        raise SystemExit(_self_test_worker(args.self_test_worker, args.receipt))
    if args.output is None:
        parser.error("meter mode requires --output")
    with tempfile.TemporaryDirectory(prefix="one-fresh-meter-") as td:
        receipt = Path(td) / "worker.json"
        command = [sys.executable, __file__, "--self-test-worker", "memory", "--receipt", str(receipt)]
        result = measure_command(command, receipt_path=receipt)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("cpu_total_s", "peak_rss_bytes", "resource_scope", "returncode")}, sort_keys=True))


if __name__ == "__main__":
    main()
