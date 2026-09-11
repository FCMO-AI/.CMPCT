from __future__ import annotations

"""ONE-G0.3 generic statistical-Law opportunity diagnostic.

This benchmark is intentionally not a compressor and has no product/Genesis scoring authority.
It regenerates and seals the exact 15 Genesis workloads, then measures empirical H0/H1 byte
prediction opportunity in one streaming observation pass. Dense model-description charges are
included exactly as frozen in the preregistration.
"""

from array import array
import argparse
import json
import math
from pathlib import Path
import resource
import stat
import time
from typing import Any

import numpy as np

from benchmarks.one.one_genesis_gate_measurement_executor import _seal_physical_inputs

H0_MODEL_BYTES = 256 * 4
H1_MODEL_BYTES = (256 * 256 + 256) * 4
BLOCK_BYTES = 4 * 1024 * 1024

CAUSAL_GAP_NAMES = {
    "04_analytics_and_database",
    "05_logs_and_telemetry",
    "10_large_mixed_binary",
}
INCOMPRESSIBLE_KEYS = {
    ("neutral_hostile_v1", "07_incompressible_and_encrypted_like"),
    ("resemblance_hostile_v1", "05_incompressible"),
}


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if __import__("sys").platform == "darwin" else value * 1024)


def _suite_root(work_root: Path, suite: str) -> Path:
    if suite == "neutral_hostile_v1":
        return work_root / "neutral"
    if suite == "resemblance_hostile_v1":
        return work_root / "resemblance"
    raise RuntimeError(f"unknown Genesis suite: {suite}")


def _regular_files(root: Path) -> list[Path]:
    rows: list[Path] = []
    for path in root.rglob("*"):
        if stat.S_ISREG(path.lstat().st_mode):
            rows.append(path)
    return sorted(rows, key=lambda p: p.relative_to(root).as_posix())


def _entropy_bits(counts: np.ndarray) -> float:
    nonzero = counts[counts > 0].astype(np.float64, copy=False)
    total = float(nonzero.sum())
    if total <= 0:
        return 0.0
    return float((-nonzero * np.log2(nonzero / total)).sum())


def _conditional_entropy_bits(transitions: np.ndarray) -> float:
    matrix = transitions.reshape(256, 256).astype(np.float64, copy=False)
    row_totals = matrix.sum(axis=1)
    total_bits = 0.0
    for row_id in np.nonzero(row_totals)[0]:
        row = matrix[row_id]
        nz = row[row > 0]
        total = row_totals[row_id]
        total_bits += float((-nz * np.log2(nz / total)).sum())
    return total_bits


def observe_workload(root: Path) -> dict[str, Any]:
    h0 = np.zeros(256, dtype=np.uint64)
    transitions = np.zeros(256 * 256, dtype=np.uint64)
    starts = np.zeros(256, dtype=np.uint64)
    measured_bytes = 0
    regular_files = 0
    cpu0 = time.process_time()
    wall0 = time.perf_counter()

    for path in _regular_files(root):
        regular_files += 1
        previous: int | None = None
        first = True
        with path.open("rb") as handle:
            while True:
                block = handle.read(BLOCK_BYTES)
                if not block:
                    break
                values = np.frombuffer(block, dtype=np.uint8)
                measured_bytes += int(values.size)
                h0 += np.bincount(values, minlength=256).astype(np.uint64, copy=False)
                if first:
                    starts[int(values[0])] += 1
                    first = False
                if previous is not None:
                    transitions[(previous << 8) | int(values[0])] += 1
                if values.size > 1:
                    left = values[:-1].astype(np.uint16)
                    right = values[1:].astype(np.uint16)
                    pair_ids = (left << 8) | right
                    transitions += np.bincount(pair_ids, minlength=256 * 256).astype(np.uint64, copy=False)
                previous = int(values[-1])

    h0_bits = _entropy_bits(h0)
    h1_bits = _conditional_entropy_bits(transitions) + _entropy_bits(starts)
    h0_ideal_bytes = int(math.ceil(h0_bits / 8.0))
    h1_ideal_bytes = int(math.ceil(h1_bits / 8.0))
    h0_modeled = h0_ideal_bytes + H0_MODEL_BYTES
    h1_modeled = h1_ideal_bytes + H1_MODEL_BYTES

    return {
        "regular_files": regular_files,
        "measured_bytes": measured_bytes,
        "observation_passes": 1,
        "observation_cpu_s": time.process_time() - cpu0,
        "observation_wall_s": time.perf_counter() - wall0,
        "peak_rss_bytes": _peak_rss_bytes(),
        "h0": {
            "entropy_bits": h0_bits,
            "ideal_surprise_bytes": h0_ideal_bytes,
            "model_charge_bytes": H0_MODEL_BYTES,
            "modeled_payload_bytes": h0_modeled,
            "modeled_ratio": h0_modeled / max(1, measured_bytes),
            "modeled_saving_bytes": measured_bytes - h0_modeled,
        },
        "h1": {
            "entropy_bits": h1_bits,
            "ideal_surprise_bytes": h1_ideal_bytes,
            "model_charge_bytes": H1_MODEL_BYTES,
            "modeled_payload_bytes": h1_modeled,
            "modeled_ratio": h1_modeled / max(1, measured_bytes),
            "modeled_saving_bytes": measured_bytes - h1_modeled,
        },
        "bounded_state_bytes": int(h0.nbytes + transitions.nbytes + starts.nbytes),
    }


def run(work_root: Path) -> dict[str, Any]:
    seal = _seal_physical_inputs(work_root)
    rows: list[dict[str, Any]] = []
    for identity in seal["rows"]:
        suite = str(identity["suite"])
        name = str(identity["name"])
        root = _suite_root(work_root, suite) / name
        measurement = observe_workload(root)
        if measurement["measured_bytes"] != int(identity["logical_bytes"]):
            raise RuntimeError(
                f"{suite}/{name}: statistical observer measured {measurement['measured_bytes']} bytes "
                f"but frozen identity has {identity['logical_bytes']}"
            )
        rows.append({**identity, "measurement": measurement})

    causal = [row for row in rows if row["name"] in CAUSAL_GAP_NAMES and row["suite"] == "neutral_hostile_v1"]
    causal_green = [
        row for row in causal
        if row["measurement"]["h1"]["modeled_ratio"] <= 0.85
    ]
    absolute_green = any(
        row["measurement"]["h1"]["modeled_saving_bytes"] >= 5 * 1024 * 1024
        for row in causal_green
    )
    controls = [row for row in rows if (row["suite"], row["name"]) in INCOMPRESSIBLE_KEYS]
    controls_green = all(
        row["measurement"]["h1"]["modeled_ratio"] >= 0.98
        for row in controls
    )
    decision = (
        "ADVANCE_STATISTICAL_LAW_RESEARCH"
        if len(causal_green) >= 2 and absolute_green and controls_green
        else "HOLD_STATISTICAL_LAW_RESEARCH"
    )
    return {
        "schema": "cmpct-one-g03-statistical-law-opportunity-v1",
        "claim_boundary": "information-opportunity diagnostic only; no product bytes, Genesis scoring, or promotion authority",
        "physical_input_seal": seal,
        "model": {
            "h0_dense_model_charge_bytes": H0_MODEL_BYTES,
            "h1_dense_model_charge_bytes": H1_MODEL_BYTES,
            "context": "previous-byte with file-boundary reset",
            "count_width_bytes": 4,
            "reader_visible_codec_added": False,
        },
        "rows": rows,
        "gate": {
            "causal_gap_rows_at_least_15pct": len(causal_green),
            "requires_causal_gap_rows": 2,
            "at_least_one_5mib_opportunity": absolute_green,
            "incompressible_controls_green": controls_green,
            "decision": decision,
        },
        "genesis_scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": payload["schema"], "decision": payload["gate"]["decision"]}, sort_keys=True))


if __name__ == "__main__":
    main()
