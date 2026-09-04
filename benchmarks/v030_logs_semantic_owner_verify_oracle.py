from __future__ import annotations

"""Measure duplicate release-wrapper work around the canonical logs semantic verifier.

The canonical logs profile already owns filesystem/content identity and the canonical user-tree digest. The public
release wrapper currently calls that verifier and then reopens/decodes/hashes the filesystem manifest a second time.
This oracle measures only that duplicate receipt-building tax. It changes no archive byte and earns no release
credit; a positive result merely authorizes a later wrapper refactor that must re-earn the ordinary logs/external
release gates.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_logs_terminal_admission_oracle as TERMINAL
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 21
MIN_RELATIVE_SPEEDUP = 0.10
MIN_ABSOLUTE_SPEEDUP_S = 0.001


def _timed(fn, archive: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    result = dict(fn(archive))
    return time.perf_counter() - started, result


def _same_integrity(a: dict, b: dict) -> bool:
    keys = (
        "ok",
        "tree_sha256",
        "user_tree_sha256",
        "canonical_filesystem_manifest",
        "filesystem_manifest_entries",
        "filesystem_regular_members",
    )
    return all(a.get(key) == b.get(key) for key in keys)


def _corruption_rejected(path: Path) -> bool:
    try:
        receipt = LOGS.strong_verify(path)
    except Exception:
        return True
    return not bool(receipt.get("ok"))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    neutral = TERMINAL.GENERAL.V029._load(
        TERMINAL.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_logs_semantic_owner_neutral",
    )
    repair = TERMINAL.GENERAL.V029._load(
        TERMINAL.GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_logs_semantic_owner_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "05_logs_and_telemetry"
    stage = TERMINAL.EXT._normalized_stage(source, work_root / "stage-root")

    archive = work_root / "logs.cmpct"
    LOGS.build(stage, archive)
    canonical = dict(LOGS.strong_verify(archive))
    wrapped = dict(PRODUCT.strong_verify(archive))
    if not canonical.get("ok") or not wrapped.get("ok") or not _same_integrity(canonical, wrapped):
        raise RuntimeError("canonical and release-wrapper logs verification disagree before timing")

    current_samples: list[float] = []
    owner_samples: list[float] = []
    for round_index in range(ROUNDS):
        order = ("current", "owner") if round_index % 2 == 0 else ("owner", "current")
        round_results = {}
        for name in order:
            fn = PRODUCT.strong_verify if name == "current" else LOGS.strong_verify
            elapsed, receipt = _timed(fn, archive)
            if not receipt.get("ok") or receipt.get("tree_sha256") != canonical.get("tree_sha256"):
                raise RuntimeError(f"{name} verification identity drift")
            round_results[name] = elapsed
        current_samples.append(round_results["current"])
        owner_samples.append(round_results["owner"])

    current_median = statistics.median(current_samples)
    owner_median = statistics.median(owner_samples)
    saving = current_median - owner_median
    relative = saving / current_median if current_median else 0.0

    corrupt = work_root / "corrupt.cmpct"
    raw = bytearray(archive.read_bytes())
    if len(raw) < 256:
        raise RuntimeError("logs archive unexpectedly tiny")
    raw[len(raw) // 2] ^= 0x5A
    corrupt.write_bytes(raw)
    corruption_rejected = _corruption_rejected(corrupt)

    promotion_signal = (
        saving >= MIN_ABSOLUTE_SPEEDUP_S
        and relative >= MIN_RELATIVE_SPEEDUP
        and corruption_rejected
        and _same_integrity(canonical, wrapped)
    )
    return {
        "schema": "cmpct-v030-logs-semantic-owner-verify-oracle-v1",
        "contract": {
            "rounds": ROUNDS,
            "minimum_relative_speedup": MIN_RELATIVE_SPEEDUP,
            "minimum_absolute_speedup_s": MIN_ABSOLUTE_SPEEDUP_S,
            "archive_bytes_changed": False,
            "selector_change": False,
            "release_credit": False,
            "ordinary_logs_and_external_authority_remains_decisive": True,
        },
        "archive_bytes": archive.stat().st_size,
        "current_samples_s": current_samples,
        "semantic_owner_samples_s": owner_samples,
        "current_median_s": current_median,
        "semantic_owner_median_s": owner_median,
        "absolute_saving_s": saving,
        "relative_speedup": relative,
        "same_integrity_receipt": _same_integrity(canonical, wrapped),
        "tree_sha256": canonical.get("tree_sha256"),
        "corruption_rejected": corruption_rejected,
        "experiment_valid": True,
        "promotion_signal": promotion_signal,
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
