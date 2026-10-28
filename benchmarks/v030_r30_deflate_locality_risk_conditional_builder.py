from __future__ import annotations

"""Frozen R30 Deflate locality-risk conditional-retention Builder.

Normative preregistration:
``docs/v030-rnd/R30_DEFLATE_LOCALITY_RISK_CONDITIONAL_BUILDER_PREREG.md``.

Diagnostic only. A positive result can authorize only the superseding protected-workload
Builder required by the preregistration; it cannot edit product policy or grant release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PRODUCT_SUBSTRATE = "b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a"
SCHEMA = "cmpct-v030-r30-deflate-locality-risk-conditional-builder-v1"
TARGET_SUITE = "neutral_hostile_v1"
TARGET_NAME = "06_incremental_backups"
NESTED_MEMBER = "snapshot_2.zip"
MATURE_DEFLATE_REUSE_MIN = 65_536
MAX_LOCALITY = 8.0
REPETITIONS = 3
ARMS = ("release-all-exact", "mature-64k", "locality-risk-v1")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _material_runtime_regression(base_s: float, candidate_s: float) -> bool:
    delta = candidate_s - base_s
    return delta > 0.003 and (delta / base_s if base_s > 0 else float("inf")) > 0.05


def _zip_members(root: Path) -> list[str]:
    rows: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() in {".zip", ".whl"}:
            rows.append(path.relative_to(root).as_posix())
    return rows


def _build_arm(arm: str, source: Path, archive: Path) -> tuple[dict, dict, dict]:
    from cmpct.builder import Builder, Candidate
    from experiments import entropygraph_v030_release_product as PRODUCT

    class ConditionalDeflateBuilder(Builder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.r30_retained_canonical_count = 0
            self.r30_retained_canonical_bytes = 0
            self.r30_retained_secondary_count = 0
            self.r30_retained_secondary_bytes = 0
            self.r30_regenerated_canonical_count = 0
            self.r30_regenerated_canonical_bytes = 0
            self.r30_regenerated_secondary_count = 0
            self.r30_regenerated_secondary_bytes = 0

        @staticmethod
        def _retain(arm_name: str, raw_bytes: int, stream_bytes: int) -> bool:
            if arm_name == "release-all-exact":
                return True
            if arm_name == "mature-64k":
                return stream_bytes >= MATURE_DEFLATE_REUSE_MIN
            if arm_name == "locality-risk-v1":
                return (
                    stream_bytes >= MATURE_DEFLATE_REUSE_MIN
                    or raw_bytes > int(MAX_LOCALITY * stream_bytes)
                )
            raise ValueError(arm_name)

        def _prepare_deflate_reuse(self):
            additions: list[tuple[bytes, bytes]] = []
            for raw_hash, candidate in list(self.cands.items()):
                if not candidate.deflates:
                    continue
                chosen_hash, (chosen_bytes, _chosen_count) = max(
                    candidate.deflates.items(),
                    key=lambda kv: (kv[1][1], -len(kv[1][0])),
                )
                raw_len = len(candidate.raw)
                if self._retain(arm, raw_len, len(chosen_bytes)):
                    self.canonical_deflate[raw_hash] = chosen_hash
                    self.r30_retained_canonical_count += 1
                    self.r30_retained_canonical_bytes += len(chosen_bytes)
                else:
                    self.r30_regenerated_canonical_count += 1
                    self.r30_regenerated_canonical_bytes += len(chosen_bytes)

                for stream_hash, (stream, _count) in candidate.deflates.items():
                    if stream_hash == chosen_hash:
                        continue
                    if self._retain(arm, raw_len, len(stream)):
                        additions.append((stream_hash, stream))
                        self.r30_retained_secondary_count += 1
                        self.r30_retained_secondary_bytes += len(stream)
                    else:
                        self.r30_regenerated_secondary_count += 1
                        self.r30_regenerated_secondary_bytes += len(stream)

            for stream_hash, stream in additions:
                if stream_hash not in self.cands:
                    self.cands[stream_hash] = Candidate(stream, {".opaque-deflate"}, {})
                else:
                    self.cands[stream_hash].hints.add(".opaque-deflate")
                self.secondary_stream_hashes.add(stream_hash)

    regular_files, largest_member = PRODUCT._regular_user_shape(source)
    dynamic_target = (
        min(PRODUCT.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)
        if largest_member
        else 256 * 1024
    )
    wide_single_file = (
        regular_files == 1 and largest_member >= PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES
    )

    builder = ConditionalDeflateBuilder(source, deflate_reuse_min=0)
    builder.micro_pack_target = int(dynamic_target)
    builder.micro_pack_max_file = int(PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)

    policy = PRODUCT._BASE_IMPL._R24_CDC_POLICY
    previous_wide = getattr(policy, "wide_single_file", False)
    previous_medium = getattr(policy, "medium_binary_pack", False)
    policy.wide_single_file = wide_single_file
    policy.medium_binary_pack = True
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
        "arm": arm,
        "micro_pack_target": int(dynamic_target),
        "micro_pack_max_file": int(PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES),
        "medium_binary_pack": True,
        "wide_single_file": bool(wide_single_file),
        "regular_user_files": int(regular_files),
        "largest_regular_member_bytes": int(largest_member),
        "mature_deflate_reuse_min": MATURE_DEFLATE_REUSE_MIN,
        "locality_risk_ratio": MAX_LOCALITY,
    }
    retention = {
        "retained_canonical_count": builder.r30_retained_canonical_count,
        "retained_canonical_bytes": builder.r30_retained_canonical_bytes,
        "retained_secondary_count": builder.r30_retained_secondary_count,
        "retained_secondary_bytes": builder.r30_retained_secondary_bytes,
        "regenerated_canonical_count": builder.r30_regenerated_canonical_count,
        "regenerated_canonical_stream_bytes": builder.r30_regenerated_canonical_bytes,
        "regenerated_secondary_count": builder.r30_regenerated_secondary_count,
        "regenerated_secondary_stream_bytes": builder.r30_regenerated_secondary_bytes,
    }
    return stats, effective, retention


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member
    from experiments import entropygraph_v030_release_product as PRODUCT

    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    build_stats, effective, retention = _build_arm(arm, source, archive)
    build_wall_s = time.perf_counter() - started
    build_peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    expected_product_tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != expected_product_tree:
        raise RuntimeError(
            f"{arm} product-tree mismatch: {verified.get('tree_sha256')} != {expected_product_tree}"
        )

    member_rows: list[dict] = []
    for member in _zip_members(source):
        raw, locality = _observed_product_member(PRODUCT, archive, member)
        decoded = locality.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError(f"{arm} locality omitted decoded-context bytes for {member}")
        amp = float(locality["max_member_read_amplification"])
        member_rows.append(
            {
                "member": member,
                "member_bytes": len(raw),
                "decoded_context_bytes": int(decoded),
                "decoded_context_amplification": amp,
                "locality_within_8x": amp <= MAX_LOCALITY,
            }
        )

    if not member_rows:
        raise RuntimeError(f"{arm} target contains no measured virtual ZIP/WHL member")

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": expected_product_tree,
        "format_revision": verified.get("format_revision"),
        "format_profile": verified.get("format_profile"),
        "strong_verify_ok": True,
        "build_wall_s": build_wall_s,
        "build_peak_rss_kib": build_peak_rss_kib,
        "effective_policy": effective,
        "deflate_retention": retention,
        "virtual_members": member_rows,
        "max_virtual_member_amplification": max(
            row["decoded_context_amplification"] for row in member_rows
        ),
        "locality_within_8x": all(row["locality_within_8x"] for row in member_rows),
        "build_stats": build_stats,
    }


def _run_worker(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
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
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"R30 worker {arm} emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def _median_summary(repetitions: list[dict]) -> dict:
    return {
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in repetitions)),
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in repetitions)),
        "build_peak_rss_kib": int(
            statistics.median(row["build_peak_rss_kib"] for row in repetitions)
        ),
        "max_virtual_member_amplification": max(
            float(row["max_virtual_member_amplification"]) for row in repetitions
        ),
        "locality_within_8x": all(bool(row["locality_within_8x"]) for row in repetitions),
        "strong_verify_ok": all(bool(row["strong_verify_ok"]) for row in repetitions),
    }


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)

    full_source: Path | None = None
    generator_expected_tree: str | None = None
    generator_observed_tree: str | None = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == TARGET_SUITE and source.name == TARGET_NAME:
            full_source = source
            generator_expected_tree = str(expected["tree_sha256"])
            generator_observed_tree = A.RC.treehash(source)
            break
    if full_source is None or generator_expected_tree is None or generator_observed_tree is None:
        raise RuntimeError("R30 frozen Incremental Backups corpus was not generated")
    if generator_observed_tree != generator_expected_tree:
        raise RuntimeError(
            "R30 generator identity mismatch: "
            f"{generator_observed_tree} != {generator_expected_tree}"
        )

    nested_source_file = full_source / NESTED_MEMBER
    if not nested_source_file.is_file():
        raise RuntimeError(f"R30 frozen nested member missing: {nested_source_file}")
    nested_source_sha256 = _sha256_file(nested_source_file)
    nested_root = work_root / "nested-only"
    nested_root.mkdir(parents=True)
    nested_copy = nested_root / NESTED_MEMBER
    shutil.copyfile(nested_source_file, nested_copy)
    if _sha256_file(nested_copy) != nested_source_sha256:
        raise RuntimeError("R30 nested-only projection changed snapshot_2.zip bytes")

    sources = {"full-backups": full_source, "nested-only": nested_root}
    targets: dict[str, dict] = {}
    substrate_failure = False

    for target_name, source in sources.items():
        arms: dict[str, dict] = {}
        for arm in ARMS:
            repetitions: list[dict] = []
            for repetition in range(1, REPETITIONS + 1):
                archive = work_root / "archives" / target_name / f"{arm}-{repetition}.cmpct"
                row = _run_worker(arm, source, archive)
                row["repetition"] = repetition
                repetitions.append(row)
            arms[arm] = {
                "repetitions": repetitions,
                "median": _median_summary(repetitions),
            }

        trees = {
            row["tree_sha256"]
            for arm_data in arms.values()
            for row in arm_data["repetitions"]
        }
        strong_ok = all(
            row["strong_verify_ok"]
            for arm_data in arms.values()
            for row in arm_data["repetitions"]
        )
        locality_present = all(
            bool(row["virtual_members"])
            and all(member.get("decoded_context_bytes") is not None for member in row["virtual_members"])
            for arm_data in arms.values()
            for row in arm_data["repetitions"]
        )
        if len(trees) != 1 or not strong_ok or not locality_present:
            substrate_failure = True

        base = arms["release-all-exact"]["median"]
        conditional = arms["locality-risk-v1"]["median"]
        mature = arms["mature-64k"]["median"]
        conditional["bytes_vs_release"] = conditional["archive_bytes"] - base["archive_bytes"]
        conditional["build_wall_delta_s"] = conditional["build_wall_s"] - base["build_wall_s"]
        conditional["build_wall_delta_fraction"] = (
            conditional["build_wall_delta_s"] / base["build_wall_s"]
            if base["build_wall_s"] > 0
            else None
        )
        conditional["material_runtime_regression"] = _material_runtime_regression(
            base["build_wall_s"], conditional["build_wall_s"]
        )
        conditional["rss_delta_fraction"] = (
            (conditional["build_peak_rss_kib"] - base["build_peak_rss_kib"])
            / base["build_peak_rss_kib"]
            if base["build_peak_rss_kib"] > 0
            else None
        )
        conditional["rss_regression_over_10pct"] = bool(
            conditional["rss_delta_fraction"] is not None
            and conditional["rss_delta_fraction"] > 0.10
        )
        mature["bytes_vs_release"] = mature["archive_bytes"] - base["archive_bytes"]

        targets[target_name] = {
            "source_product_tree_sha256": next(iter(trees)) if len(trees) == 1 else None,
            "arms": arms,
        }

    full_base = targets["full-backups"]["arms"]["release-all-exact"]["median"]
    full_cond = targets["full-backups"]["arms"]["locality-risk-v1"]["median"]
    nested_base = targets["nested-only"]["arms"]["release-all-exact"]["median"]
    nested_cond = targets["nested-only"]["arms"]["locality-risk-v1"]["median"]

    conditional_saves_full = full_cond["archive_bytes"] < full_base["archive_bytes"]
    byte_nonregression = (
        full_cond["archive_bytes"] <= full_base["archive_bytes"]
        and nested_cond["archive_bytes"] <= nested_base["archive_bytes"]
    )
    locality_ok = full_cond["locality_within_8x"] and nested_cond["locality_within_8x"]
    runtime_ok = (
        not full_cond["material_runtime_regression"]
        and not nested_cond["material_runtime_regression"]
    )
    rss_ok = (
        not full_cond["rss_regression_over_10pct"]
        and not nested_cond["rss_regression_over_10pct"]
    )

    if substrate_failure:
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    elif conditional_saves_full and not locality_ok:
        decision = "BYTE_WIN_LOCALITY_FAIL"
    elif conditional_saves_full and byte_nonregression and locality_ok and (not runtime_ok or not rss_ok):
        decision = "BYTE_WIN_RUNTIME_OR_RSS_DEBT"
    elif conditional_saves_full and byte_nonregression and locality_ok and runtime_ok and rss_ok:
        decision = "PROMOTE_CONDITIONAL_TO_GLOBAL_BUILDER"
    else:
        decision = "NO_MATERIAL_CONDITIONAL_WIN"

    return {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "source_head": os.environ.get("GITHUB_SHA"),
        "authority_product_substrate_head": AUTHORITY_PRODUCT_SUBSTRATE,
        "release_fingerprint_at_execution": fingerprint,
        "target": {"suite": TARGET_SUITE, "name": TARGET_NAME},
        "generator_expected_tree_sha256": generator_expected_tree,
        "generator_observed_tree_sha256": generator_observed_tree,
        "nested_member": NESTED_MEMBER,
        "nested_member_sha256": nested_source_sha256,
        "repetitions": REPETITIONS,
        "locality_ceiling": MAX_LOCALITY,
        "mature_deflate_reuse_min": MATURE_DEFLATE_REUSE_MIN,
        "targets": targets,
        "decision_inputs": {
            "conditional_saves_full_backups": conditional_saves_full,
            "byte_nonregression_both_targets": byte_nonregression,
            "locality_within_8x_both_targets": locality_ok,
            "no_material_runtime_regression_both_targets": runtime_ok,
            "rss_within_10pct_both_targets": rss_ok,
        },
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/r30-deflate-locality-risk-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/r30-deflate-locality-risk.json"),
    )
    parser.add_argument("--worker-arm", choices=ARMS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()

    if args.worker_arm:
        if args.source is None or args.archive is None:
            raise SystemExit("worker mode requires --source and --archive")
        print(
            json.dumps(
                _worker(args.worker_arm, args.source, args.archive),
                separators=(",", ":"),
                default=str,
            )
        )
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "release_fingerprint_at_execution": result["release_fingerprint_at_execution"],
                "decision_inputs": result["decision_inputs"],
                "targets": {
                    target: {
                        arm: data["median"]
                        for arm, data in target_data["arms"].items()
                    }
                    for target, target_data in result["targets"].items()
                },
                "decision": result["decision"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
