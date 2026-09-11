from __future__ import annotations

"""ONE-G0.3 block-adaptive Statistical-Law opportunity diagnostic.

This is not a compressor and has no Genesis scoring authority.  It measures the exact
prequential codelength of a reader-mirrorable previous-byte KT predictor reset at fixed
64 KiB blocks, plus a preregistered 8-byte framing charge per non-empty block.
"""

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

BLOCK_BYTES = 64 * 1024
ALPHABET = 256
ALPHA = 0.5
FRAME_BYTES_PER_BLOCK = 8
MODEL_STATE_BYTES = (ALPHABET * ALPHABET + ALPHABET) * 4

TARGETS = {
    "04_analytics_and_database",
    "05_logs_and_telemetry",
    "10_large_mixed_binary",
}
INCOMPRESSIBLE_KEYS = {
    ("neutral_hostile_v1", "07_incompressible_and_encrypted_like"),
    ("resemblance_hostile_v1", "05_incompressible"),
}

# Exact KT/Dirichlet-multinomial terms for counts that can occur in one frozen block.
_COUNT_TERM = np.asarray(
    [math.lgamma(n + ALPHA) - math.lgamma(ALPHA) for n in range(BLOCK_BYTES + 1)],
    dtype=np.float64,
)
_ROW_TERM = np.asarray(
    [
        math.lgamma(ALPHABET * ALPHA) - math.lgamma(n + ALPHABET * ALPHA)
        for n in range(BLOCK_BYTES + 1)
    ],
    dtype=np.float64,
)
_INV_LN2 = 1.0 / math.log(2.0)


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


def kt_block_bits(block: bytes) -> float:
    """Exact ideal prequential bits for one fixed-reset KT H1 block.

    The first symbol has no previous-byte context and is charged at 8 bits.  The
    remaining probability product equals a 256-way Dirichlet-multinomial marginal for
    each previous-byte context, so final transition counts are sufficient to compute the
    same codelength a sequential reader-mirrorable KT update assigns.
    """
    if not block:
        return 0.0
    if len(block) == 1:
        return 8.0
    values = np.frombuffer(block, dtype=np.uint8)
    left = values[:-1].astype(np.uint16)
    right = values[1:].astype(np.uint16)
    pair_ids = (left << 8) | right
    counts = np.bincount(pair_ids, minlength=ALPHABET * ALPHABET).reshape(ALPHABET, ALPHABET)
    row_totals = counts.sum(axis=1)
    nonzero_counts = counts[counts > 0]
    active_rows = row_totals[row_totals > 0]
    log_probability = float(_COUNT_TERM[nonzero_counts].sum() + _ROW_TERM[active_rows].sum())
    return 8.0 - log_probability * _INV_LN2


def observe_workload(root: Path) -> dict[str, Any]:
    measured_bytes = 0
    regular_files = 0
    blocks = 0
    ideal_bits = 0.0
    cpu0 = time.process_time()
    wall0 = time.perf_counter()

    for path in _regular_files(root):
        regular_files += 1
        with path.open("rb") as handle:
            while True:
                block = handle.read(BLOCK_BYTES)
                if not block:
                    break
                blocks += 1
                measured_bytes += len(block)
                ideal_bits += kt_block_bits(block)

    ideal_bytes = int(math.ceil(ideal_bits / 8.0))
    framing_bytes = blocks * FRAME_BYTES_PER_BLOCK
    modeled_bytes = ideal_bytes + framing_bytes
    return {
        "regular_files": regular_files,
        "measured_bytes": measured_bytes,
        "observation_passes": 1,
        "block_bytes": BLOCK_BYTES,
        "nonempty_blocks": blocks,
        "kt_alpha": ALPHA,
        "ideal_prequential_bits": ideal_bits,
        "ideal_prequential_bytes": ideal_bytes,
        "framing_charge_bytes": framing_bytes,
        "modeled_payload_bytes": modeled_bytes,
        "modeled_ratio": modeled_bytes / max(1, measured_bytes),
        "modeled_saving_bytes": measured_bytes - modeled_bytes,
        "bounded_model_state_bytes": MODEL_STATE_BYTES,
        "stored_learned_model_bytes": 0,
        "observation_cpu_s": time.process_time() - cpu0,
        "observation_wall_s": time.perf_counter() - wall0,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def run(work_root: Path) -> dict[str, Any]:
    seal = _seal_physical_inputs(work_root)
    rows: list[dict[str, Any]] = []
    for identity in seal["rows"]:
        suite = str(identity["suite"])
        name = str(identity["name"])
        measurement = observe_workload(_suite_root(work_root, suite) / name)
        if measurement["measured_bytes"] != int(identity["logical_bytes"]):
            raise RuntimeError(
                f"{suite}/{name}: adaptive observer measured {measurement['measured_bytes']} bytes "
                f"but frozen identity has {identity['logical_bytes']}"
            )
        rows.append({**identity, "measurement": measurement})

    targets = [
        row for row in rows
        if row["suite"] == "neutral_hostile_v1" and row["name"] in TARGETS
    ]
    target_green = [row for row in targets if row["measurement"]["modeled_ratio"] <= 0.75]
    absolute_green = any(
        row["measurement"]["modeled_saving_bytes"] >= 5 * 1024 * 1024
        for row in target_green
    )
    controls = [row for row in rows if (row["suite"], row["name"]) in INCOMPRESSIBLE_KEYS]
    controls_green = all(row["measurement"]["modeled_ratio"] >= 0.98 for row in controls)
    one_pass = all(row["measurement"]["observation_passes"] == 1 for row in rows)
    no_stored_model = all(row["measurement"]["stored_learned_model_bytes"] == 0 for row in rows)
    decision = (
        "ADVANCE_BLOCK_ADAPTIVE_STATISTICAL_LAW"
        if len(target_green) >= 2 and absolute_green and controls_green and one_pass and no_stored_model
        else "HOLD_BLOCK_ADAPTIVE_STATISTICAL_LAW"
    )
    return {
        "schema": "cmpct-one-g03-block-adaptive-statistical-law-v1",
        "claim_boundary": "online statistical information-opportunity diagnostic only; no product bytes or Genesis authority",
        "physical_input_seal": seal,
        "model": {
            "context": "previous-byte",
            "prior": "symmetric KT alpha=0.5",
            "block_bytes": BLOCK_BYTES,
            "file_boundary_reset": True,
            "block_boundary_reset": True,
            "frame_charge_bytes_per_nonempty_block": FRAME_BYTES_PER_BLOCK,
            "stored_learned_model_bytes": 0,
            "bounded_model_state_bytes": MODEL_STATE_BYTES,
            "reader_visible_codec_added": False,
        },
        "rows": rows,
        "gate": {
            "target_rows_at_or_below_075": len(target_green),
            "requires_target_rows": 2,
            "at_least_one_5mib_opportunity": absolute_green,
            "incompressible_controls_green": controls_green,
            "one_source_pass": one_pass,
            "no_stored_learned_model": no_stored_model,
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
