#!/usr/bin/env python3
"""J24N02 original-source/native-candidate comparison; does not change a benchmark gate.

Compiles the *actual* GitHub parent native C file and exact current branch source.
Captures raw output, compiler identity and repeated standalone ordinary throughput.
All expected historic observations are explicit; a historical negative is not a
candidate test failure. Full CMPCT Builder/Reader/ABI product parity is separate.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = "5e99cdcdc213d91792ca616881570976362b7d98"
PARENT_BLOB = "a6253beece20ce8aad3cdb605a6d9fcaa50d9364"
CANDIDATE_BLOB = "216189c6a15f1579d596bc4df5128ae63f794168"


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(args, cwd=cwd or ROOT, text=True, capture_output=True, check=False)
    if check and p.returncode:
        raise RuntimeError(f"command failed {args!r} rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}")
    return p


def blob(rev: str) -> str:
    return run("git", "rev-parse", f"{rev}:native/cmpct_cdc.c").stdout.strip()


def compile_native(c_source: Path, court: Path, output: Path) -> str:
    if os.name == "nt":
        cc = shutil.which("cl")
        if not cc:
            raise RuntimeError("MSVC cl missing: do not report Windows green without native compilation")
        cmd = [cc, "/nologo", "/W4", "/WX", "/std:c11", str(court), str(c_source),
               "/Fe:" + str(output), "/Fo:" + str(output.with_suffix(".obj"))]
    else:
        cc = shutil.which(os.getenv("CC", "cc"))
        if not cc:
            raise RuntimeError("No C compiler; cannot claim source-exact verification")
        cmd = [cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               str(court), str(c_source), "-o", str(output)]
    run(*cmd)
    return run(cc, "--version", check=False).stdout.splitlines()[0] if os.name != "nt" else "MSVC cl"


def audit() -> dict[str, object]:
    observed_parent = blob(PARENT)
    observed_head = run("git", "rev-parse", "HEAD").stdout.strip()
    observed_candidate = blob(observed_head)
    if observed_parent != PARENT_BLOB:
        raise RuntimeError(f"source custody: historical {observed_parent} != {PARENT_BLOB}")
    if observed_candidate != CANDIDATE_BLOB:
        raise RuntimeError(f"source custody: candidate {observed_candidate} != {CANDIDATE_BLOB}")
    court = ROOT / "tests" / "native_cdc_bounds_court.c"
    with tempfile.TemporaryDirectory(prefix="j24n02_") as d:
        temp = Path(d)
        baseline_src = temp / "historical_cdc.c"
        baseline_src.write_bytes(run("git", "show", f"{PARENT}:native/cmpct_cdc.c").stdout.encode())
        suffix = ".exe" if os.name == "nt" else ""
        oldbin = temp / ("native_old" + suffix)
        newbin = temp / ("native_fixed" + suffix)
        compiler = compile_native(baseline_src, court, oldbin)
        compile_native(ROOT / "native" / "cmpct_cdc.c", court, newbin)
        checks = {}
        for label, binary, mode in [
            ("parent_ordinary", oldbin, "ordinary"),
            ("candidate_ordinary", newbin, "ordinary"),
            ("parent_negative", oldbin, "parent"),
            ("candidate_extreme", newbin, "candidate"),
        ]:
            p = run(str(binary), mode)
            checks[label] = p.stdout.strip()
        if checks["parent_ordinary"] != checks["candidate_ordinary"]:
            raise RuntimeError("normal CDC boundary parity diverged:\n" + str(checks))

        # Repeated raw measurements are microbenchmarks, not release speed evidence.
        timings: list[dict[str, object]] = []
        for iteration in range(6):
            order = [("old", oldbin), ("new", newbin)] if iteration % 2 == 0 else [
                ("new", newbin), ("old", oldbin)]
            for variant, binary in order:
                started = time.perf_counter_ns()
                p = run(str(binary), "ordinary")
                elapsed = time.perf_counter_ns() - started
                if p.stdout.strip() != checks["parent_ordinary"]:
                    raise RuntimeError("repeated ordinary fingerprint drift")
                timings.append({"round": iteration, "source": variant, "wall_ns_with_startup": elapsed})
        return {
            "scientific_question": "CDC bounded cumulative offsets retain ordinary cuts and fix extreme max_size",
            "parent_commit": PARENT,
            "historical_native_blob": observed_parent,
            "candidate_commit": observed_head,
            "candidate_native_blob": observed_candidate,
            "compiler": compiler,
            "platform": platform.platform(),
            "python": sys.version,
            "c_court_sha256": hashlib.sha256(court.read_bytes()).hexdigest(),
            "checks": checks,
            "micro_timing_with_process_startup": timings,
            "claim_boundary": "Standalone native C correctness + scoped process-start-inclusive timing only; no Builder/Reader/full product release credit.",
        }


def main() -> int:
    dest = Path(os.environ.get("J24N02_RECEIPT_DIR", "j24n02-receipts"))
    dest.mkdir(parents=True, exist_ok=True)
    name = platform.system().lower()
    try:
        result = audit()
        result["status"] = "PASS"
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "platform": platform.platform()}
        (dest / f"j24n02-{name}.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 1
    (dest / f"j24n02-{name}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "micro_timing_with_process_startup"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
