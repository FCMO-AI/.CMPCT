from __future__ import annotations

"""Exact oracle for eliminating avoidable logs-source preflight work.

The shipping logs terminal needs only one source-side fact before it constructs real
r24/logs candidates: whether at least two compressed sidecars have an uncompressed
sibling.  The current prefilter materializes every regular path, sorts the complete
set, then counts pairs.  This oracle tests an equivalent streaming decision procedure
that may stop immediately after the second proven pair.

This file is research-only.  It changes no selector, archive byte, timing boundary,
or release credit.  Promotion requires exact eligibility agreement on adversarial
cases plus a meaningful same-runner speedup on a large early-positive tree.
"""

import json
import os
from pathlib import Path
import statistics
import tempfile
import time

from experiments import entropygraph_v030_release_product_logs_candidate as PROD

ROUNDS = 9
MIN_SPEEDUP = 0.25
MIN_ABSOLUTE_SAVING_S = 0.003


def streaming_eligible(root: Path) -> dict:
    """Prove the same >=2 sidecar-pair predicate without enumerating/sorting the tree.

    Only regular non-symlink files participate, matching the shipping prefilter.  Two
    small seen sets are sufficient because a pair may be encountered in either order.
    Once MIN_SIDECAR_PAIRS distinct sidecars have proven siblings, later paths cannot
    change the boolean answer and traversal terminates exactly.
    """
    root = Path(root)
    plain: set[str] = set()
    sidecars: dict[str, str] = {}
    pairs: list[tuple[str, str]] = []
    scanned_regular_files = 0

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            if not path.is_file() or path.is_symlink():
                continue
            scanned_regular_files += 1
            rel = path.relative_to(root).as_posix()

            sidecar_base = None
            for suffix in (".gz", ".zst"):
                if rel.endswith(suffix):
                    sidecar_base = rel[: -len(suffix)]
                    break

            if sidecar_base is not None:
                sidecars[rel] = sidecar_base
                if sidecar_base in plain:
                    pairs.append((rel, sidecar_base))
            else:
                plain.add(rel)
                for suffix in (".gz", ".zst"):
                    candidate = rel + suffix
                    if sidecars.get(candidate) == rel:
                        pairs.append((candidate, rel))

            if len(pairs) >= PROD.MIN_SIDECAR_PAIRS:
                return {
                    "eligible": True,
                    "proven_sidecar_pairs": len(pairs),
                    "pair_examples": pairs[:8],
                    "scanned_regular_files": scanned_regular_files,
                    "short_circuited": True,
                }

    return {
        "eligible": False,
        "proven_sidecar_pairs": len(pairs),
        "pair_examples": pairs[:8],
        "scanned_regular_files": scanned_regular_files,
        "short_circuited": False,
    }


def _write(path: Path, payload: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _case(root: Path, *, ordinary: int, pair_positions: str, one_pair: bool = False) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if pair_positions == "early":
        _write(root / "a.log", b"alpha")
        _write(root / "a.log.gz", b"gzip-sidecar")
        if not one_pair:
            _write(root / "b.log", b"beta")
            _write(root / "b.log.zst", b"zstd-sidecar")
    for i in range(ordinary):
        _write(root / "bulk" / f"f-{i:05d}.bin", bytes((i & 255,)))
    if pair_positions == "late":
        _write(root / "zz-a.log", b"alpha")
        _write(root / "zz-a.log.gz", b"gzip-sidecar")
        if not one_pair:
            _write(root / "zz-b.log", b"beta")
            _write(root / "zz-b.log.zst", b"zstd-sidecar")


def _adversarial_cases(base: Path) -> list[dict]:
    specs = [
        ("early-positive", 4000, "early", False),
        ("late-positive", 4000, "late", False),
        ("single-pair", 1500, "late", True),
        ("no-pair", 1500, "none", False),
    ]
    rows = []
    for name, ordinary, where, one_pair in specs:
        root = base / name
        _case(root, ordinary=ordinary, pair_positions=where, one_pair=one_pair)
        # Suffix-shaped files without siblings must not create false positives.
        _write(root / "traps" / "orphan.gz")
        _write(root / "traps" / "orphan.zst")
        reference = PROD.logs_source_prefilter(root)
        candidate = streaming_eligible(root)
        rows.append(
            {
                "name": name,
                "reference_eligible": bool(reference["eligible"]),
                "streaming_eligible": bool(candidate["eligible"]),
                "eligibility_equal": bool(reference["eligible"]) == bool(candidate["eligible"]),
                "reference_sidecar_pairs": int(reference["sidecar_pairs"]),
                "streaming_proven_pairs": int(candidate["proven_sidecar_pairs"]),
                "streaming_scanned_regular_files": int(candidate["scanned_regular_files"]),
                "streaming_short_circuited": bool(candidate["short_circuited"]),
            }
        )
    return rows


def _timed(fn, root: Path) -> float:
    started = time.perf_counter()
    fn(root)
    return time.perf_counter() - started


def _performance_case(base: Path) -> dict:
    root = base / "large-early-positive"
    _case(root, ordinary=12000, pair_positions="early")

    reference_samples: list[float] = []
    streaming_samples: list[float] = []
    # Rotate order to reduce cache/order bias while keeping both algorithms on the
    # exact same already-materialized filesystem tree.
    for round_index in range(ROUNDS):
        if round_index % 2:
            streaming_samples.append(_timed(streaming_eligible, root))
            reference_samples.append(_timed(PROD.logs_source_prefilter, root))
        else:
            reference_samples.append(_timed(PROD.logs_source_prefilter, root))
            streaming_samples.append(_timed(streaming_eligible, root))

    reference_median = statistics.median(reference_samples)
    streaming_median = statistics.median(streaming_samples)
    saving = reference_median - streaming_median
    speedup_fraction = saving / max(reference_median, 1e-12)
    final = streaming_eligible(root)
    return {
        "rounds": ROUNDS,
        "reference_samples_s": reference_samples,
        "streaming_samples_s": streaming_samples,
        "reference_median_s": reference_median,
        "streaming_median_s": streaming_median,
        "absolute_saving_s": saving,
        "speedup_fraction": speedup_fraction,
        "streaming_scanned_regular_files": int(final["scanned_regular_files"]),
        "streaming_short_circuited": bool(final["short_circuited"]),
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-prefilter-") as td:
        base = Path(td)
        correctness = _adversarial_cases(base / "correctness")
        performance = _performance_case(base / "performance")

    exact = all(row["eligibility_equal"] for row in correctness)
    early_row = next(row for row in correctness if row["name"] == "early-positive")
    useful_short_circuit = early_row["streaming_short_circuited"]
    promotion_signal = (
        exact
        and useful_short_circuit
        and performance["speedup_fraction"] >= MIN_SPEEDUP
        and performance["absolute_saving_s"] >= MIN_ABSOLUTE_SAVING_S
    )
    result = {
        "experiment": "v030-logs-streaming-prefilter-v1",
        "research_only": True,
        "selector_change": False,
        "release_credit": False,
        "predicate": "at least two regular .gz/.zst sidecars with regular unsuffixed siblings",
        "correctness": correctness,
        "performance": performance,
        "requirements": {
            "exact_eligibility_on_all_cases": True,
            "minimum_speedup_fraction": MIN_SPEEDUP,
            "minimum_absolute_saving_s": MIN_ABSOLUTE_SAVING_S,
        },
        "experiment_valid": exact,
        "promotion_signal": promotion_signal,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    # Scientific validity is exactness.  Performance controls promotion only; a
    # valid negative result remains durable evidence rather than permanent-red CI.
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
