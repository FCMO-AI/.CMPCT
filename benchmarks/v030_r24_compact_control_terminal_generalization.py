from __future__ import annotations

"""Unseen/adversarial generalization for the C25CC01 terminal-admission envelope.

The frozen 15-workload proof is intentionally insufficient for selector promotion.  This campaign creates new,
deterministic trees that were not used to derive the admission constants, applies exactly the frozen structural
predicate, and charges every admitted tree against complete C25CC01 build+strong-verification plus same-runner ZIP
and solid Zstd-19 comparators.  A valid rejection is useful evidence; a single admitted counterexample blocks
promotion.
"""

import argparse
import json
from pathlib import Path
import random
import shutil
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_terminal_admission as ADM


def _bytes(seed: int, n: int) -> bytes:
    return random.Random(seed).randbytes(n)


def _write_entropy_tree(root: Path, *, seed: int, files: int, size: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(files):
        (root / f"member-{i:04d}.bin").write_bytes(_bytes(seed + i * 7919, size))


def _write_repeated_tree(root: Path, *, seed: int, files: int, size: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    block = _bytes(seed, size)
    for i in range(files):
        (root / f"member-{i:04d}.bin").write_bytes(block)


def _write_partly_redundant_tree(root: Path, *, seed: int, files: int, size: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    common = _bytes(seed, size // 2)
    for i in range(files):
        unique = _bytes(seed + 100_000 + i * 3571, size - len(common))
        (root / f"member-{i:04d}.bin").write_bytes(common + unique)


def _cases(root: Path) -> dict[str, Path]:
    cases: dict[str, Path] = {}
    specs = {
        # Strong positive candidates: multiple high-entropy shapes and file-count regimes.
        "entropy_40x256k": ("entropy", 1101, 40, 256 * 1024),
        "entropy_96x128k": ("entropy", 2202, 96, 128 * 1024),
        "entropy_256x48k": ("entropy", 3303, 256, 48 * 1024),
        # Threshold-neighbor entropy family: should exercise the minimum-size/file-count boundary.
        "entropy_32x40k": ("entropy", 4404, 32, 40 * 1024),
        # Deliberate rejection families: strong cross-file redundancy should make r24 materially compressible.
        "repeated_40x256k": ("repeated", 5505, 40, 256 * 1024),
        "half_redundant_64x192k": ("partial", 6606, 64, 192 * 1024),
        # File-count neighbor: cannot be admitted even if payloads are high entropy.
        "entropy_31x256k": ("entropy", 7707, 31, 256 * 1024),
    }
    for name, (kind, seed, files, size) in specs.items():
        dst = root / name
        if kind == "entropy":
            _write_entropy_tree(dst, seed=seed, files=files, size=size)
        elif kind == "repeated":
            _write_repeated_tree(dst, seed=seed, files=files, size=size)
        else:
            _write_partly_redundant_tree(dst, seed=seed, files=files, size=size)
        cases[name] = dst
    return cases


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    rows = []
    cases = _cases(args.work_root / "sources")
    for name, source in cases.items():
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-generalize-", dir=args.work_root) as td:
            root = Path(td)
            stage = EXT._normalized_stage(source, root / "stage")
            shape = ADM._source_shape(stage)
            candidate = ADM._build_candidate(stage, root / "preflight")
            admitted = ADM._admitted(shape, candidate["r24_bytes"], candidate["candidate_bytes"])
            row = {
                "case": name,
                **shape,
                "r24_bytes": candidate["r24_bytes"],
                "candidate_bytes": candidate["candidate_bytes"],
                "r24_to_logical": candidate["r24_bytes"] / max(1, shape["logical_bytes"]),
                "candidate_to_r24": candidate["candidate_bytes"] / max(1, candidate["r24_bytes"]),
                "admitted": admitted,
                "payload_unchanged": candidate["payload_unchanged"],
                "two_control_copies": candidate["two_control_copies"],
            }
            if admitted:
                competitors = ADM._competitors(stage, root / "competitors")
                row["competitors"] = competitors
                row["strict_four_way_win"] = bool(competitors["strict_four_way_win"])
            rows.append(row)

    admitted = [row for row in rows if row["admitted"]]
    rejected = [row for row in rows if not row["admitted"]]
    counterexamples = [row["case"] for row in admitted if not row.get("strict_four_way_win", False)]
    result = {
        "schema": "cmpct-v030-r24-compact-control-terminal-generalization-v1",
        "contract": {
            "predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "min_logical_bytes": ADM.MIN_LOGICAL_BYTES,
            "min_regular_files": ADM.MIN_REGULAR_FILES,
            "min_r24_to_logical": ADM.MIN_R24_TO_LOGICAL,
            "max_candidate_to_r24": ADM.MAX_CC_TO_R24,
            "comparator_rounds": ADM.ROUNDS,
            "selector_change": False,
            "release_credit": False,
        },
        "rows": rows,
        "admitted_count": len(admitted),
        "rejected_count": len(rejected),
        "counterexamples": counterexamples,
        "gate": {
            "all_cases_complete": len(rows) == 7,
            "at_least_one_unseen_admission": bool(admitted),
            "at_least_one_unseen_rejection": bool(rejected),
            "zero_admitted_counterexamples": not counterexamples,
            "all_admitted_payloads_unchanged": all(row["payload_unchanged"] for row in admitted),
            "all_admitted_two_control_copies": all(row["two_control_copies"] for row in admitted),
            "passed": len(rows) == 7 and bool(admitted) and bool(rejected) and not counterexamples and all(
                row["payload_unchanged"] and row["two_control_copies"] for row in admitted
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
