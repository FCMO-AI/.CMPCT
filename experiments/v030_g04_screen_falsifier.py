from __future__ import annotations

"""Bounded falsifier for a zero-threshold G04 Hierarchical-Geometry early reject.

Question: can the already-paid level-6 screen prove enough no-headroom to skip level-19 finalists
without changing any frozen-workload complete-artifact bytes?  This is an oracle only.  It does not
change canonical product code, thresholds, workloads, or release gates.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_hierarchical_geometry as HG


def _guarded_audition(raw: bytes) -> dict:
    base_codec, base_payload = HG.G._compress_physical(raw)
    best = {
        "kind": "direct", "primary": None, "secondary": None, "prefix_planes": False,
        "physical": raw, "codec": base_codec, "payload": base_payload,
        "payload_bytes": len(base_payload), "saving_bytes": 0,
        "screened_candidates": 0, "exact_finalists": 0,
    }
    if len(raw) < HG.MIN_NODE_BYTES:
        best["screen_direct_bytes"] = HG._compressed_size(raw, HG.SCREEN_LEVEL)
        best["screen_best_bytes"] = None
        best["screen_early_reject"] = True
        return best

    started = time.perf_counter()
    direct_screen = HG._compressed_size(raw, HG.SCREEN_LEVEL)
    screened: list[tuple[int, int, int, bool]] = []
    for primary in HG.primary_candidates(raw):
        rows = raw.split(bytes((primary,)))
        for secondary in HG.secondary_candidates(rows, primary):
            for prefix_planes in (False, True):
                try:
                    transformed = HG.hierarchy_forward(raw, primary, secondary, prefix_planes=prefix_planes)
                except ValueError:
                    continue
                if HG.hierarchy_inverse(transformed, len(raw)) != raw:
                    raise RuntimeError("screen falsifier candidate failed exact inverse")
                screen_bytes = HG._compressed_size(transformed, HG.SCREEN_LEVEL)
                screened.append((screen_bytes, primary, secondary, prefix_planes))
    screened.sort(key=lambda row: (row[0], row[3], row[1], row[2]))
    screen_elapsed = time.perf_counter() - started
    best_screen = screened[0][0] if screened else None
    best.update({
        "screened_candidates": len(screened),
        "screen_direct_bytes": direct_screen,
        "screen_best_bytes": best_screen,
        "screen_margin_bytes": None if best_screen is None else direct_screen - best_screen,
        "screen_elapsed_s": screen_elapsed,
    })

    # Zero-threshold discriminator: if no transformed candidate beats direct bytes at the cheap screen
    # level, decline expensive level-19 finalists.  This is the only policy under test.
    if best_screen is None or best_screen >= direct_screen:
        best["screen_early_reject"] = True
        return best
    best["screen_early_reject"] = False

    finalists = screened[:HG.MAX_EXACT_FINALISTS]
    exact_started = time.perf_counter()
    for _, primary, secondary, prefix_planes in finalists:
        transformed = HG.hierarchy_forward(raw, primary, secondary, prefix_planes=prefix_planes)
        if HG.hierarchy_inverse(transformed, len(raw)) != raw:
            raise RuntimeError("screen falsifier finalist failed exact inverse")
        codec, payload = HG.G._compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving < HG.MIN_PAYLOAD_SAVING:
            continue
        rank = (len(payload), 0 if prefix_planes else 1, primary, secondary)
        incumbent = (
            best["payload_bytes"], 0 if best["prefix_planes"] else 1,
            best["primary"] if best["primary"] is not None else 1 << 30,
            best["secondary"] if best["secondary"] is not None else 1 << 30,
        )
        if rank < incumbent:
            best.update({
                "kind": "hierarchical", "primary": primary, "secondary": secondary,
                "prefix_planes": prefix_planes, "physical": transformed, "codec": codec,
                "payload": payload, "payload_bytes": len(payload), "saving_bytes": saving,
            })
    best["exact_finalists"] = len(finalists)
    best["exact_elapsed_s"] = time.perf_counter() - exact_started
    return best


def _build_corpora(work_root: Path):
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "g04_screen_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "g04_screen_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "g04_screen_repair")
    repair.install_generation_hooks(neutral)
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            expected = accepted[(suite, workload.name)]
            live = G04.treehash(workload)
            if live != expected["tree_sha256"]:
                raise RuntimeError(f"source drift: {suite}/{workload.name}: {live} != {expected['tree_sha256']}")
            yield suite, workload


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = []
    original = HG.audition
    for index, (suite, source) in enumerate(_build_corpora(work_root / "corpus")):
        row_root = work_root / "archives" / suite / source.name
        row_root.mkdir(parents=True, exist_ok=True)
        original_path = row_root / "original.cmpct"
        guarded_path = row_root / "guarded.cmpct"
        order = ("original", "guarded") if index % 2 == 0 else ("guarded", "original")
        stats = {}
        try:
            for arm in order:
                HG.audition = original if arm == "original" else _guarded_audition
                started = time.perf_counter()
                path = original_path if arm == "original" else guarded_path
                arm_stats = G04.build(source, path)
                arm_stats = dict(arm_stats)
                arm_stats["measured_wall_s"] = time.perf_counter() - started
                verified = G04.strong_verify(path)
                if not verified.get("ok"):
                    raise RuntimeError(f"G04 verification failed: {suite}/{source.name}/{arm}")
                stats[arm] = arm_stats
        finally:
            HG.audition = original
        row = {
            "suite": suite, "name": source.name, "order": list(order),
            "original_bytes": original_path.stat().st_size,
            "guarded_bytes": guarded_path.stat().st_size,
            "byte_delta": guarded_path.stat().st_size - original_path.stat().st_size,
            "original_selected": stats["original"].get("selected"),
            "guarded_selected": stats["guarded"].get("selected"),
            "original_wall_s": stats["original"]["measured_wall_s"],
            "guarded_wall_s": stats["guarded"]["measured_wall_s"],
            "wall_delta_s": stats["guarded"]["measured_wall_s"] - stats["original"]["measured_wall_s"],
            "original_auditions": stats["original"].get("auditions", []),
            "guarded_auditions": stats["guarded"].get("auditions", []),
        }
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("suite", "name", "byte_delta", "wall_delta_s")}), flush=True)
    regressions = [f"{r['suite']}/{r['name']}" for r in rows if r["guarded_bytes"] > r["original_bytes"]]
    changed = [f"{r['suite']}/{r['name']}" for r in rows if r["guarded_bytes"] != r["original_bytes"]]
    return {
        "schema": "cmpct-v030-g04-screen-falsifier-v1",
        "policy": "skip level-19 hierarchical finalists iff best level-6 transformed size >= direct level-6 size",
        "rows": rows,
        "regressions": regressions,
        "changed_complete_artifacts": changed,
        "gate": {"zero_complete_artifact_regressions": not regressions, "passed": not regressions},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"regressions": result["regressions"], "changed": result["changed_complete_artifacts"]}, indent=2))
    if not result["gate"]["passed"]:
        raise SystemExit("G04 screen discriminator changed a complete-artifact winner")


if __name__ == "__main__":
    main()
