from __future__ import annotations

"""Lower-effort generic C25EG08 office policy frontier.

The identity-free policy family previously jumped directly from Zstd level 1 to
12/15/19/22.  Exact full-frontier evidence then found a byte-safe generic policy but
spent ~0.8 s in high-effort compression alone.  This oracle tests the unexplored CPU/
size Pareto region without adding content identity or a larger semantic policy.

Only nested raw-pack-size rules are allowed.  Candidate effort levels are
1/3/6/9/12/15/19/22.  Research-time profiling measures each final raw pack at those
levels and searches every one- and two-threshold rule for the smallest modeled
4-worker makespan that is *exactly* below the immutable office/v0.29/ZIP/Zstd byte
ceiling.  Profiling is not part of candidate creation: it exists only to distill one
fixed generic rule.  The selected rule is then rebuilt repeatedly through the actual
bounded-parallel C25EG08 encoder, mandatory strong verification and locality audit.

A result earns promotion consideration only if the measured candidate remains strictly
smaller and faster to create than both ZIP and Zstd-19, is strictly smaller than
accepted v0.29, and is byte/SHA-identical to a serial implementation of the same
content-agnostic rule.  This cannot authorize selector/native/Android/release promotion.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as DV4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5
from experiments import entropygraph_v025 as V25

LEVELS = (1, 3, 6, 9, 12, 15, 19, 22)
SIZE_THRESHOLDS = (64 << 10, 128 << 10, 256 << 10, 384 << 10, 512 << 10, 1 << 20)
PROFILE_ROUNDS = 2
WORKERS = 4
ROUNDS = V1.ROUNDS


def _payload_and_cpu(raw: bytes, level: int) -> tuple[int, float]:
    samples: list[float] = []
    payload_len: int | None = None
    for _ in range(PROFILE_ROUNDS):
        started = time.perf_counter()
        compressed = V25.zc(raw, int(level))
        elapsed = time.perf_counter() - started
        effective = len(compressed) if len(compressed) + 8 < len(raw) else len(raw)
        if payload_len is None:
            payload_len = effective
        elif effective != payload_len:
            raise RuntimeError("Zstd payload size nondeterminism during effort profiling")
        samples.append(elapsed)
    assert payload_len is not None
    return int(payload_len), float(statistics.median(samples))


def _profile(raws: list[bytes]) -> tuple[list[dict[int, int]], list[dict[int, float]]]:
    sizes: list[dict[int, int]] = []
    cpu: list[dict[int, float]] = []
    for raw in raws:
        size_row: dict[int, int] = {}
        cpu_row: dict[int, float] = {}
        for level in LEVELS:
            payload, elapsed = _payload_and_cpu(raw, int(level))
            size_row[int(level)] = payload
            cpu_row[int(level)] = elapsed
        sizes.append(size_row); cpu.append(cpu_row)
    return sizes, cpu


def _vector(raws: list[bytes], rules: list[dict]) -> tuple[int, ...]:
    result: list[int] = []
    for raw in raws:
        level = 1
        for rule in rules:
            if len(raw) >= int(rule["threshold"]):
                level = max(level, int(rule["level"]))
        result.append(level)
    return tuple(result)


def _modeled_parallel_makespan(cpu: list[dict[int, float]], vector: tuple[int, ...]) -> tuple[float, float]:
    jobs = [float(cpu[index][int(level)]) for index, level in enumerate(vector)]
    loads = [0.0] * WORKERS
    for job in sorted(jobs, reverse=True):
        slot = min(range(WORKERS), key=loads.__getitem__)
        loads[slot] += job
    return float(max(loads, default=0.0)), float(sum(jobs))


def _rule_space() -> list[list[dict]]:
    policies: list[list[dict]] = []
    for threshold in SIZE_THRESHOLDS:
        for level in LEVELS[1:]:
            policies.append([{"feature": "raw_bytes", "operator": ">=", "threshold": threshold, "level": level}])
    for lower_index, lower in enumerate(SIZE_THRESHOLDS):
        for upper in SIZE_THRESHOLDS[lower_index + 1:]:
            for low_level in LEVELS[1:-1]:
                for high_level in LEVELS[1:]:
                    if high_level <= low_level:
                        continue
                    policies.append([
                        {"feature": "raw_bytes", "operator": ">=", "threshold": lower, "level": low_level},
                        {"feature": "raw_bytes", "operator": ">=", "threshold": upper, "level": high_level},
                    ])
    return policies


def _search(raws: list[bytes], meta_comp: bytes, sizes: list[dict[int, int]], cpu: list[dict[int, float]], ceiling: int):
    best = None
    feasible = 0
    vectors_seen: set[tuple[int, ...]] = set()
    for rules in _rule_space():
        vector = _vector(raws, rules)
        if vector in vectors_seen:
            continue
        vectors_seen.add(vector)
        archive_bytes = V3._exact_archive_bytes(meta_comp, sizes, vector)
        if archive_bytes >= ceiling:
            continue
        feasible += 1
        makespan, total_cpu = _modeled_parallel_makespan(cpu, vector)
        selected = sum(1 for level in vector if level != 1)
        cost = (makespan, total_cpu, max(vector), selected, len(rules), archive_bytes)
        item = (cost, rules, vector, archive_bytes)
        if best is None or item[0] < best[0]:
            best = item
    if best is None:
        return None, {"feasible_policies": 0, "deduplicated_vectors": len(vectors_seen)}
    cost, rules, vector, archive_bytes = best
    return (rules, vector, int(archive_bytes)), {
        "feasible_policies": feasible,
        "deduplicated_vectors": len(vectors_seen),
        "modeled_parallel_makespan_s": float(cost[0]),
        "modeled_total_compression_cpu_s": float(cost[1]),
        "maximum_level": int(cost[2]),
        "selected_high_effort_packs": int(cost[3]),
        "rule_count": int(cost[4]),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-low-effort-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")
        raw_eg07, _ = DV5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = DV4._raw_eg07_parts(raw_eg07)
        sizes, cpu = _profile(raws)
        ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )
        selected, search = _search(raws, meta_comp, sizes, cpu, ceiling)
        if selected is None:
            raise RuntimeError("expanded lower-effort rule family contains no byte-feasible office policy")
        rules, vector, projected_bytes = selected

        reference_path = root / "serial-reference.c25eg08"
        serial = V1._emit(raw_eg07, reference_path, V3._selection_dict(vector))
        reference = reference_path.read_bytes()
        if len(reference) != projected_bytes or int(serial["archive_bytes"]) != projected_bytes:
            raise RuntimeError("expanded-level projected bytes disagree with serial reference")

        samples: list[float] = []
        compression_samples: list[float] = []
        shas: set[str] = set()
        last = None
        for round_index in range(ROUNDS):
            measured = V6._candidate_once(stage, root / f"measure-{round_index}", rules, reference, vector)
            samples.append(float(measured["verified_create_s"]))
            compression_samples.append(float(measured["parallel_compression_s"]))
            shas.add(str(measured["archive_sha256"])); last = measured
        if len(shas) != 1:
            raise RuntimeError("expanded-level generic EG08 output is nondeterministic")
        assert last is not None
        median_create = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": len(reference) < int(accepted_v029),
            "beats_zip_size": len(reference) < int(comparators["zip"]["archive_bytes"]),
            "beats_zstd19_size": len(reference) < int(comparators["zstd19"]["archive_bytes"]),
            "verified_create_beats_zip": median_create < float(comparators["zip"]["median_create_s"]),
            "verified_create_beats_zstd19": median_create < float(comparators["zstd19"]["median_create_s"]),
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_identity_not_policy_input": True,
            "only_raw_size_policy_input": all(rule["feature"] == "raw_bytes" for rule in rules),
            "exact_serial_archive_identity": bool(last["exact_bytes_vs_serial_reference"]),
            "same_selected_level_vector": tuple(last["selected_levels"]) == tuple(vector),
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-low-effort-policy-v1",
        "candidate": "C25EG08",
        "accepted_v029_bytes": int(accepted_v029),
        "effort_levels": list(LEVELS),
        "policy_family": "one-or-two nested raw-size thresholds only",
        "selected_policy": {"rules": rules, "overlap_resolution": "max_level"},
        "search": search,
        "measured_candidate": {
            "archive_bytes": len(reference),
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": float(median_create),
            "raw_verified_create_s": samples,
            "median_parallel_compression_s": float(statistics.median(compression_samples)),
            "workers": int(last["workers"]),
            "selected_high_effort_packs": int(last["selected_high_effort_packs"]),
            "selected_levels": list(last["selected_levels"]),
            "max_member_read_amplification": float(last["locality"]["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(last["locality"]["max_decode_unit_bytes"]),
            "exact_bytes_vs_serial_reference": True,
        },
        "comparators": comparators,
        "strict": strict,
        "claim_boundary": (
            "Research-only generic effort frontier. Research-time compression profiling selects a fixed rule; it is "
            "not charged to candidate creation because the production-shaped candidate evaluates raw pack size only. "
            "No content identity is a policy input. Ordinary all-15/native/Android/final authority remain mandatory."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": result["selected_policy"],
        "search": result["search"],
        "measured_candidate": result["measured_candidate"],
        "strict": result["strict"],
    }, indent=2), flush=True)
    if not result["strict"]["passed"]:
        raise SystemExit("lower-effort generic C25EG08 policy did not satisfy the four-way office contract")


if __name__ == "__main__":
    main()
