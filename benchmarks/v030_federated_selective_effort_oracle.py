from __future__ import annotations

"""Per-pack compression-effort frontier for the bounded C25EG01 candidate.

The all-15 admission evidence shows office and analytics already beat ZIP and solid Zstd-19 on both size and
verified creation time, but still miss the immutable accepted-v0.29 byte floor.  A global level increase is the
wrong question: it spends CPU on every physical pack even when only a small subset may own most of the remaining
byte opportunity.

This oracle profiles every *final* requested-Zstd-19 physical compression input produced by the exact C25EG01
representation.  For each unique raw pack it measures levels 1/3/6/9/12/15/19, including multiplicity when an
identical pack is emitted more than once.  It then computes:

1. the maximum byte saving possible from compression effort alone (all packs at their best measured level);
2. whether that upper bound can cross the accepted-v0.29 row at all;
3. the minimum measured extra compression CPU needed to reach the v0.29 floor, when reachable; and
4. the maximum saving available inside a conservative ZIP creation-time budget.

The selected modeled policy is rebuilt as a real C25EG01 archive, strongly verified, locality-audited and measured
against fresh ZIP/Deflate-9 and solid Zstd-19 comparators.  Probe/audition calls requested below level 19 remain
capped at level 1 exactly like the current candidate; only final physical payload compression is varied.

This is research evidence only.  It neither changes C25EG01's default level-1 policy nor authorizes selector,
native, Android or release promotion.  A red result is valuable: if even the all-best byte upper bound cannot beat
v0.29, the missing bytes are structural/canonical-framing debt rather than a compression-effort tuning problem.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_candidate as CAND
from experiments import entropygraph_v030_product_fs as FS

TARGETS = ("02_office_workspace", "04_analytics_and_database")
LEVELS = (1, 3, 6, 9, 12, 15, 19)
ROUNDS = 3
PROFILE_REPEATS = 3
TIME_BUCKET_MS = 1
# The full global-19 analytics build is historically <10 s.  Twenty seconds keeps the exact multi-choice DP bounded
# while comfortably spanning every useful compression-effort assignment seen in the accepted representation.
MAX_MODEL_EXTRA_MS = 20_000


def _h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _effective_payload_bytes(raw_len: int, compressed_len: int) -> int:
    # v0.25 stores raw bytes unless compressed payload buys >8 bytes, so model the exact final pack choice.
    return compressed_len if compressed_len + 8 < raw_len else raw_len


@contextmanager
def _engine(archive: Path, profile: Path, zc_impl):
    """Use the dedicated candidate identity while replacing only the research engine's compression callback."""
    with CAND._LOCK:
        old = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)
        V25.ROOT = profile
        V25.OUT = archive
        V25.MAG = CAND.MAGIC
        V25.TAIL = CAND.TAIL_MAGIC
        V25.zc = zc_impl
        try:
            yield
        finally:
            V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc = old


def _prepare(source: Path, parent: Path) -> tuple[Path, dict]:
    profile = parent / "profile"
    fs = FS.prepare_profile_tree(
        source,
        profile,
        max_path_bytes=CAND.MAX_PATH_BYTES,
        max_profile_files=CAND.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CAND.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CAND.MAX_MANIFEST_ENTRIES,
    )
    return profile, fs


def _profile_final_packs(source: Path, root: Path) -> dict:
    """Build level-1 bytes while measuring every final pack's multi-level size/time frontier."""
    profile, fs = _prepare(source, root / "profile-stage")
    archive = root / "profiled.c25eg01"
    original_zc = V25.zc
    table: dict[str, dict] = {}

    def profiled(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            return original_zc(raw, min(requested, 1))
        key = _h(raw)
        row = table.get(key)
        if row is None:
            measurements = {}
            outputs = {}
            for level in LEVELS:
                samples = []
                out = b""
                for _ in range(PROFILE_REPEATS):
                    started = time.perf_counter()
                    out = original_zc(raw, level)
                    samples.append(time.perf_counter() - started)
                outputs[level] = out
                measurements[level] = {
                    "compressed_bytes": len(out),
                    "effective_payload_bytes": _effective_payload_bytes(len(raw), len(out)),
                    "median_compress_s": statistics.median(samples),
                    "raw_compress_s": samples,
                }
            row = {
                "sha256": key,
                "raw_bytes": len(raw),
                "count": 0,
                "levels": measurements,
            }
            table[key] = row
        row["count"] += 1
        # Emit the exact current candidate policy during profiling.
        return outputs[1] if "outputs" in locals() else original_zc(raw, 1)

    started = time.perf_counter()
    with _engine(archive, profile, profiled):
        build_stats = dict(V25.build())
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = CAND.strong_verify(archive, expected_tree=CAND._treehash(source))
    verify_s = time.perf_counter() - started
    locality = CAND.locality_report(archive)
    if not verified.get("ok") or not locality.get("within_release_bounds"):
        raise RuntimeError("profiled level-1 C25EG01 candidate failed integrity/locality")

    rows = []
    for key, row in sorted(table.items()):
        base = row["levels"][1]
        options = []
        for level in LEVELS:
            item = row["levels"][level]
            saving = (int(base["effective_payload_bytes"]) - int(item["effective_payload_bytes"])) * int(row["count"])
            extra_s = max(0.0, float(item["median_compress_s"]) - float(base["median_compress_s"])) * int(row["count"])
            options.append({
                "level": level,
                "saving_bytes": int(saving),
                "extra_compress_s": extra_s,
                **item,
            })
        # Keep only Pareto-useful options: no more CPU and no fewer bytes saved than another choice.
        useful = []
        for option in options:
            dominated = any(
                other["saving_bytes"] >= option["saving_bytes"]
                and other["extra_compress_s"] <= option["extra_compress_s"]
                and (
                    other["saving_bytes"] > option["saving_bytes"]
                    or other["extra_compress_s"] < option["extra_compress_s"]
                )
                for other in options
            )
            if not dominated:
                useful.append(option)
        rows.append({**row, "options": useful})

    return {
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "verified_create_s": build_s + verify_s,
        "filesystem_manifest_bytes": int(fs["manifest_bytes"]),
        "build_stats": build_stats,
        "locality": locality,
        "packs": rows,
    }


def _dp(packs: list[dict], *, max_extra_ms: int) -> dict:
    """Exact multi-choice knapsack over 1 ms measured-extra-CPU buckets."""
    # state[time_ms] = (saving_bytes, selection_by_sha)
    states: dict[int, tuple[int, dict[str, int]]] = {0: (0, {})}
    for pack in packs:
        nxt: dict[int, tuple[int, dict[str, int]]] = {}
        for used_ms, (saved, selection) in states.items():
            for option in pack["options"]:
                extra_ms = int(math.ceil(float(option["extra_compress_s"]) * 1000.0))
                total_ms = used_ms + extra_ms
                if total_ms > max_extra_ms:
                    continue
                total_saved = saved + int(option["saving_bytes"])
                current = nxt.get(total_ms)
                if current is None or total_saved > current[0]:
                    chosen = dict(selection)
                    if int(option["level"]) != 1:
                        chosen[str(pack["sha256"])] = int(option["level"])
                    nxt[total_ms] = (total_saved, chosen)
        # Pareto-prune states whose saving is no better than a lower/equal CPU state.
        best_saved = -1
        states = {}
        for used_ms in sorted(nxt):
            saved, selection = nxt[used_ms]
            if saved > best_saved:
                states[used_ms] = (saved, selection)
                best_saved = saved
    return {"states": states}


def _policy_build(source: Path, root: Path, selection: dict[str, int]) -> dict:
    profile, _ = _prepare(source, root / "profile-stage")
    archive = root / "candidate.c25eg01"
    original_zc = V25.zc

    def selective(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            return original_zc(raw, min(requested, 1))
        return original_zc(raw, int(selection.get(_h(raw), 1)))

    started = time.perf_counter()
    with _engine(archive, profile, selective):
        V25.build()
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = CAND.strong_verify(archive, expected_tree=CAND._treehash(source))
    verify_s = time.perf_counter() - started
    locality = CAND.locality_report(archive)
    if not verified.get("ok") or not locality.get("within_release_bounds"):
        raise RuntimeError("selective-effort candidate failed integrity/locality")
    return {
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "verified_create_s": build_s + verify_s,
        "locality": locality,
    }


def _comparators(source: Path, root: Path) -> dict:
    expected_tree = EXT._tree(source)
    samples = {"zip": [], "zstd19": []}
    sizes = {"zip": set(), "zstd19": set()}
    for round_index in range(ROUNDS):
        order = ("zip", "zstd19") if round_index % 2 == 0 else ("zstd19", "zip")
        for name in order:
            lane = root / f"cmp-{round_index}-{name}"
            lane.mkdir(parents=True)
            if name == "zip":
                result = EXT._zip(source, lane / "archive.zip", lane / "out")
            else:
                result = EXT._tar_zstd(source, lane / "archive.tar.zst", lane / "out", lane)
                if not result.get("available"):
                    raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
            EXT._verify_extracted(lane / "out", expected_tree, name)
            samples[name].append(float(result["create_s"]))
            sizes[name].add(int(result["archive_bytes"]))
    if any(len(values) != 1 for values in sizes.values()):
        raise RuntimeError(f"nondeterministic comparator size: {sizes!r}")
    return {
        name: {
            "archive_bytes": next(iter(sizes[name])),
            "median_create_s": statistics.median(samples[name]),
            "raw_create_s": samples[name],
        }
        for name in ("zip", "zstd19")
    }


def _one(suite: str, name: str, source: Path, work: Path, accepted_v029_bytes: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg01-selective-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized-root")
        profile = _profile_final_packs(stage, root / "profile")
        comparators = _comparators(stage, root / "comparators")
        baseline_bytes = int(profile["archive_bytes"])
        required_saving = max(0, baseline_bytes - int(accepted_v029_bytes) + 1)

        max_saving = sum(
            max(int(option["saving_bytes"]) for option in pack["options"])
            for pack in profile["packs"]
        )
        all_best_floor = baseline_bytes - max_saving
        effort_can_cross_floor = all_best_floor < int(accepted_v029_bytes)

        model = _dp(profile["packs"], max_extra_ms=MAX_MODEL_EXTRA_MS)
        states = model["states"]
        minimum_floor_state = None
        for used_ms in sorted(states):
            saved, selection = states[used_ms]
            if saved >= required_saving:
                minimum_floor_state = {
                    "modeled_extra_ms": used_ms,
                    "modeled_saving_bytes": saved,
                    "selection": selection,
                }
                break

        # Preserve a material noise cushion: target at most 90% of same-run ZIP creation wall-clock.
        zip_budget_s = float(comparators["zip"]["median_create_s"]) * 0.90
        extra_budget_s = max(0.0, zip_budget_s - float(profile["verified_create_s"]))
        extra_budget_ms = int(math.floor(extra_budget_s * 1000.0))
        budget_states = [(ms, value) for ms, value in states.items() if ms <= extra_budget_ms]
        if budget_states:
            best_ms, (best_saved, best_selection) = max(budget_states, key=lambda item: (item[1][0], -item[0]))
        else:
            best_ms, best_saved, best_selection = 0, 0, {}

        # Rebuild the conservative ZIP-budget policy three times to test the model against real end-to-end cost.
        policy_samples = []
        policy_sizes = set()
        policy_locality = None
        for round_index in range(ROUNDS):
            lane = root / f"policy-{round_index}"
            lane.mkdir()
            result = _policy_build(stage, lane, best_selection)
            policy_samples.append(float(result["verified_create_s"]))
            policy_sizes.add(int(result["archive_bytes"]))
            policy_locality = result["locality"]
        if len(policy_sizes) != 1:
            raise RuntimeError("selective-effort archive size is nondeterministic")
        policy_bytes = next(iter(policy_sizes))
        policy_median_s = statistics.median(policy_samples)
        strict = {
            "beats_accepted_v029_size": policy_bytes < int(accepted_v029_bytes),
            "beats_zip_size": policy_bytes < int(comparators["zip"]["archive_bytes"]),
            "beats_zstd19_size": policy_bytes < int(comparators["zstd19"]["archive_bytes"]),
            "verified_create_beats_zip": policy_median_s < float(comparators["zip"]["median_create_s"]),
            "verified_create_beats_zstd19": policy_median_s < float(comparators["zstd19"]["median_create_s"]),
            "within_release_locality_bounds": bool(policy_locality and policy_locality["within_release_bounds"]),
        }
        strict["passed"] = all(strict.values())

        return {
            "label": f"{suite}/{name}",
            "accepted_v029_bytes": int(accepted_v029_bytes),
            "baseline_level1": {
                "archive_bytes": baseline_bytes,
                "verified_create_s": float(profile["verified_create_s"]),
                "required_saving_to_beat_v029": required_saving,
                "physical_pack_count": len(profile["packs"]),
            },
            "compression_effort_upper_bound": {
                "maximum_possible_saving_bytes": max_saving,
                "all_best_archive_floor_bytes": all_best_floor,
                "can_strictly_beat_v029": effort_can_cross_floor,
            },
            "minimum_modeled_effort_to_v029": minimum_floor_state,
            "comparators": comparators,
            "conservative_zip_budget": {
                "target_total_s": zip_budget_s,
                "available_extra_s": extra_budget_s,
                "modeled_extra_ms": best_ms,
                "modeled_saving_bytes": best_saved,
                "selected_pack_count": len(best_selection),
                "selection": best_selection,
            },
            "measured_zip_budget_policy": {
                "archive_bytes": policy_bytes,
                "median_verified_create_s": policy_median_s,
                "raw_verified_create_s": policy_samples,
                "locality": policy_locality,
                "strict": strict,
            },
            "pack_frontier": profile["packs"],
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg01_selective_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg01_selective_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    rows = []
    for name in TARGETS:
        key = ("neutral_hostile_v1", name)
        source = corpus / name
        expected_tree = accepted[key]["tree_sha256"]
        if EXT._tree(source) != expected_tree:
            raise RuntimeError(f"frozen source drift for {key!r}")
        row = _one("neutral_hostile_v1", name, source, work_root, int(accepted[key]["archive_bytes"]))
        rows.append(row)
        print(json.dumps({
            "label": row["label"],
            "upper_bound": row["compression_effort_upper_bound"],
            "minimum_modeled_effort_to_v029": row["minimum_modeled_effort_to_v029"],
            "measured_strict": row["measured_zip_budget_policy"]["strict"],
        }, separators=(",", ":")), flush=True)

    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_frozen_sources_verified": len(rows) == len(TARGETS),
        "all_profiled_candidates_locality_safe": all(
            row["measured_zip_budget_policy"]["locality"]["within_release_bounds"] for row in rows
        ),
        "all_policy_rounds_complete": all(
            len(row["measured_zip_budget_policy"]["raw_verified_create_s"]) == ROUNDS for row in rows
        ),
        "all_comparator_rounds_complete": all(
            len(row["comparators"][name]["raw_create_s"]) == ROUNDS
            for row in rows for name in ("zip", "zstd19")
        ),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-federated-selective-effort-v1",
        "targets": list(TARGETS),
        "levels": list(LEVELS),
        "rounds": ROUNDS,
        "profile_repeats": PROFILE_REPEATS,
        "time_bucket_ms": TIME_BUCKET_MS,
        "rows": rows,
        "measurement_gate": gate,
        "summary": {
            "effort_only_can_cross_v029": [
                row["label"] for row in rows
                if row["compression_effort_upper_bound"]["can_strictly_beat_v029"]
            ],
            "measured_full_contract_wins": [
                row["label"] for row in rows if row["measured_zip_budget_policy"]["strict"]["passed"]
            ],
        },
        "claim_boundary": (
            "research-only per-pack effort model for C25EG01.  It cannot alter the candidate default, selector, "
            "native/Android support, v0.29 floor or release authority.  If the byte upper bound misses v0.29, "
            "structural representation changes are required; thresholds must not be weakened."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("federated selective-effort measurement invalid")


if __name__ == "__main__":
    main()
