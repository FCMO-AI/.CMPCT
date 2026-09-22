from __future__ import annotations

"""Frozen R31 regenerable-Deflate codec-effort rehabilitation Builder.

Normative preregistration:
``docs/v030-rnd/R31_REGENERABLE_DEFLATE_CODEC_EFFORT_REHABILITATION_PREREG.md``.

Diagnostic only. A positive result can authorize only the superseding protected-workload/global
rehabilitation Builder required by R30/R31. It cannot edit product policy or grant release credit.
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
SCHEMA = "cmpct-v030-r31-regenerable-deflate-codec-effort-rehab-v1"
TARGET_SUITE = "neutral_hostile_v1"
TARGET_NAME = "06_incremental_backups"
NESTED_MEMBER = "snapshot_2.zip"
MATURE_DEFLATE_REUSE_MIN = 65_536
SPECIALIZED_RAW_MAX = 65_536
MAX_LOCALITY = 8.0
REPETITIONS = 3
ARMS = ("release-all-exact", "full-search", "single-zstd12", "single-zstd9")


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


def _build_arm(arm: str, source: Path, archive: Path) -> tuple[dict, dict, dict, dict]:
    import cmpct.builder as CB
    from experiments import entropygraph_v030_release_product as PRODUCT

    class RehabBuilder(CB.Builder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.r31_retained_canonical_count = 0
            self.r31_retained_canonical_bytes = 0
            self.r31_retained_secondary_count = 0
            self.r31_retained_secondary_bytes = 0
            self.r31_regenerated_canonical_count = 0
            self.r31_regenerated_canonical_bytes = 0
            self.r31_regenerated_secondary_count = 0
            self.r31_regenerated_secondary_bytes = 0
            self.r31_specialized_candidate_count = 0
            self.r31_specialized_raw_bytes = 0

        @staticmethod
        def _retain(arm_name: str, raw_bytes: int, stream_bytes: int) -> bool:
            if arm_name == "release-all-exact":
                return True
            return (
                stream_bytes >= MATURE_DEFLATE_REUSE_MIN
                or raw_bytes > int(MAX_LOCALITY * stream_bytes)
            )

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
                    self.r31_retained_canonical_count += 1
                    self.r31_retained_canonical_bytes += len(chosen_bytes)
                else:
                    self.r31_regenerated_canonical_count += 1
                    self.r31_regenerated_canonical_bytes += len(chosen_bytes)

                for stream_hash, (stream, _count) in candidate.deflates.items():
                    if stream_hash == chosen_hash:
                        continue
                    if self._retain(arm, raw_len, len(stream)):
                        additions.append((stream_hash, stream))
                        self.r31_retained_secondary_count += 1
                        self.r31_retained_secondary_bytes += len(stream)
                    else:
                        self.r31_regenerated_secondary_count += 1
                        self.r31_regenerated_secondary_bytes += len(stream)

            for stream_hash, stream in additions:
                if stream_hash not in self.cands:
                    self.cands[stream_hash] = CB.Candidate(stream, {".opaque-deflate"}, {})
                else:
                    self.cands[stream_hash].hints.add(".opaque-deflate")
                self.secondary_stream_hashes.add(stream_hash)

        def _encode_candidate(self, h: bytes, candidate: CB.Candidate):
            if arm not in {"single-zstd12", "single-zstd9"}:
                return super()._encode_candidate(h, candidate)
            if (
                not candidate.deflates
                or h in self.canonical_deflate
                or h in self.secondary_stream_hashes
                or len(candidate.raw) >= SPECIALIZED_RAW_MAX
            ):
                return super()._encode_candidate(h, candidate)

            self.r31_specialized_candidate_count += 1
            self.r31_specialized_raw_bytes += len(candidate.raw)
            raw = candidate.raw

            if self.dict_hash is not None and h == self.dict_hash:
                return CB.CODEC_RAW, raw, b""

            best = None

            def consider(codec: int, comp: bytes, meta: bytes = b"") -> None:
                nonlocal best
                total = len(comp) + len(meta)
                if best is None or total < best[0]:
                    best = (total, codec, comp, meta)

            # Preserve every inherited non-Zstd candidate on the specialized semantic path.
            if ".wav" in candidate.hints:
                wf = CB.wavflac_compress(raw)
                if wf:
                    comp, meta = wf
                    consider(CB.CODEC_WAVFLAC, comp, meta)
                co = CB.zlib.compressobj(9, CB.zlib.DEFLATED, -15)
                dc = co.compress(raw) + co.flush()
                consider(
                    CB.CODEC_DEFLATE,
                    dc,
                    CB.msgpack.packb([b"generated", 9], use_bin_type=True),
                )

            level = 12 if arm == "single-zstd12" else 9
            comp = CB.zc(raw, level)
            consider(CB.CODEC_ZSTD, comp, CB.msgpack.packb([level], use_bin_type=True))

            if self.dictionary and any(ext in CB.TEXT_EXT for ext in candidate.hints):
                dc = CB.zcd(raw, self.dictionary, 12)
                consider(CB.CODEC_ZSTDDICT, dc, CB.msgpack.packb([12], use_bin_type=True))

            if best and best[0] + 16 < len(raw):
                return best[1], best[2], best[3]
            return CB.CODEC_RAW, raw, b""

    regular_files, largest_member = PRODUCT._regular_user_shape(source)
    dynamic_target = (
        min(PRODUCT.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)
        if largest_member
        else 256 * 1024
    )
    wide_single_file = (
        regular_files == 1 and largest_member >= PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES
    )

    builder = RehabBuilder(source, deflate_reuse_min=0)
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
        "specialized_raw_max": SPECIALIZED_RAW_MAX,
    }
    retention = {
        "retained_canonical_count": builder.r31_retained_canonical_count,
        "retained_canonical_bytes": builder.r31_retained_canonical_bytes,
        "retained_secondary_count": builder.r31_retained_secondary_count,
        "retained_secondary_bytes": builder.r31_retained_secondary_bytes,
        "regenerated_canonical_count": builder.r31_regenerated_canonical_count,
        "regenerated_canonical_stream_bytes": builder.r31_regenerated_canonical_bytes,
        "regenerated_secondary_count": builder.r31_regenerated_secondary_count,
        "regenerated_secondary_stream_bytes": builder.r31_regenerated_secondary_bytes,
    }
    specialized = {
        "candidate_count": builder.r31_specialized_candidate_count,
        "raw_bytes": builder.r31_specialized_raw_bytes,
    }
    return stats, effective, retention, specialized


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member
    from experiments import entropygraph_v030_release_product as PRODUCT

    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    build_stats, effective, retention, specialized = _build_arm(arm, source, archive)
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
        "specialized_codec_path": specialized,
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
        raise RuntimeError(f"R31 worker {arm} emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def _median_summary(repetitions: list[dict]) -> dict:
    archive_shas = {row["archive_sha256"] for row in repetitions}
    if len(archive_shas) != 1:
        raise RuntimeError(f"R31 nondeterministic archive bytes: {sorted(archive_shas)}")
    return {
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in repetitions)),
        "archive_sha256": next(iter(archive_shas)),
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in repetitions)),
        "build_peak_rss_kib": int(
            statistics.median(row["build_peak_rss_kib"] for row in repetitions)
        ),
        "max_virtual_member_amplification": max(
            float(row["max_virtual_member_amplification"]) for row in repetitions
        ),
        "locality_within_8x": all(bool(row["locality_within_8x"]) for row in repetitions),
        "strong_verify_ok": all(bool(row["strong_verify_ok"]) for row in repetitions),
        "specialized_candidate_count": int(
            statistics.median(row["specialized_codec_path"]["candidate_count"] for row in repetitions)
        ),
        "specialized_raw_bytes": int(
            statistics.median(row["specialized_codec_path"]["raw_bytes"] for row in repetitions)
        ),
    }


def _rss_regression_over_10pct(base: dict, candidate: dict) -> bool:
    return candidate["build_peak_rss_kib"] > base["build_peak_rss_kib"] * 1.10


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
        raise RuntimeError("R31 frozen Incremental Backups corpus was not generated")
    if generator_observed_tree != generator_expected_tree:
        raise RuntimeError(
            "R31 generator identity mismatch: "
            f"{generator_observed_tree} != {generator_expected_tree}"
        )

    nested_source_file = full_source / NESTED_MEMBER
    if not nested_source_file.is_file():
        raise RuntimeError(f"R31 frozen nested member missing: {nested_source_file}")
    nested_source_sha256 = _sha256_file(nested_source_file)
    nested_root = work_root / "nested-only"
    nested_root.mkdir(parents=True)
    nested_copy = nested_root / NESTED_MEMBER
    shutil.copyfile(nested_source_file, nested_copy)
    if _sha256_file(nested_copy) != nested_source_sha256:
        raise RuntimeError("R31 nested-only projection changed snapshot_2.zip bytes")

    targets: dict[str, dict] = {}
    substrate_failure = False
    for target_name, source in {"full-backups": full_source, "nested-only": nested_root}.items():
        arms: dict[str, dict] = {}
        for arm in ARMS:
            repetitions: list[dict] = []
            for repetition in range(1, REPETITIONS + 1):
                archive = work_root / "archives" / target_name / f"{arm}-{repetition}.cmpct"
                row = _run_worker(arm, source, archive)
                row["repetition"] = repetition
                repetitions.append(row)
            arms[arm] = {"repetitions": repetitions, "median": _median_summary(repetitions)}

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

        release = arms["release-all-exact"]["median"]
        full_search = arms["full-search"]["median"]
        single12 = arms["single-zstd12"]["median"]
        single9 = arms["single-zstd9"]["median"]
        for candidate in (full_search, single12, single9):
            candidate["bytes_vs_release"] = candidate["archive_bytes"] - release["archive_bytes"]
            candidate["build_wall_delta_s_vs_release"] = (
                candidate["build_wall_s"] - release["build_wall_s"]
            )
            candidate["build_wall_delta_fraction_vs_release"] = (
                candidate["build_wall_delta_s_vs_release"] / release["build_wall_s"]
                if release["build_wall_s"] > 0
                else None
            )
            candidate["material_runtime_regression_vs_release"] = _material_runtime_regression(
                release["build_wall_s"], candidate["build_wall_s"]
            )
            candidate["rss_regression_over_10pct_vs_release"] = _rss_regression_over_10pct(
                release, candidate
            )
        single12["byte_identity_with_full_search"] = (
            single12["archive_bytes"] == full_search["archive_bytes"]
            and single12["archive_sha256"] == full_search["archive_sha256"]
        )
        single9["byte_identity_with_full_search"] = (
            single9["archive_bytes"] == full_search["archive_bytes"]
            and single9["archive_sha256"] == full_search["archive_sha256"]
        )
        targets[target_name] = {
            "source_product_tree_sha256": next(iter(trees)) if len(trees) == 1 else None,
            "arms": arms,
        }

    preferred = [
        targets[name]["arms"]["single-zstd12"]["median"]
        for name in ("full-backups", "nested-only")
    ]
    fallback9 = [
        targets[name]["arms"]["single-zstd9"]["median"]
        for name in ("full-backups", "nested-only")
    ]

    specialized_executes = all(row["specialized_candidate_count"] > 0 for row in preferred)
    preferred_identity = all(row["byte_identity_with_full_search"] for row in preferred)
    preferred_locality = all(row["locality_within_8x"] for row in preferred)
    preferred_rss = all(not row["rss_regression_over_10pct_vs_release"] for row in preferred)
    preferred_runtime = all(
        not row["material_runtime_regression_vs_release"] for row in preferred
    )
    preferred_strictly_smaller_than_release = all(row["bytes_vs_release"] < 0 for row in preferred)
    fallback9_smaller = all(row["bytes_vs_release"] < 0 for row in fallback9)
    fallback9_runtime = all(
        not row["material_runtime_regression_vs_release"] for row in fallback9
    )
    fallback9_locality = all(row["locality_within_8x"] for row in fallback9)
    fallback9_rss = all(not row["rss_regression_over_10pct_vs_release"] for row in fallback9)

    if substrate_failure:
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    elif (
        preferred_identity
        and preferred_locality
        and preferred_rss
        and preferred_runtime
        and specialized_executes
    ):
        decision = "PROMOTE_SINGLE12_TO_GLOBAL_REHAB_BUILDER"
    elif preferred_identity and preferred_locality and preferred_rss and specialized_executes:
        decision = "BYTE_IDENTITY_WIN_RUNTIME_DEBT_REMAINS"
    elif (
        preferred_strictly_smaller_than_release
        and preferred_locality
        and preferred_rss
        and preferred_runtime
        and specialized_executes
    ):
        decision = "PARTIAL_BYTE_RETENTION_RUNTIME_WIN"
    elif fallback9_smaller and fallback9_runtime and fallback9_locality and fallback9_rss:
        decision = "SINGLE9_ONLY_TRADEOFF"
    else:
        decision = "NO_REHABILITATION"

    return {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD"),
        "github_sha_diagnostic": os.environ.get("GITHUB_SHA"),
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
        "specialized_raw_max": SPECIALIZED_RAW_MAX,
        "targets": targets,
        "decision_inputs": {
            "specialized_executes_both_targets": specialized_executes,
            "single12_byte_identity_with_full_search_both_targets": preferred_identity,
            "single12_locality_within_8x_both_targets": preferred_locality,
            "single12_rss_within_10pct_release_both_targets": preferred_rss,
            "single12_no_material_runtime_regression_vs_release_both_targets": preferred_runtime,
            "single12_strictly_smaller_than_release_both_targets": preferred_strictly_smaller_than_release,
            "single9_strictly_smaller_than_release_both_targets": fallback9_smaller,
            "single9_no_material_runtime_regression_vs_release_both_targets": fallback9_runtime,
        },
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/r31-regenerable-deflate-codec-effort-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/r31-regenerable-deflate-codec-effort.json"),
    )
    parser.add_argument("--worker-arm", choices=ARMS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()

    if args.worker_arm:
        if args.source is None or args.archive is None:
            raise SystemExit("worker mode requires --source and --archive")
        print(json.dumps(_worker(args.worker_arm, args.source, args.archive), separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence_head": result["evidence_head"],
                "release_fingerprint_at_execution": result["release_fingerprint_at_execution"],
                "decision_inputs": result["decision_inputs"],
                "targets": {
                    target: {arm: data["median"] for arm, data in target_data["arms"].items()}
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
