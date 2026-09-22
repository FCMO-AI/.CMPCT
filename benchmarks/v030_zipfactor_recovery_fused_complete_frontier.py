from __future__ import annotations

"""Complete external frontier for the exact ZIP-factor V3 recovery envelope.

This is the next productization boundary after the byte-identical fused V3 builder + in-process Rust V3 verifier
proved a strict four-way win. The shipping format still owes recovery, so this oracle measures the exact level-3 /
group-7 recovery envelope with the already-proven fused builder and *mandatory recovery verification* inside CMPCT
creation timing. It deliberately does not borrow the base-V3 speed result.

The result is research evidence only. A strict four-way win here would justify native/platform productization of the
recovery representation; a loss identifies the recovery verifier/build envelope as the next CPU owner. No selector
or release credit is granted by this lane.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_recovery_oracle as REC
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED

ROUNDS = 9
LEVEL = 3
GROUP_SIZE = 7


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-rec-complete-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        expected_external_tree = EXT._tree(stage)

        cmpct_samples: list[float] = []
        build_samples: list[float] = []
        verify_samples: list[float] = []
        zip_samples: list[float] = []
        zstd_samples: list[float] = []
        candidate_sizes: set[int] = set()
        candidate_sha: set[str] = set()
        candidate_stats: dict | None = None
        clean_snapshot: dict | None = None

        order = ("cmpct", "zip", "zstd")
        original_build = V3.build
        V3.build = FUSED.build
        try:
            for round_index in range(ROUNDS):
                rotated = order[round_index % len(order) :] + order[: round_index % len(order)]
                for kind in rotated:
                    if kind == "cmpct":
                        archive = td / f"candidate-{round_index}.cmpct"
                        t0 = time.perf_counter()
                        stats = REC.build_recovery(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
                        t1 = time.perf_counter()
                        verified = REC.recover_verify(archive)
                        t2 = time.perf_counter()
                        if not verified.get("ok"):
                            raise RuntimeError(f"recovery candidate failed strong verification: {verified!r}")
                        snap = REC._snapshot(verified)
                        if clean_snapshot is None:
                            clean_snapshot = snap
                        elif snap != clean_snapshot:
                            raise RuntimeError("recovery semantic identity changed between rounds")
                        if not stats.get("fused_group_finalize"):
                            raise RuntimeError("recovery frontier did not execute fused V3 builder")
                        candidate_sizes.add(int(archive.stat().st_size))
                        import hashlib
                        candidate_sha.add(hashlib.sha256(archive.read_bytes()).hexdigest())
                        candidate_stats = stats
                        build_samples.append(t1 - t0)
                        verify_samples.append(t2 - t1)
                        cmpct_samples.append(t2 - t0)
                    elif kind == "zip":
                        archive = td / f"archive-{round_index}.zip"
                        out = td / f"zip-out-{round_index}"
                        result = EXT._zip(stage, archive, out)
                        EXT._verify_extracted(out, expected_external_tree, "zf-rec-complete-zip")
                        zip_samples.append(float(result["create_s"]))
                    else:
                        archive = td / f"archive-{round_index}.tar.zst"
                        out = td / f"zstd-out-{round_index}"
                        work = td / f"zstd-work-{round_index}"
                        work.mkdir()
                        result = EXT._tar_zstd(stage, archive, out, work)
                        if not result.get("available"):
                            raise RuntimeError("solid Zstd-19 unavailable")
                        EXT._verify_extracted(out, expected_external_tree, "zf-rec-complete-zstd19")
                        zstd_samples.append(float(result["create_s"]))
        finally:
            V3.build = original_build

        if len(candidate_sizes) != 1 or len(candidate_sha) != 1 or candidate_stats is None or clean_snapshot is None:
            raise RuntimeError("recovery candidate was not deterministic")

        # Rebuild comparator sizes once on the same normalized stage; timing samples above remain the rotated values.
        zip_archive = td / "size.zip"
        zip_out = td / "size-zip-out"
        zip_size_result = EXT._zip(stage, zip_archive, zip_out)
        zstd_archive = td / "size.tar.zst"
        zstd_out = td / "size-zstd-out"
        zstd_work = td / "size-zstd-work"
        zstd_work.mkdir()
        zstd_size_result = EXT._tar_zstd(stage, zstd_archive, zstd_out, zstd_work)
        if not zstd_size_result.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable for size ratchet")

        cmpct_bytes = next(iter(candidate_sizes))
        zip_bytes = int(zip_size_result["archive_bytes"])
        zstd_bytes = int(zstd_size_result["archive_bytes"])
        med_cmpct = _median(cmpct_samples)
        med_zip = _median(zip_samples)
        med_zstd = _median(zstd_samples)
        strict = cmpct_bytes < zip_bytes and cmpct_bytes < zstd_bytes and med_cmpct < med_zip and med_cmpct < med_zstd

        return {
            "schema": "cmpct-v030-zipfactor-recovery-fused-complete-frontier-v1",
            "contract": {
                "rounds": ROUNDS,
                "candidate_profile": "zip-framing-factor-recovery-oracle-v4",
                "base_profile": V3.PROFILE,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "cmpct_timing": "fused-v3-build-plus-recovery-envelope-plus-mandatory-recovery-strong-verify",
                "zip_timing": "external-harness-deflate9-create",
                "zstd19_timing": "external-harness-solid-tar-plus-zstd19-create",
                "ties_fail": True,
                "archive_bytes_changed_from_recovery_candidate": False,
                "selector_change": False,
                "release_credit": False,
            },
            "candidate": {
                **candidate_stats,
                "archive_sha256": next(iter(candidate_sha)),
                "max_member_read_amplification": clean_snapshot["max_member_read_amplification"],
                "max_decode_unit_bytes": clean_snapshot["max_decode_unit_bytes"],
            },
            "sizes": {"cmpct": cmpct_bytes, "zip": zip_bytes, "zstd19": zstd_bytes},
            "samples_s": {"cmpct": cmpct_samples, "zip": zip_samples, "zstd19": zstd_samples},
            "cmpct_phase_samples_s": {"build": build_samples, "verify": verify_samples},
            "medians_s": {"cmpct": med_cmpct, "zip": med_zip, "zstd19": med_zstd},
            "cmpct_phase_medians_s": {"build": _median(build_samples), "verify": _median(verify_samples)},
            "strict_four_way_win": strict,
            "experiment_valid": (
                len(cmpct_samples) == len(zip_samples) == len(zstd_samples) == ROUNDS
                and cmpct_bytes < zip_bytes
                and cmpct_bytes < zstd_bytes
                and float(clean_snapshot["max_member_read_amplification"]) <= 8.0
                and int(clean_snapshot["max_decode_unit_bytes"]) <= 8 * 1024 * 1024
            ),
            "promotion_signal": strict,
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
        raise SystemExit("ZIP-factor recovery fused complete frontier invalid")


if __name__ == "__main__":
    main()
