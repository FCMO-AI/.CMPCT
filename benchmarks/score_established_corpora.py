#!/usr/bin/env python3
from __future__ import annotations

"""Build a transparent multi-axis scorecard from established-corpora v3 JSON.

This intentionally does not collapse compression, speed, memory and coverage into one opaque number.
For each CMPCT engine it reports direct pairwise geometric-mean indices against mature baselines,
direct CMPCT-generation comparisons, coverage/failures, native-container size rank, mature density-frontier
distance, and Pareto-front participation. Ratios use 100 = parity to the named baseline; above 100 is better
for the CMPCT engine on that axis.

The comparison remains structural research evidence, not a release gate: deterministic tar+stream compressors
and native archive containers expose different random-access, metadata and recovery semantics.
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable

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


def axis_index(
    rows: list[tuple[str, dict[str, Any], dict[str, Any]]],
    value: Callable[[dict[str, Any]], float],
) -> tuple[float | None, int]:
    ratios: list[float] = []
    for _, engine, baseline in rows:
        e = float(value(engine))
        b = float(value(baseline))
        # GNU time has centisecond resolution here. A reported 0.00 s is below measurement resolution,
        # not evidence of infinite speed, so exclude that corpus from this timing axis rather than inventing
        # an epsilon or a giant score.
        if not (e > 0 and b > 0 and math.isfinite(e) and math.isfinite(b)):
            continue
        ratios.append(b / e)
    gm = gmean(ratios)
    return ((100.0 * gm) if gm is not None else None, len(ratios))


def pairwise(corpora: dict[str, dict[str, Any]], engine: str, baseline: str) -> dict[str, Any]:
    rows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for corpus, entry in corpora.items():
        e = entry.get("results", {}).get(engine)
        b = entry.get("results", {}).get(baseline)
        if ok(e) and ok(b):
            rows.append((corpus, e, b))

    size, size_n = axis_index(rows, lambda c: float(c["bytes"]))
    create, create_n = axis_index(rows, lambda c: float(c["create"]["median_s"]))
    extract, extract_n = axis_index(rows, lambda c: float(c["extract"]["median_s"]))
    memory, memory_n = axis_index(rows, lambda c: rss(c, "create"))
    wins = sum(1 for _, e, b in rows if e["bytes"] < b["bytes"])
    ties = sum(1 for _, e, b in rows if e["bytes"] == b["bytes"])
    return {
        "common_corpora": len(rows),
        "size_index": size,
        "size_index_corpora": size_n,
        "create_speed_index": create,
        "create_speed_index_corpora": create_n,
        "extract_speed_index": extract,
        "extract_speed_index_corpora": extract_n,
        "create_memory_index": memory,
        "create_memory_index_corpora": memory_n,
        "size_wins": wins,
        "size_ties": ties,
        "size_losses": len(rows) - wins - ties,
        "corpora": [r[0] for r in rows],
    }


def mature_size_frontier(corpora: dict[str, dict[str, Any]], engine: str) -> dict[str, Any]:
    ratios: list[float] = []
    wins = ties = losses = 0
    rows: list[dict[str, Any]] = []
    for corpus, entry in corpora.items():
        results = entry.get("results", {})
        e = results.get(engine)
        mature = [(name, results.get(name)) for name in MATURE]
        mature = [(name, cell) for name, cell in mature if ok(cell)]
        if not (ok(e) and mature):
            continue
        best_name, best = min(mature, key=lambda kv: int(kv[1]["bytes"]))
        ebytes = int(e["bytes"])
        bbytes = int(best["bytes"])
        ratios.append(bbytes / ebytes)
        if ebytes < bbytes:
            wins += 1
        elif ebytes == bbytes:
            ties += 1
        else:
            losses += 1
        rows.append({
            "corpus": corpus,
            "best_mature": best_name,
            "best_mature_bytes": bbytes,
            "engine_bytes": ebytes,
            "index": 100.0 * bbytes / ebytes,
        })
    gm = gmean(ratios)
    return {
        "definition": "per-corpus smallest successful mature-compressor artifact; an oracle reference, not one deployable compressor",
        "corpora": len(rows),
        "size_index": (100.0 * gm) if gm is not None else None,
        "size_wins": wins,
        "size_ties": ties,
        "size_losses": losses,
        "rows": rows,
    }


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    av = (a["bytes"], a["create"]["median_s"], a["extract"]["median_s"], rss(a, "create"))
    bv = (b["bytes"], b["create"]["median_s"], b["extract"]["median_s"], rss(b, "create"))
    # A zero timing is a censored measurement at timer resolution, so it cannot establish dominance.
    if not all(math.isfinite(float(x)) and float(x) > 0 for x in av + bv):
        return False
    return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))


def engine_summary(corpora: dict[str, dict[str, Any]], engine: str) -> dict[str, Any]:
    attempted = success = timeout = error = 0
    pareto = 0
    native_ranks: list[float] = []
    weighted_logical = weighted_bytes = 0
    for entry in corpora.values():
        results = entry.get("results", {})
        cell = results.get(engine)
        if cell is None:
            continue
        attempted += 1
        status = cell.get("status", "ok")
        if status != "ok":
            timeout += int(status == "timeout")
            error += int(status != "timeout")
            continue
        success += 1
        weighted_logical += int(entry["logical_bytes"])
        weighted_bytes += int(cell["bytes"])
        candidates = {
            k: v for k, v in results.items()
            if k in (*CMPCT_ENGINES, *MATURE) and ok(v)
        }
        if candidates and not any(
            name != engine and dominates(other, cell) for name, other in candidates.items()
        ):
            pareto += 1
        native = [
            (k, v) for k, v in results.items()
            if k in (*NATIVE_ARCHIVES, engine) and ok(v)
        ]
        if native:
            ordered = sorted(native, key=lambda kv: kv[1]["bytes"])
            native_ranks.append(1 + next(i for i, (k, _) in enumerate(ordered) if k == engine))
    return {
        "attempted_corpora": attempted,
        "successful_corpora": success,
        "coverage_pct": (100.0 * success / attempted) if attempted else 0.0,
        "timeout_corpora": timeout,
        "error_corpora": error,
        "weighted_size_ratio_on_successful_corpora": (
            weighted_bytes / weighted_logical if weighted_logical else None
        ),
        "pareto_front_corpora": pareto,
        "pareto_front_share_pct": (100.0 * pareto / success) if success else 0.0,
        "native_archive_size_rank_mean": (
            sum(native_ranks) / len(native_ranks) if native_ranks else None
        ),
        "native_archive_rank_corpora": len(native_ranks),
        "mature_size_frontier": mature_size_frontier(corpora, engine),
        "pairwise": {baseline: pairwise(corpora, engine, baseline) for baseline in MATURE},
        "direct_cmpct": {
            baseline: pairwise(corpora, engine, baseline)
            for baseline in CMPCT_ENGINES if baseline != engine
        },
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
        "Zero-duration timer samples are excluded from timing indices instead of being treated as infinite speed.",
        "The mature size frontier is a per-corpus oracle (smallest successful mature result), not a single deployable compressor.",
        "",
    ]
    for engine, s in score["engines"].items():
        f = s["mature_size_frontier"]
        lines += [
            f"## {engine}",
            "",
            f"Coverage: **{fmt(s['coverage_pct'])}%** ({s['successful_corpora']}/{s['attempted_corpora']} corpora); timeouts={s['timeout_corpora']}, errors={s['error_corpora']}.",
            f"Mature density-frontier index: **{fmt(f['size_index'])}** across {f['corpora']} common corpora (W/T/L {f['size_wins']}/{f['size_ties']}/{f['size_losses']}).",
            f"Pareto-front participation: **{fmt(s['pareto_front_share_pct'])}%** of successful corpora. Mean native-archive size rank: **{fmt(s['native_archive_size_rank_mean'])}**.",
            "",
            "### Mature baselines",
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
        direct = [(name, p) for name, p in s["direct_cmpct"].items() if p["common_corpora"]]
        if direct:
            lines += [
                "",
                "### Direct CMPCT lineage",
                "",
                "| Baseline | Common | Size | Create speed | Extract speed | Create memory | Size W/T/L |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for baseline, p in direct:
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
        "Treat pairwise rows and the mature oracle as measured reference axes, not as a universal winner claim.",
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
        "schema": "cmpct-established-corpora-scorecard-v2",
        "axis_definition": "100=baseline parity; >100 favors CMPCT; geometric mean across common successful, measurable corpora",
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
