from __future__ import annotations

"""Fresh-process causal attribution for the promoted G04 DGO1 inverse.

Build one shipping r25 ML archive, then extract it in fresh subprocesses with exactly one semantic difference:
`fast` keeps the release-only one-buffer inverse; `historical` swaps the isolated canonical reader references back to
`C._PRESERVED_DELIMITER_INVERSE`. Archive bytes, manifest, policy, publication, filesystem restoration and all
other code remain identical. This measures the end-to-end product contribution of the promoted inverse itself.

Diagnostic only: no frozen runtime threshold changes and zero release credit.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import v030_release_performance as PERF

SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPS = 5


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    p = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"child failed {p.returncode}: {p.stderr}\n{p.stdout}")
    rows = [x for x in p.stdout.splitlines() if x.strip().startswith("{")]
    if not rows:
        raise RuntimeError(f"child emitted no JSON: {p.stdout}")
    return json.loads(rows[-1])


def child(archive: Path, destination: Path, arm: str) -> dict:
    import resource
    from experiments import entropygraph_v030_release_product as E

    C = E.C
    if arm == "historical":
        historical = C._PRESERVED_DELIMITER_INVERSE
        C.SHARED.G.O.delimiter_inverse = historical
        if getattr(C.POLICY.R.G04, "O", None) is not None:
            C.POLICY.R.G04.O.delimiter_inverse = historical
    elif arm != "fast":
        raise ValueError(arm)

    if destination.exists():
        shutil.rmtree(destination)
    started = time.perf_counter()
    E.extract(archive, destination)
    wall = time.perf_counter() - started
    tree = E.treehash(destination)
    return {
        "arm": arm,
        "wall_s": wall,
        "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "tree_sha256": tree,
        "inverse_is_historical": C.SHARED.G.O.delimiter_inverse is C._PRESERVED_DELIMITER_INVERSE,
    }


def parent(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]
    archive = work_root / "v030.cmpct"
    pack = _json_child([
        sys.executable, str(PERF.WORKER), "--engine", "v030", "--op", "pack",
        "--source", str(source), "--archive", str(archive),
    ])
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError("focused ML source no longer publishes g04-overlay")

    samples = {"fast": [], "historical": []}
    for rep in range(REPS):
        order = ("fast", "historical") if rep % 2 == 0 else ("historical", "fast")
        for arm in order:
            row = _json_child([
                sys.executable, __file__, "--child", "--archive", str(archive),
                "--destination", str(work_root / f"extract-{arm}-{rep}"), "--arm", arm,
            ])
            if row["tree_sha256"] != pack["tree_sha256"]:
                raise RuntimeError(f"{arm} extraction tree identity mismatch")
            if row["inverse_is_historical"] != (arm == "historical"):
                raise RuntimeError(f"{arm} inverse toggle did not bind")
            samples[arm].append(row)

    fast = [float(r["wall_s"]) for r in samples["fast"]]
    historical = [float(r["wall_s"]) for r in samples["historical"]]
    fm = statistics.median(fast)
    hm = statistics.median(historical)
    return {
        "schema": "cmpct-v030-g04-fastpath-causal-extract-v1",
        "status": "PASS",
        "evidence_class": "focused-product-causal-attribution",
        "product_release_credit": False,
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "same_archive_bytes": True,
            "same_shipping_extract_frontdoor": True,
            "only_reader_inverse_binding_differs": True,
            "fresh_process_each_extract": True,
            "repetitions_each": REPS,
            "runtime_thresholds_changed": False,
        },
        "pack": pack,
        "samples": samples,
        "comparison": {
            "fast_median_s": fm,
            "historical_median_s": hm,
            "fast_over_historical_ratio": fm / max(hm, 1e-12),
            "fast_time_reduction_fraction": (hm - fm) / max(hm, 1e-12),
            "saved_s": hm - fm,
            "fast_max_rss_kib": max(int(r["peak_rss_kib"]) for r in samples["fast"]),
            "historical_max_rss_kib": max(int(r["peak_rss_kib"]) for r in samples["historical"]),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--destination", type=Path)
    ap.add_argument("--arm", choices=("fast", "historical"))
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-fastpath-causal-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-fastpath-causal.json"))
    args = ap.parse_args()
    if args.child:
        if args.archive is None or args.destination is None or args.arm is None:
            raise SystemExit("child requires --archive --destination --arm")
        print(json.dumps(child(args.archive, args.destination, args.arm), separators=(",", ":")), flush=True)
        return
    try:
        payload = parent(args.work_root)
    except BaseException as exc:
        payload = {
            "schema": "cmpct-v030-g04-fastpath-causal-extract-v1",
            "status": "HARNESS_FAILURE",
            "evidence_class": "focused-product-causal-attribution",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
