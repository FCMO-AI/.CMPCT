#!/usr/bin/env python3
from __future__ import annotations

"""Build a transparent multi-axis scorecard from established-corpora v3 JSON.

This intentionally does not collapse compression, speed, memory and coverage into one opaque number.
For each CMPCT engine it reports direct pairwise geometric-mean indices against mature baselines,
coverage/failures, native-container size rank, and Pareto-front participation. Ratios are expressed with
100 = parity to the named baseline; above 100 is better for the CMPCT engine on that axis.

The comparison remains structural research evidence, not a release gate: deterministic tar+stream
compressors and native archive containers expose different random-access, metadata and recovery semantics.
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

CMPCT_ENGINES = (
    "cmpct-v0.29-shipping-r24",
    "cmpct-v0.29-research",
    "cmpct-v0.30-canonical-snapshot",
)
MATURE = (
    "zip-deflate-9",
    "zstd-3",
    "zstd-19",
    "7z-lzma2-9",
    "xz-9e",
    "gzip-9",
    "bzip2-9",
)
NATIVE_ARCHIVES = ("zip-deflate-9", "7z-lzma2-9")


def gmean(xs: Iterable[float]) -> float | None:
    vals = [float(x) for x in xs if x > 0 and math.isfinite(float(x))]
    if not vals:
        return None
    return math.exp(sum(math.log(x) for x in vals) / len(vals))


def ok(cell: dict[str, Any] | None) -> bool:
    return bool(cell) and cell.get("status", "ok") == "ok"


def rss(cell: dict[str, Any], phase: str) -> float:
    samples = cell.get(f"{phase}_peak_rss_kib_samples") or []
    return float(max(samples)) if samples else math.nan


def load(paths: list[Path]) -> dict[str, dict[str, Any]]:
    corpora: dict[str, dict[str, Any]] = {}
    for path in paths:
        doc = json.loads(path.read_text())
        for name, entry in doc.get("corpora", {}).items():
            if name in corpora:
                raise SystemExit(f"duplicate corpus {name!r} across inputs")
            corpora[name] = entry
    return corpora


def pairwise(corpora: dict[str, dict[str, Any]], engine: str, baseline: str) -> dict[str, Any]:
    rows = []
    for corpus, entry in corpora.items():
        e = entry.get("results", {}).get(engine)
        b = entry.get("results", {}).get(baseline)
        if not (ok(e) and ok(b)):
            continue
        rows.append((corpus, e, b))
    def idx(fn):
        # 100 = parity. Because lower is better on every measured axis, baseline/engine is the score.
        return None if not rows else 100.0 * gmean(fn(e, b) for _, e, b in rows)
    size = idx(lambda e, b: b["bytes"] / e["bytes"])
    create = idx(lambda e, b: b["create"]["median_s"] / e["create"]["median_s"])
    extract = idx(lambda e, b: b["extract"]["median_s"] / e["extract"]["median_s"])
    memory = idx(lambda e, b: rss(b, "create") / rss(e, "create") if rss(e, "create") > 0 and rss(b, "create") > 0 else math.nan)
    wins = sum(1 for _, e, b in rows if e["bytes"] < b["bytes"])
    ties = sum(1 for _, e, b in rows if e["bytes"] == b["bytes"])
    return {
        "common_corpora": len(rows),
        "size_index": size,
        "create_speed_index": create,
        "extract_speed_index": extract,
        "create_memory_index": memory,
        "size_wins": wins,
        "size_ties": ties,
        "size_losses": len(rows) - wins - ties,
        "corpora": [r[0] for r in rows],
    }


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    av = (a["bytes"], a["create"]["median_s"], a["extract"]["median_s"], rss(a, "create"))
    bv = (b["bytes"], b["create"]["median_s"], b["extract"]["median_s"], rss(b, "create"))
    if not all(math.isfinite(x) for x in av + bv):
        return False
    return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))


def engine_summary(corpora: dict[str, dict[str, Any]], engine: str) -> dict[str, Any]:
    attempted = success = timeout = error = 0
    pareto = native_rank_rows = 0
    native_ranks: list[float] = []
    weighted_logical = weighted_bytes = 0
    for _, entry in corpora.items():
        results = entry.get("results", {})
        cell = results.get(engine)
        if cell is None:
            continue
        attempted += 1
        status = cell.get("status", "ok")
        if status != "ok":
            timeout += status == "timeout"
            error += status != "timeout"
            continue
        success += 1
        weighted_logical += int(entry["logical_bytes"])
        weighted_bytes += int(cell["bytes"])
        candidates = {k: v for k, v in results.items() if k in (*CMPCT_ENGINES, *MATURE) and ok(v)}
        if candidates and not any(name != engine and dominates(other, cell) for name, other in candidates.items()):
            pareto += 1
        native = [(k, v) for k, v in results.items() if k in (*NATIVE_ARCHIVES, engine) and ok(v)]
        if native:
            native_rank_rows += 1
            ordered = sorted(native, key=lambda kv: kv[1]["bytes"])
            native_ranks.append(1 + next(i for i, (k, _) in enumerate(ordered) if k == engine))
    return {
        "attempted_corpora": attempted,
        "successful_corpora": success,
        "coverage_pct": (100.0 * success / attempted) if attempted else 0.0,
        "timeout_corpora": timeout,
        "error_corpora": error,
        "weighted_size_ratio_on_successful_corpora": (weighted_bytes / weighted_logical) if weighted_logical else None,
        "pareto_front_corpora": pareto,
        "pareto_front_share_pct": (100.0 * pareto / success) if success else 0.0,
        "native_archive_size_rank_mean": (sum(native_ranks) / len(native_ranks)) if native_ranks else None,
        "native_archive_rank_corpora": native_rank_rows,
        "pairwise": {baseline: pairwise(corpora, engine, baseline) for baseline in MATURE},
    }


def fmt(v: Any) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def markdown(score: dict[str, Any]) -> str:
    lines = [
        "# CMPCT established-corpora scorecard",
        "",
        "Indices use **100 = parity with the named baseline**. Above 100 is better for CMPCT on that axis; below 100 is worse.",
        "No single weighted composite is published because the correct tradeoff between bytes, time, memory, and semantics is workload-dependent.",
        "",
    ]
    for engine, s in score["engines"].items():
        lines += [
            f"## {engine}",
            "",
            f"Coverage: **{fmt(s['coverage_pct'])}%** ({s['successful_corpora']}/{s['attempted_corpora']} corpora); timeouts={s['timeout_corpora']}, errors={s['error_corpora']}.",
            f"Pareto-front participation: **{fmt(s['pareto_front_share_pct'])}%** of successful corpora. Mean native-archive size rank: **{fmt(s['native_archive_size_rank_mean'])}**.",
            "",
            "| Baseline | Common | Size | Create speed | Extract speed | Create memory | Size W/T/L |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for baseline, p in s["pairwise"].items():
            lines.append(
                f"| {baseline} | {p['common_corpora']} | {fmt(p['size_index'])} | {fmt(p['create_speed_index'])} | "
                f"{fmt(p['extract_speed_index'])} | {fmt(p['create_memory_index'])} | "
                f"{p['size_wins']}/{p['size_ties']}/{p['size_losses']} |"
            )
        lines.append("")
    lines += [
        "## Interpretation boundary",
        "",
        "Native archive containers and deterministic tar+stream compressors are both shown because they answer different useful questions. "
        "Their size/time numbers are informative but not semantically identical: random-member access, metadata fidelity, authentication, recovery, and selective-read cost differ. "
        "Treat pairwise rows as measured axes, not as a universal winner claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--markdown-out", type=Path)
    args = ap.parse_args()
    corpora = load(args.inputs)
    score = {
        "schema": "cmpct-established-corpora-scorecard-v1",
        "axis_definition": "100=baseline parity; >100 favors CMPCT; geometric mean across common successful corpora",
        "corpus_count": len(corpora),
        "engines": {engine: engine_summary(corpora, engine) for engine in CMPCT_ENGINES},
    }
    rendered = markdown(score)
    if args.json_out:
        args.json_out.write_text(json.dumps(score, indent=2))
    if args.markdown_out:
        args.markdown_out.write_text(rendered)
    if not args.json_out and not args.markdown_out:
        print(rendered)


if __name__ == "__main__":
    main()
