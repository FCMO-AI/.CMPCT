#!/usr/bin/env python3
from __future__ import annotations

"""Fault-isolated established-corpus lane for frozen v0.30 versus same-run shipping v0.29.

The shipping anchor is deliberately rerun in the same job so v0.30 runtime ratios do not depend on a
different GitHub runner. Strong mature-compressor sizes come from the separate baseline lane because
archive size is deterministic under the benchmark contract; cross-run wall times are not treated as paired.
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


def runners(py29: str, py30: str, repo30: str) -> list[tuple[str, Callable[[Path, Path], dict[str, Any]]]]:
    return [
        ("cmpct-v0.29-shipping-r24", lambda s, w: v2.cmpct_shipping(s, w, py29)),
        ("cmpct-v0.30-canonical-snapshot", lambda s, w: v2.cmpct_module(s, w, py30, repo30, "v030-canonical")),
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
    py30 = os.environ["CMPCT_V030_PYTHON"]
    repo30 = os.environ["CMPCT_V030_REPO"]

    result: dict[str, Any] = {
        "schema": "cmpct-established-corpora-v030-anchor-v1",
        "purpose": "same-run frozen-v0.30 versus shipping-v0.29 anchor; research evidence, not release credit or website evidence",
        "provenance": {
            "v029_release_sha": os.environ["CMPCT_V029_SHA"],
            "v030_snapshot_sha": os.environ["CMPCT_V030_SHA"],
            "benchmark_sha": os.environ.get("GITHUB_SHA"),
            "runner": os.environ.get("RUNNER_NAME"),
        },
        "semantics": {
            "timing": "fresh-process GNU time; v0.29 shipping and v0.30 snapshot share the same runner and corpus bytes",
            "timeout_policy": f"same {v2.TIMEOUT}s process ceiling for both CMPCT cells; timeout remains a negative coverage result",
            "roundtrip": "relative path + byte length + SHA-256 must match exactly",
            "v030_boundary": "canonical snapshot only; rejected research candidates do not receive canonical byte credit",
            "scores": "no weighted universal score in raw evidence",
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

        for label, fn in runners(py29, py30, repo30):
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
