#!/usr/bin/env python3
from __future__ import annotations

"""Fast, fault-isolated established-corpus lane for shipping CMPCT and mature compressors.

This lane intentionally excludes provisional/research CMPCT engines so their runtime cannot hold the
shipping-vs-established evidence hostage. It uses the exact corpus, timing and round-trip semantics from
established_corpora_v2 and the failure-preservation contract from v3.
"""

import argparse
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Callable

import established_corpora_v2 as v2
import established_corpora_v3 as v3


def baseline_runners(py29: str) -> list[tuple[str, Callable[[Path, Path], dict[str, Any]]]]:
    return [
        ("cmpct-v0.29-shipping-r24", lambda s, w: v2.cmpct_shipping(s, w, py29)),
        ("zip-deflate-9", v2.zip9),
        ("zstd-3", lambda s, w: v2.stream("zstd-3", s, w)),
        ("zstd-19", lambda s, w: v2.stream("zstd-19", s, w)),
        ("7z-lzma2-9", v2.seven),
        ("xz-9e", lambda s, w: v2.stream("xz-9e", s, w)),
        ("gzip-9", lambda s, w: v2.stream("gzip-9", s, w)),
        ("bzip2-9", lambda s, w: v2.stream("bzip2-9", s, w)),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.manifest).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    py29 = os.environ["CMPCT_V029_PYTHON"]

    result: dict[str, Any] = {
        "schema": "cmpct-established-corpora-baselines-v1",
        "purpose": "shipping-v0.29 versus mature external compressors; research evidence, not a release gate or website headline",
        "provenance": {
            "v029_release_sha": os.environ["CMPCT_V029_SHA"],
            "benchmark_sha": os.environ.get("GITHUB_SHA"),
            "runner": os.environ.get("RUNNER_NAME"),
            "tool_versions": v2.tool_versions(),
        },
        "semantics": {
            "timing": "fresh-process GNU time; requested repetitions retained for successful cells",
            "timeout_policy": f"same {v2.TIMEOUT}s process ceiling for every cell; timeout remains a negative result",
            "single_file_stream": "raw canonical file; archive formats retain native container overhead",
            "multi_file_stream": "deterministic normalized tar piped to stream compressor",
            "source_metadata": "regular-file mode and mtime normalized because corpus authorities specify bytes, not filesystem timestamps",
            "roundtrip": "relative path + byte length + SHA-256 must match exactly",
            "failure_policy": "one compressor timeout/error never suppresses later competitors; partial JSON persisted after every cell",
            "threading_note": "CMPCT shipping is explicitly workers=1; mainstream tools use their stated/default CLI threading, so wall time is practical-invocation rather than normalized CPU-thread efficiency",
            "scores": "raw evidence has no weighted universal score",
        },
        "corpora": {},
    }

    attempted = good = timeouts = errors = 0
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
        v3.persist(result, out)

        for label, fn in baseline_runners(py29):
            attempted += 1
            reps: list[dict[str, Any]] = []
            started = time.perf_counter()
            try:
                for i in range(entry["timing_repetitions_requested"]):
                    work = out / "work" / name / label / f"rep-{i}"
                    shutil.rmtree(work, ignore_errors=True)
                    work.mkdir(parents=True)
                    print(f"BENCH {name} :: {label} :: rep {i + 1}", flush=True)
                    reps.append(fn(src, work))
                cell = v2.summarize(reps, logical)
                cell["status"] = "ok"
                good += 1
            except BaseException as exc:
                cell = v3.failure(exc, started)
                if cell["status"] == "timeout":
                    timeouts += 1
                else:
                    errors += 1
            entry["results"][label] = cell
            result["coverage"] = {
                "attempted_cells": attempted,
                "ok_cells": good,
                "timeout_cells": timeouts,
                "error_cells": errors,
            }
            v3.persist(result, out)
            print(json.dumps({"corpus": name, "compressor": label, **cell}, sort_keys=True), flush=True)

    result["coverage"] = {
        "attempted_cells": attempted,
        "ok_cells": good,
        "timeout_cells": timeouts,
        "error_cells": errors,
    }
    result["complete_with_recorded_failures"] = True
    v3.persist(result, out, final=True)
    print("RESULT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
