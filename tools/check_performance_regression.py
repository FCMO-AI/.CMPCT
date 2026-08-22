#!/usr/bin/env python3
from __future__ import annotations

"""Fail a release when the candidate moves CMPCT behind its direct base.

Size is deterministic and therefore has zero tolerance. Timing is inherently noisy on shared runners,
so a timing regression must clear *both* a relative and an absolute envelope before it is considered
real. This is deliberately stricter than comparing two unrelated historical CI machines: base and
candidate are expected to have been benchmarked in the same workflow job.

The two ``--max-*-regression`` options are retained only as compatibility aliases for older workflow callers.
``--max-time-regression`` maps to the current relative timing envelope. ``--max-size-regression`` is accepted but
can never relax the zero-byte size law; any non-negative supplied value is ignored for admission. This lets stale
callers fail or pass on measured data rather than argparse drift without weakening current release policy.
"""

import argparse
import json
from pathlib import Path
from typing import Any

TIMING_FIELDS = ("create_s_median", "extract_s_median")
LAYERS = ("library", "cli")


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-zip-parity-v1":
        raise ValueError(f"{path}: unsupported benchmark schema {data.get('schema')!r}")
    if not isinstance(data.get("corpora"), dict):
        raise ValueError(f"{path}: missing corpora")
    return data


def pct(delta: float) -> str:
    return f"{delta * 100:+.2f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--timing-relative", type=float, default=0.05)
    ap.add_argument("--timing-absolute-ms", type=float, default=3.0)
    ap.add_argument("--max-time-regression", type=float, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--max-size-regression", type=float, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--summary", type=Path)
    args = ap.parse_args()

    if args.max_time_regression is not None:
        if args.max_time_regression < 0:
            ap.error("--max-time-regression must be non-negative")
        args.timing_relative = args.max_time_regression
    if args.max_size_regression is not None and args.max_size_regression < 0:
        ap.error("--max-size-regression must be non-negative")

    base = load(args.base)
    cand = load(args.candidate)
    failures: list[str] = []
    improvements: list[str] = []
    observations: list[str] = []

    base_names = set(base["corpora"])
    cand_names = set(cand["corpora"])
    if base_names != cand_names:
        missing = sorted(base_names - cand_names)
        added = sorted(cand_names - base_names)
        failures.append(f"corpus set changed during release gate; missing={missing}, added={added}")

    for name in sorted(base_names & cand_names):
        b_row = base["corpora"][name]
        c_row = cand["corpora"][name]
        for layer in LAYERS:
            b_cmpct = b_row[layer]["cmpct"]
            c_cmpct = c_row[layer]["cmpct"]

            b_bytes = int(b_cmpct["bytes"])
            c_bytes = int(c_cmpct["bytes"])
            if c_bytes > b_bytes:
                failures.append(f"{name}/{layer}: archive size {b_bytes:,} -> {c_bytes:,} B (+{c_bytes-b_bytes:,} B)")
            elif c_bytes < b_bytes:
                improvements.append(f"{name}/{layer}: archive size {b_bytes:,} -> {c_bytes:,} B ({b_bytes-c_bytes:,} B smaller)")

            for field in TIMING_FIELDS:
                bv = float(b_cmpct[field])
                cv = float(c_cmpct[field])
                rel = (cv / bv - 1.0) if bv else 0.0
                abs_ms = (cv - bv) * 1000.0
                confirmed = rel > args.timing_relative and abs_ms > args.timing_absolute_ms
                if confirmed:
                    failures.append(
                        f"{name}/{layer}/{field}: {bv*1000:.3f} -> {cv*1000:.3f} ms "
                        f"({pct(rel)}, +{abs_ms:.3f} ms)"
                    )
                elif cv < bv:
                    improvements.append(
                        f"{name}/{layer}/{field}: {bv*1000:.3f} -> {cv*1000:.3f} ms ({pct(rel)})"
                    )
                else:
                    observations.append(
                        f"{name}/{layer}/{field}: apparent +{abs_ms:.3f} ms / {pct(rel)} remains inside noise envelope"
                    )

    lines = [
        "# CMPCT release performance gate",
        "",
        "Size policy: **0 byte regression allowed**.",
        f"Timing policy: fail when slowdown exceeds both **{args.timing_relative*100:.1f}%** and **{args.timing_absolute_ms:.1f} ms** on the same runner.",
        "",
        f"Result: **{'FAIL' if failures else 'PASS'}**",
        "",
        f"Confirmed regressions: **{len(failures)}**",
        f"Measured improvements: **{len(improvements)}**",
        "",
    ]
    if args.max_size_regression is not None:
        lines += [
            f"Compatibility note: deprecated --max-size-regression={args.max_size_regression:g} was supplied; current zero-byte size policy remains authoritative.",
            "",
        ]
    if failures:
        lines += ["## Regressions", *[f"- {x}" for x in failures], ""]
    if improvements:
        lines += ["## Improvements", *[f"- {x}" for x in improvements[:40]], ""]
    if observations:
        lines += ["## Inside timing noise envelope", *[f"- {x}" for x in observations[:40]], ""]

    report = "\n".join(lines) + "\n"
    print(report)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(report, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
