from __future__ import annotations

"""Unseen/adversarial generalization for the C25CC01 terminal-admission envelope.

The frozen 15-workload proof is intentionally insufficient for selector promotion. This campaign creates new,
deterministic trees that were not used to derive the admission constants, applies exactly the frozen structural
predicate, and charges every admitted tree against complete C25CC01 build+strong-verification plus same-runner ZIP
and solid Zstd-19 comparators. A valid rejection is useful evidence; a single admitted counterexample blocks
promotion.

The positive side deliberately includes two distinct high-entropy regimes. Flat medium-file entropy trees test that
mere incompressibility is *not* enough to trigger compact control. High-file-count entropy trees test the actual
structural hypothesis behind C25CC01: when payload compression has essentially no leverage and authenticated per-file
control dominates, compact control should remove enough duplicated framing to justify admission. These families are
newly generated and do not reuse the frozen encrypted-like corpus, paths, hashes, counts, or byte layout.

As with the frozen all-15 oracle, inherited r24 layouts that violate the compact-control locality/decode contract are
recorded as profile-ineligible negative evidence. They are never forced through the byte-ratio admission predicate,
never benchmarked as admitted candidates, and never converted into harness crashes.
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


def _write_entropy_mosaic(
    root: Path,
    *,
    seed: int,
    tiny_files: int,
    tiny_size: int,
    large_bytes: int,
    chunk_files: int,
    chunk_size: int,
) -> None:
    """Create an unseen high-file-count/high-entropy family without copying the frozen corpus shape."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "bulk.bin").write_bytes(_bytes(seed, large_bytes))
    chunks = root / "chunks"
    chunks.mkdir()
    for i in range(chunk_files):
        (chunks / f"part-{i:03d}.bin").write_bytes(_bytes(seed + 10_000 + i * 4253, chunk_size))
    crumbs = root / "crumbs"
    crumbs.mkdir()
    for i in range(tiny_files):
        # Variable tiny sizes prevent the test from depending on a single repeated recipe length.
        n = tiny_size + ((i * 37) % max(1, tiny_size // 3))
        (crumbs / f"piece-{i:05d}.bin").write_bytes(_bytes(seed + 1_000_000 + i * 7919, n))


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
        # Flat high-entropy controls. These are intentionally expected to remain rejected if compact-control
        # savings are too small; incompressibility alone must not authorize the profile.
        "entropy_40x256k": ("entropy", 1101, 40, 256 * 1024),
        "entropy_96x128k": ("entropy", 2202, 96, 128 * 1024),
        "entropy_256x48k": ("entropy", 3303, 256, 48 * 1024),
        # Threshold-neighbor entropy family.
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

    # Independent positive-shape probes. They intentionally differ from the frozen target's file count, large-blob
    # size, chunk count, tiny-member size, names, and random seeds. Their only shared property is the generic one the
    # selector claims to recognize: lots of authenticated control around payloads with essentially no compressible
    # structure.
    mosaics = {
        "entropy_mosaic_640": dict(seed=8808, tiny_files=640, tiny_size=3072, large_bytes=7 * 1024 * 1024, chunk_files=17, chunk_size=48 * 1024),
        "entropy_mosaic_1150": dict(seed=9909, tiny_files=1150, tiny_size=2048, large_bytes=6 * 1024 * 1024, chunk_files=11, chunk_size=80 * 1024),
        "entropy_mosaic_1750": dict(seed=10110, tiny_files=1750, tiny_size=1536, large_bytes=5 * 1024 * 1024, chunk_files=29, chunk_size=40 * 1024),
    }
    for name, kwargs in mosaics.items():
        dst = root / name
        _write_entropy_mosaic(dst, **kwargs)
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
            eligible = bool(candidate["profile_eligible"])
            admitted = eligible and ADM._admitted(shape, int(candidate["r24_bytes"]), int(candidate["candidate_bytes"]))
            row = {
                "case": name,
                **shape,
                "profile_eligible": eligible,
                "profile_reject_reason": candidate["profile_reject_reason"],
                "r24_bytes": candidate["r24_bytes"],
                "candidate_bytes": candidate["candidate_bytes"],
                "r24_to_logical": candidate["r24_bytes"] / max(1, shape["logical_bytes"]),
                "candidate_to_r24": (
                    candidate["candidate_bytes"] / max(1, candidate["r24_bytes"]) if eligible else None
                ),
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
    ineligible = [row for row in rows if not row["profile_eligible"]]
    counterexamples = [row["case"] for row in admitted if not row.get("strict_four_way_win", False)]
    expected_cases = 10
    result = {
        "schema": "cmpct-v030-r24-compact-control-terminal-generalization-v3",
        "contract": {
            "predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "min_logical_bytes": ADM.MIN_LOGICAL_BYTES,
            "min_regular_files": ADM.MIN_REGULAR_FILES,
            "min_r24_to_logical": ADM.MIN_R24_TO_LOGICAL,
            "max_candidate_to_r24": ADM.MAX_CC_TO_R24,
            "comparator_rounds": ADM.ROUNDS,
            "profile_ineligibility_is_negative_evidence": True,
            "selector_change": False,
            "release_credit": False,
        },
        "rows": rows,
        "profile_ineligible_cases": [row["case"] for row in ineligible],
        "admitted_count": len(admitted),
        "rejected_count": len(rejected),
        "counterexamples": counterexamples,
        "gate": {
            "all_cases_complete": len(rows) == expected_cases,
            "at_least_one_unseen_admission": bool(admitted),
            "at_least_one_unseen_rejection": bool(rejected),
            "zero_admitted_counterexamples": not counterexamples,
            "all_admitted_payloads_unchanged": all(row["payload_unchanged"] for row in admitted),
            "all_admitted_two_control_copies": all(row["two_control_copies"] for row in admitted),
            "passed": len(rows) == expected_cases and bool(admitted) and bool(rejected) and not counterexamples and all(
                row["payload_unchanged"] and row["two_control_copies"] for row in admitted
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
