from __future__ import annotations

"""Recovery-size budget for the exact speed-oriented ZIP-factor V3 candidate.

The complete native frontier uses ZIP-factor binary-control V3 at level 3 / group size 7 because that is the
candidate close enough to normal ZIP creation speed to matter. Recovery cannot be evaluated on a roomier, slower
compression level and then assumed to fit this candidate: V3 has only a small byte margin over solid Zstd-19.

This oracle therefore wraps *the exact level-3 candidate* in the existing two-control-copy recovery envelope and
proves that recovery still fits strictly below both ZIP and Zstd-19 while retaining one payload-body copy,
primary->tail and tail->primary recovery, fail-closed double-control corruption, exact logical identity, <=8x
locality, and <=8 MiB decode units. It is research evidence only and grants no dispatch or release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_recovery_oracle as REC
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3

LEVEL = 3
GROUP_SIZE = 7


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-v3-recovery-budget-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        expected_external_tree = EXT._tree(stage)

        base = td / "base-v3.cmpct"
        base_stats = V3.build(stage, base, level=LEVEL, group_size=GROUP_SIZE)
        base_scan = V3.verify_and_identities(base)
        if not base_scan.get("ok"):
            raise RuntimeError("exact level-3 ZIP-factor V3 base failed verification")

        recovery = td / "recovery.cmpct"
        recovery_stats = REC.build_recovery(stage, recovery, level=LEVEL, group_size=GROUP_SIZE)
        clean = REC.recover_verify(recovery)
        if not clean.get("ok"):
            raise RuntimeError(f"clean level-3 recovery envelope failed: {clean!r}")

        raw = recovery.read_bytes()
        control_len = int(recovery_stats["control_bytes"])
        primary_bad = td / "primary-bad.cmpct"
        primary_bad.write_bytes(REC._flip(raw, 8 + 4 + 3))
        primary = REC.recover_verify(primary_bad)

        _tail, tail_start = REC._tail_control(raw)
        tail_bad = td / "tail-bad.cmpct"
        tail_bad.write_bytes(REC._flip(raw, tail_start + min(7, control_len - 1)))
        tail = REC.recover_verify(tail_bad)

        both_bad = td / "both-bad.cmpct"
        both_bad.write_bytes(REC._flip(primary_bad.read_bytes(), tail_start + min(7, control_len - 1)))
        both = REC.recover_verify(both_bad)

        zip_archive = td / "archive.zip"
        zip_out = td / "zip-out"
        zip_result = EXT._zip(stage, zip_archive, zip_out)
        EXT._verify_extracted(zip_out, expected_external_tree, "zf-v3-recovery-budget-zip")

        zstd_archive = td / "archive.tar.zst"
        zstd_out = td / "zstd-out"
        zstd_work = td / "zstd-work"
        zstd_work.mkdir()
        zstd_result = EXT._tar_zstd(stage, zstd_archive, zstd_out, zstd_work)
        if not zstd_result.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable")
        EXT._verify_extracted(zstd_out, expected_external_tree, "zf-v3-recovery-budget-zstd19")

        clean_snapshot = REC._snapshot(clean)
        primary_snapshot = REC._snapshot(primary) if primary.get("ok") else None
        tail_snapshot = REC._snapshot(tail) if tail.get("ok") else None

        base_bytes = int(base.stat().st_size)
        recovery_bytes = int(recovery.stat().st_size)
        zip_bytes = int(zip_result["archive_bytes"])
        zstd_bytes = int(zstd_result["archive_bytes"])
        overhead = recovery_bytes - base_bytes
        zstd_headroom_before = zstd_bytes - base_bytes
        zstd_headroom_after = zstd_bytes - recovery_bytes

        gate = {
            "base_profile_is_exact_v3": base_stats.get("format_profile") == V3.PROFILE,
            "level_is_speed_candidate": int(base_stats.get("level", -1)) == LEVEL,
            "group_size_is_speed_candidate": int(base_stats.get("group_size", -1)) == GROUP_SIZE,
            "payload_body_single_copy": int(recovery_stats["payload_body_copies"]) == 1,
            "authenticated_control_copies": int(recovery_stats["control_copies"]) == 2,
            "clean_verified": clean.get("ok") is True,
            "primary_corruption_recovers_from_tail": primary.get("ok") is True
            and primary.get("recovered_from") == "tail",
            "tail_corruption_recovers_from_primary": tail.get("ok") is True
            and tail.get("recovered_from") == "primary",
            "double_control_corruption_fails_closed": both.get("ok") is False,
            "recovered_identity_exact": clean_snapshot == primary_snapshot == tail_snapshot,
            "locality_within_8x": float(clean_snapshot["max_member_read_amplification"]) <= 8.0,
            "decode_unit_within_8mib": int(clean_snapshot["max_decode_unit_bytes"]) <= 8 * 1024 * 1024,
            "base_smaller_than_zstd19": base_bytes < zstd_bytes,
            "recovery_smaller_than_zstd19": recovery_bytes < zstd_bytes,
            "recovery_smaller_than_zip": recovery_bytes < zip_bytes,
            "recovery_overhead_fits_strict_zstd_margin": overhead < zstd_headroom_before,
            "strict_zstd_headroom_remains": zstd_headroom_after > 0,
        }
        gate["passed"] = all(gate.values())

        return {
            "schema": "cmpct-v030-zipfactor-v3-recovery-budget-v1",
            "contract": {
                "candidate_profile": V3.PROFILE,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "payload_body_copies": 1,
                "control_copies": 2,
                "ties_fail": True,
                "selector_change": False,
                "release_credit": False,
            },
            "sizes": {
                "base_v3": base_bytes,
                "recovery": recovery_bytes,
                "zip": zip_bytes,
                "zstd19": zstd_bytes,
                "recovery_overhead": overhead,
                "zstd_headroom_before_recovery": zstd_headroom_before,
                "zstd_headroom_after_recovery": zstd_headroom_after,
            },
            "candidate": recovery_stats,
            "gate": gate,
            "experiment_valid": bool(gate["passed"]),
            "promotion_signal": False,
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("exact level-3 ZIP-factor recovery budget failed")


if __name__ == "__main__":
    main()
