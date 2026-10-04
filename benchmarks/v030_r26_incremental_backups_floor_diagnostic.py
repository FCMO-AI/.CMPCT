from __future__ import annotations

"""Frozen R26 diagnosis for the Incremental Backups canonical product-floor regression.

Normative preregistration:
``docs/v030-rnd/R26_INCREMENTAL_BACKUPS_PRODUCT_FLOOR_DIAGNOSTIC_PREREG.md``.

This instrument is diagnostic only. It cannot grant release credit or relax the genuine-r24/product-locality laws.
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
EXPECTED_PRODUCT_FINGERPRINT = "aa5693f6d5899e61753bf005b70f3460f82f477535d941807d14e35788e7c1ee"
ARMS = ("genuine-r24", "release-r24", "current-product")


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
        raise RuntimeError("R26 target has no regular member")
    size, rel = max(rows, key=lambda item: (item[0], item[1]))
    return rel, size


def _worker(arm: str, source: Path, archive: Path, member: str) -> dict:
    from cmpct.builder import Builder
    from experiments import entropygraph_v030_release_product as PRODUCT
    from benchmarks.v030_perf_worker_canonical import _observed_product_member

    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if arm == "genuine-r24":
        build_stats = dict(Builder(source).build(archive))
        selection = {"selected": "genuine-canonical-r24"}
    elif arm == "release-r24":
        build_stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
        selection = {"selected": "release-locality-bounded-r24"}
    elif arm == "current-product":
        build_stats = dict(PRODUCT.build(source, archive))
        selection = {
            key: build_stats.get(key)
            for key in (
                "selected",
                "format_revision",
                "format_profile",
                "r24_product_bytes",
                "r25_product_bytes",
                "r25_attempted",
                "r25_reject_reason",
            )
        }
    else:  # pragma: no cover
        raise ValueError(arm)
    build_wall_s = time.perf_counter() - started
    build_peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    expected_tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(
            f"{arm} product-tree mismatch: {verified.get('tree_sha256')} != {expected_tree}"
        )

    raw, locality = _observed_product_member(PRODUCT, archive, member)
    amp = float(locality["max_member_read_amplification"])
    decoded = locality.get("decoded_context_bytes")
    if decoded is None:
        raise RuntimeError(f"{arm} locality omitted decoded-context bytes")

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
        "selection": selection,
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
        raise RuntimeError(f"R26 worker {arm} emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)
    if fingerprint != EXPECTED_PRODUCT_FINGERPRINT:
        raise RuntimeError(
            "R26 frozen product fingerprint drift: "
            f"{fingerprint} != {EXPECTED_PRODUCT_FINGERPRINT}; superseding freeze required"
        )

    target_source: Path | None = None
    expected_historical_tree: str | None = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == TARGET_SUITE and source.name == TARGET_NAME:
            target_source = source
            expected_historical_tree = expected
            break
    if target_source is None:
        raise RuntimeError("R26 frozen Incremental Backups corpus was not generated")

    member, member_bytes = _largest_regular_member(target_source)
    rows = {
        arm: _run_worker(arm, target_source, work_root / "archives" / f"{arm}.cmpct", member)
        for arm in ARMS
    }
    trees = {row["tree_sha256"] for row in rows.values()}
    if len(trees) != 1:
        raise RuntimeError(f"R26 arm product identities diverged: {trees!r}")

    genuine = rows["genuine-r24"]
    release = rows["release-r24"]
    product = rows["current-product"]
    deltas = {
        "release_r24_minus_genuine_r24_bytes": int(release["archive_bytes"]) - int(genuine["archive_bytes"]),
        "current_product_minus_genuine_r24_bytes": int(product["archive_bytes"]) - int(genuine["archive_bytes"]),
        "current_product_minus_release_r24_bytes": int(product["archive_bytes"]) - int(release["archive_bytes"]),
    }

    if int(product["archive_bytes"]) <= int(genuine["archive_bytes"]):
        decision = "D1_REPRODUCTION_OR_SUBSTRATE_MISMATCH"
    elif not bool(genuine["locality_within_8x"]):
        decision = "D3_D4_GENUINE_R24_BYTE_FLOOR_EXPORTS_LOCALITY_DEBT"
    else:
        decision = "D2_LAWFUL_GENUINE_R24_FLOOR_EXISTS_REQUIRE_CARRYING_COST_BUILDER"

    return {
        "schema": "cmpct-v030-r26-incremental-backups-floor-diagnostic-v1",
        "status": "diagnostic-only-no-release-credit",
        "source_head": os.environ.get("GITHUB_SHA"),
        "product_fingerprint": fingerprint,
        "authority_substrate_head": "b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a",
        "target": {"suite": TARGET_SUITE, "name": TARGET_NAME},
        "historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": next(iter(trees)),
        "largest_regular_member": member,
        "largest_regular_member_bytes": member_bytes,
        "locality_ceiling": MAX_LOCALITY,
        "arms": rows,
        "deltas": deltas,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r26-backups-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r26-backups.json"))
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
        "product_fingerprint": result["product_fingerprint"],
        "deltas": result["deltas"],
        "locality": {
            arm: row["decoded_context_amplification"] for arm, row in result["arms"].items()
        },
        "decision": result["decision"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
