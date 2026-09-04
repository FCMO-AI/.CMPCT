#!/usr/bin/env python3
from __future__ import annotations

"""Resilient continuation of established_corpora_v2.

The v2 run exposed a benchmark-harness defect: one slow research engine could abort a corpus before
mature competitors or the v0.30 snapshot ran. v3 keeps the same corpus bytes and per-engine semantics,
but records timeout/error as an outcome, persists after every cell, and continues. The practical profile
puts shipping CMPCT and mature tools first, then the frozen v0.30 snapshot. Experimental v0.29 research
runs last and is omitted from the 23-member sweep to avoid spending the runner budget repeatedly on a
known scalability failure; aggregate/enwik9 still test it explicitly.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import established_corpora_v2 as v2


def persist(result: dict[str, Any], out: Path, final: bool = False) -> None:
    path = out / ("external-corpora.json" if final else "external-corpora.partial.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=False))


def failure(exc: BaseException, started: float) -> dict[str, Any]:
    elapsed = time.perf_counter() - started
    text = str(exc)[-4000:]
    timeout_like = isinstance(exc, subprocess.TimeoutExpired) or "timeout" in text.lower() or "timed out" in text.lower()
    return {
        "status": "timeout" if timeout_like else "error",
        "elapsed_until_failure_s": elapsed,
        "timeout_ceiling_s": v2.TIMEOUT,
        "error_type": type(exc).__name__,
        "error_tail": text,
    }


def runners(profile: str, py29: str, repo29: str, py30: str, repo30: str) -> list[tuple[str, Callable[[Path, Path], dict[str, Any]]]]:
    practical: list[tuple[str, Callable[[Path, Path], dict[str, Any]]]] = [
        ("cmpct-v0.29-shipping-r24", lambda s, w: v2.cmpct_shipping(s, w, py29)),
        ("zip-deflate-9", v2.zip9),
        ("zstd-3", lambda s, w: v2.stream("zstd-3", s, w)),
        ("zstd-19", lambda s, w: v2.stream("zstd-19", s, w)),
        ("7z-lzma2-9", v2.seven),
        ("xz-9e", lambda s, w: v2.stream("xz-9e", s, w)),
        ("gzip-9", lambda s, w: v2.stream("gzip-9", s, w)),
        ("bzip2-9", lambda s, w: v2.stream("bzip2-9", s, w)),
        ("cmpct-v0.30-canonical-snapshot", lambda s, w: v2.cmpct_module(s, w, py30, repo30, "v030-canonical")),
    ]
    if profile == "all":
        practical.append(("cmpct-v0.29-research", lambda s, w: v2.cmpct_module(s, w, py29, repo29, "v029-research")))
    return practical


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=["practical", "all"], default="all")
    a = ap.parse_args()

    spec = json.loads(Path(a.manifest).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    py29 = os.environ["CMPCT_V029_PYTHON"]
    repo29 = os.environ["CMPCT_V029_REPO"]
    py30 = os.environ["CMPCT_V030_PYTHON"]
    repo30 = os.environ["CMPCT_V030_REPO"]

    result: dict[str, Any] = {
        "schema": "cmpct-established-corpora-v3",
        "purpose": "fault-isolated external research evidence; not a release gate or website headline",
        "provenance": {
            "v029_release_sha": os.environ["CMPCT_V029_SHA"],
            "v030_snapshot_sha": os.environ["CMPCT_V030_SHA"],
            "benchmark_sha": os.environ.get("GITHUB_SHA"),
            "runner": os.environ.get("RUNNER_NAME"),
            "tool_versions": v2.tool_versions(),
        },
        "semantics": {
            "timing": "fresh-process GNU time; requested corpus repetitions retained for successful cells",
            "timeout_policy": f"same {v2.TIMEOUT}s outer process ceiling for every engine cell; timeout is retained as a negative result",
            "single_file_stream": "raw canonical file; archive formats retain native container overhead",
            "multi_file_stream": "deterministic normalized tar piped to stream compressor",
            "source_metadata": "regular-file mode and mtime normalized because corpus authorities specify bytes, not filesystem timestamps",
            "roundtrip": "relative path + byte length + SHA-256 must match exactly",
            "failure_policy": "one engine timeout/error never suppresses later competitors; partial JSON persisted after every cell",
            "profile": a.profile,
            "scores": "no weighted aggregate score in raw evidence; downstream scorecards must expose each axis and coverage",
        },
        "corpora": {},
    }

    attempted = ok = timeouts = errors = 0
    for item in spec["corpora"]:
        name = item["name"]
        src = Path(item["path"])
        rows = v2.tree_manifest(src)
        logical = sum(r["bytes"] for r in rows)
        if logical != int(item["expected_logical_bytes"]):
            raise RuntimeError(f"{name} logical mismatch")
        entry: dict[str, Any] = {
            "authority": item.get("authority"),
            "mode": item.get("mode"),
            "logical_bytes": logical,
            "files": len(rows),
            "tree_sha256": v2.tree_digest(rows),
            "timing_repetitions_requested": int(item.get("repetitions", 1)),
            "results": {},
        }
        result["corpora"][name] = entry
        persist(result, out)

        for label, fn in runners(a.profile, py29, repo29, py30, repo30):
            attempted += 1
            reps: list[dict[str, Any]] = []
            started = time.perf_counter()
            try:
                for i in range(entry["timing_repetitions_requested"]):
                    work = out / "work" / name / label / f"rep-{i}"
                    shutil.rmtree(work, ignore_errors=True)
                    work.mkdir(parents=True)
                    print(f"BENCH {name} :: {label} :: rep {i+1}", flush=True)
                    reps.append(fn(src, work))
                cell = v2.summarize(reps, logical)
                cell["status"] = "ok"
                ok += 1
            except BaseException as exc:
                cell = failure(exc, started)
                if cell["status"] == "timeout":
                    timeouts += 1
                else:
                    errors += 1
                print(json.dumps({"corpus": name, "compressor": label, **cell}, sort_keys=True), flush=True)
            entry["results"][label] = cell
            result["coverage"] = {"attempted_cells": attempted, "ok_cells": ok, "timeout_cells": timeouts, "error_cells": errors}
            persist(result, out)
            if cell["status"] == "ok":
                print(json.dumps({"corpus": name, "compressor": label, **cell}, sort_keys=True), flush=True)

    result["coverage"] = {"attempted_cells": attempted, "ok_cells": ok, "timeout_cells": timeouts, "error_cells": errors}
    result["complete_with_recorded_failures"] = True
    persist(result, out, final=True)
    print("RESULT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
