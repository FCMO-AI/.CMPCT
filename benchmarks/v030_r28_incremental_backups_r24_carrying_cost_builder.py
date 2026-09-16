from __future__ import annotations

"""Frozen R28 attribution Builder for Incremental Backups r24 carrying cost.

Normative preregistration:
``docs/v030-rnd/R28_INCREMENTAL_BACKUPS_R24_CARRYING_COST_BUILDER_PREREG.md``.

Diagnostic only: this instrument cannot grant release credit or authorize product policy changes.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

ROOT = Path(__file__).resolve().parents[1]
TARGET_SUITE = "neutral_hostile_v1"
TARGET_NAME = "06_incremental_backups"
MAX_LOCALITY = 8.0
EXPECTED_R27_GAP_BYTES = 52_024
AUTHORITY_PRODUCT_SUBSTRATE = "b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a"
MATURE_DEFLATE_REUSE_MIN = 65_536
MATURE_MICRO_PACK_TARGET = 256 * 1024
MATURE_MICRO_PACK_MAX_FILE = 32 * 1024
ARMS = (
    "genuine-r24",
    "release-r24",
    "mature-deflate-threshold",
    "mature-pack-target",
    "mature-pack-max-file",
    "no-medium-bin-pack",
)
EXPERIMENTAL_ARMS = ARMS[2:]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _largest_regular_member(root: Path) -> tuple[str, int]:
    rows: list[tuple[int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            rows.append((int(path.stat().st_size), rel))
    if not rows:
        raise RuntimeError("R28 target has no regular member")
    size, rel = max(rows, key=lambda item: (item[0], item[1]))
    return rel, size


def _release_variant(arm: str, source: Path, archive: Path) -> tuple[dict, dict]:
    from cmpct.builder import Builder
    from experiments import entropygraph_v030_release_product as PRODUCT

    regular_files, largest_member = PRODUCT._regular_user_shape(source)
    dynamic_target = min(PRODUCT.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member) if largest_member else MATURE_MICRO_PACK_TARGET

    deflate_reuse_min = (
        MATURE_DEFLATE_REUSE_MIN
        if arm == "mature-deflate-threshold"
        else PRODUCT.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES
    )
    micro_pack_target = MATURE_MICRO_PACK_TARGET if arm == "mature-pack-target" else dynamic_target
    micro_pack_max_file = (
        MATURE_MICRO_PACK_MAX_FILE
        if arm == "mature-pack-max-file"
        else PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES
    )
    medium_binary_pack = arm != "no-medium-bin-pack"
    wide_single_file = regular_files == 1 and largest_member >= PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES

    builder = Builder(source, deflate_reuse_min=deflate_reuse_min)
    builder.micro_pack_target = int(micro_pack_target)
    builder.micro_pack_max_file = int(micro_pack_max_file)

    policy = PRODUCT._BASE_IMPL._R24_CDC_POLICY
    previous_wide = getattr(policy, "wide_single_file", False)
    previous_medium = getattr(policy, "medium_binary_pack", False)
    policy.wide_single_file = wide_single_file
    policy.medium_binary_pack = medium_binary_pack
    try:
        stats = dict(builder.build(archive))
    finally:
        policy.wide_single_file = previous_wide
        policy.medium_binary_pack = previous_medium

    elision = PRODUCT._R24_DEAD_DICT.elide_dead_dictionary_in_place(archive)
    stats.update(
        archive_bytes=archive.stat().st_size,
        r24_dead_dictionary_elision=elision["reason"],
        r24_dead_dictionary_saving_bytes=int(elision.get("saving_bytes", 0)),
    )
    effective = {
        "deflate_reuse_min": int(deflate_reuse_min),
        "micro_pack_target": int(micro_pack_target),
        "micro_pack_max_file": int(micro_pack_max_file),
        "medium_binary_pack": bool(medium_binary_pack),
        "wide_single_file": bool(wide_single_file),
        "regular_user_files": int(regular_files),
        "largest_regular_member_bytes": int(largest_member),
    }
    return stats, effective


def _worker(arm: str, source: Path, archive: Path, member: str) -> dict:
    from cmpct.builder import Builder
    from experiments import entropygraph_v030_release_product as PRODUCT
    from benchmarks.v030_perf_worker_canonical import _observed_product_member

    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if arm == "genuine-r24":
        build_stats = dict(Builder(source).build(archive))
        effective = {
            "deflate_reuse_min": MATURE_DEFLATE_REUSE_MIN,
            "micro_pack_target": MATURE_MICRO_PACK_TARGET,
            "micro_pack_max_file": MATURE_MICRO_PACK_MAX_FILE,
            "medium_binary_pack": False,
            "wide_single_file": False,
        }
    elif arm == "release-r24":
        build_stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
        regular_files, largest = PRODUCT._regular_user_shape(source)
        effective = {
            "deflate_reuse_min": int(PRODUCT.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES),
            "micro_pack_target": int(build_stats.get("micro_pack_target_release_bytes", 0)),
            "micro_pack_max_file": int(build_stats.get("micro_pack_max_file_release_bytes", 0)),
            "medium_binary_pack": True,
            "wide_single_file": bool(regular_files == 1 and largest >= PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES),
            "regular_user_files": int(regular_files),
            "largest_regular_member_bytes": int(largest),
        }
    elif arm in EXPERIMENTAL_ARMS:
        build_stats, effective = _release_variant(arm, source, archive)
    else:  # pragma: no cover
        raise ValueError(arm)
    build_wall_s = time.perf_counter() - started
    build_peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    expected_tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{arm} product-tree mismatch: {verified.get('tree_sha256')} != {expected_tree}")

    raw, locality = _observed_product_member(PRODUCT, archive, member)
    decoded = locality.get("decoded_context_bytes")
    if decoded is None:
        raise RuntimeError(f"{arm} locality omitted decoded-context bytes")
    amp = float(locality["max_member_read_amplification"])

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": expected_tree,
        "format_revision": verified.get("format_revision"),
        "format_profile": verified.get("format_profile"),
        "strong_verify_ok": True,
        "selected_member": member,
        "selected_member_bytes": len(raw),
        "decoded_context_bytes": int(decoded),
        "decoded_context_amplification": amp,
        "locality_within_8x": amp <= MAX_LOCALITY,
        "build_wall_s": build_wall_s,
        "build_peak_rss_kib": build_peak_rss_kib,
        "effective_policy": effective,
        "build_stats": build_stats,
    }


def _run_worker(arm: str, source: Path, archive: Path, member: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-arm",
            arm,
            "--source",
            str(source),
            "--archive",
            str(archive),
            "--member",
            member,
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"R28 worker {arm} emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)

    target_source: Path | None = None
    expected_historical_tree: str | None = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == TARGET_SUITE and source.name == TARGET_NAME:
            target_source = source
            expected_historical_tree = expected
            break
    if target_source is None:
        raise RuntimeError("R28 frozen Incremental Backups corpus was not generated")

    member, member_bytes = _largest_regular_member(target_source)
    rows = {
        arm: _run_worker(arm, target_source, work_root / "archives" / f"{arm}.cmpct", member)
        for arm in ARMS
    }
    trees = {row["tree_sha256"] for row in rows.values()}
    if len(trees) != 1 or not all(row["strong_verify_ok"] for row in rows.values()):
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    else:
        genuine_bytes = int(rows["genuine-r24"]["archive_bytes"])
        release_bytes = int(rows["release-r24"]["archive_bytes"])
        observed_gap = release_bytes - genuine_bytes
        for arm in EXPERIMENTAL_ARMS:
            arm_bytes = int(rows[arm]["archive_bytes"])
            removed = release_bytes - arm_bytes
            rows[arm]["bytes_vs_release"] = arm_bytes - release_bytes
            rows[arm]["bytes_vs_genuine"] = arm_bytes - genuine_bytes
            rows[arm]["positive_gap_removed_bytes"] = max(0, removed)
            rows[arm]["positive_gap_removed_fraction"] = max(0, removed) / observed_gap if observed_gap > 0 else None

        restoring = [
            arm for arm in EXPERIMENTAL_ARMS
            if int(rows[arm]["archive_bytes"]) <= genuine_bytes
        ]
        locality_debt = [arm for arm in restoring if not bool(rows[arm]["locality_within_8x"])]
        lawful_restoring = [arm for arm in restoring if bool(rows[arm]["locality_within_8x"])]
        partial = [
            arm for arm in EXPERIMENTAL_ARMS
            if int(rows[arm]["archive_bytes"]) < release_bytes
        ]

        if observed_gap != EXPECTED_R27_GAP_BYTES:
            decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
        elif locality_debt:
            decision = "LOCALITY_DEBT"
        elif len(lawful_restoring) == 1:
            decision = "SINGLE_OWNER"
        elif len(lawful_restoring) > 1:
            decision = "MULTIPLE_SINGLE_OWNERS"
        elif partial:
            decision = "PARTIAL_OWNER"
        else:
            decision = "NO_ONE_FACTOR_EXPLANATION"

    genuine_bytes = int(rows["genuine-r24"]["archive_bytes"])
    release_bytes = int(rows["release-r24"]["archive_bytes"])
    return {
        "schema": "cmpct-v030-r28-incremental-backups-r24-carrying-cost-builder-v1",
        "status": "diagnostic-only-no-release-credit",
        "source_head": os.environ.get("GITHUB_SHA"),
        "authority_product_substrate_head": AUTHORITY_PRODUCT_SUBSTRATE,
        "release_fingerprint_at_execution": fingerprint,
        "target": {"suite": TARGET_SUITE, "name": TARGET_NAME},
        "historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": next(iter(trees)) if len(trees) == 1 else None,
        "largest_regular_member": member,
        "largest_regular_member_bytes": member_bytes,
        "locality_ceiling": MAX_LOCALITY,
        "expected_r27_gap_bytes": EXPECTED_R27_GAP_BYTES,
        "observed_release_minus_genuine_bytes": release_bytes - genuine_bytes,
        "arms": rows,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r28-backups-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r28-backups.json"))
    parser.add_argument("--worker-arm", choices=ARMS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--member")
    args = parser.parse_args()

    if args.worker_arm:
        if args.source is None or args.archive is None or not args.member:
            raise SystemExit("worker mode requires --source, --archive and --member")
        print(json.dumps(_worker(args.worker_arm, args.source, args.archive, args.member), separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "release_fingerprint_at_execution": result["release_fingerprint_at_execution"],
        "observed_release_minus_genuine_bytes": result["observed_release_minus_genuine_bytes"],
        "arms": {
            arm: {
                "archive_bytes": row["archive_bytes"],
                "amplification": row["decoded_context_amplification"],
                "bytes_vs_release": row.get("bytes_vs_release"),
                "bytes_vs_genuine": row.get("bytes_vs_genuine"),
            }
            for arm, row in result["arms"].items()
        },
        "decision": result["decision"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
