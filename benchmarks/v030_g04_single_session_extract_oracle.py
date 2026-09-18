from __future__ import annotations

"""Research-only oracle for the dominant v0.30 ML extraction debt.

Hypothesis: canonical r25 extraction pays three authenticated G04 metadata/session opens on the healthy path:
(1) manifest member read, (2) content-identity validation, then (3) the actual streamed extraction.  A single
streaming session already authenticates every logical member and owns the exact content identities needed to
validate the filesystem manifest.  Reusing those identities after staging should remove two complete archive
session opens without changing bytes, filesystem semantics, integrity, locality, or publication boundaries.

This benchmark does NOT modify the product.  It compares current PRODUCT.extract against an in-benchmark
single-session counterfactual on the frozen neutral ML workload and requires exact semantic-tree equality.
"""

import argparse
import hashlib
import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_verified_restore as VERIFIED_RESTORE

C = BASE.C
POLICY = BASE.POLICY
FS = BASE.FS
MANIFEST = C.MANIFEST_ADMISSION


def _single_session_g04_extract(archive: Path, dst: Path, *, max_output_bytes: int = POLICY.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    archive = Path(archive)
    dst = Path(dst)
    revision, profile = BASE._revision_for_archive(archive)
    if revision != C.REVISION or profile != "geometry-g04":
        raise RuntimeError(f"oracle requires canonical G04 r25, got {revision}/{profile}")
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    dst.parent.mkdir(parents=True, exist_ok=True)
    wrapper = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-single-session-oracle-", dir=dst.parent))
    content_root = wrapper / "tree"
    installed = False
    try:
        internal_budget = min(POLICY.R.MAX_DECLARED_LOGICAL_BYTES, max_output_bytes + FS.MAX_MANIFEST_BYTES)
        content_root.mkdir(parents=True, exist_ok=True)
        with C._revision25_profile_context():
            session = POLICY.R._G04Session(archive)
            tree = hashlib.sha256()
            logical = 0
            try:
                content_identities = {
                    rel: (int(desc[2]), bytes(desc[3])) for rel, desc in session.meta["files"].items()
                }
                for rel in sorted(session.meta["files"]):
                    logical += POLICY.R._consume_g04_file(
                        session, rel, session.meta["files"][rel], tree, content_root
                    )
                    if logical > internal_budget:
                        raise RuntimeError("G0-G4 extraction exceeds caller output budget")
                if tree.hexdigest() != session.meta["tree_sha256"]:
                    raise RuntimeError("G0-G4 streamed tree identity mismatch")
            finally:
                session.close()

        manifest_path = content_root.joinpath(*FS.FILESYSTEM_MANIFEST.split("/"))
        raw = manifest_path.read_bytes()
        decoded, _encoding = MANIFEST.decode_from_content_identities(
            raw,
            content_identities=content_identities,
            max_path_bytes=POLICY.R.MAX_PATH_BYTES,
            max_entries=C.MAX_MANIFEST_ENTRIES,
        )
        if any(row[1] == "l" and not C._safe_symlink_target(row[7]) for row in decoded["manifest"]["entries"]):
            raise RuntimeError("unsafe r25 symlink target")
        user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
        if user_bytes > max_output_bytes:
            raise RuntimeError("r25 extraction exceeds caller output budget")

        VERIFIED_RESTORE.restore_verified_manifest_tree(content_root, decoded, safe_symlinks=False)
        C._publish_tree(content_root, dst)
        installed = True
    finally:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)


def _timed(fn, archive: Path, dst: Path, expected_tree: str, rounds: int) -> list[float]:
    values = []
    for _ in range(rounds):
        shutil.rmtree(dst, ignore_errors=True)
        started = time.perf_counter()
        fn(archive, dst)
        elapsed = time.perf_counter() - started
        got = PRODUCT.treehash(dst)
        if got != expected_tree:
            raise RuntimeError(f"extraction tree drift: {got} != {expected_tree}")
        values.append(elapsed)
    return values


def run(work_root: Path, rounds: int = 7) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    expected_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    build_stats = PRODUCT.build(source, archive)
    revision, profile = BASE._revision_for_archive(archive)
    if revision != C.REVISION or profile != "geometry-g04":
        raise RuntimeError(f"frozen ML workload no longer selects G04 r25: {revision}/{profile}")

    # Alternate order by pair to reduce thermal/cache/order bias. Each extraction publishes a fresh tree.
    current = []
    oracle = []
    for index in range(rounds):
        order = (("current", PRODUCT.extract), ("oracle", _single_session_g04_extract))
        if index % 2:
            order = tuple(reversed(order))
        for label, fn in order:
            dst = work_root / f"extract-{label}"
            values = _timed(fn, archive, dst, expected_tree, 1)
            (current if label == "current" else oracle).extend(values)

    current_median = statistics.median(current)
    oracle_median = statistics.median(oracle)
    ratio = oracle_median / current_median
    return {
        "schema": "cmpct-v030-g04-single-session-extract-oracle-v1",
        "claim_boundary": "research/oracle evidence only; no product credit",
        "workload": "neutral_hostile_v1/09_ml_artifacts",
        "archive_bytes": archive.stat().st_size,
        "format_revision": revision,
        "format_profile": profile,
        "rounds": rounds,
        "current_extract_s": current,
        "single_session_extract_s": oracle,
        "current_median_s": current_median,
        "single_session_median_s": oracle_median,
        "single_session_to_current_ratio": ratio,
        "saving_pct": (1.0 - ratio) * 100.0,
        "exact_tree_verified_every_round": True,
        "build_selected": build_stats.get("selected"),
        "decision": "MATERIAL_HEADROOM" if ratio <= 0.85 else "INSUFFICIENT_HEADROOM",
        "falsifier": "ratio > 0.85 means duplicate pre-extraction sessions do not own enough of the ML extraction debt",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-single-session-oracle-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-single-session-oracle.json"))
    parser.add_argument("--rounds", type=int, default=7)
    args = parser.parse_args()
    result = run(args.work_root, args.rounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
