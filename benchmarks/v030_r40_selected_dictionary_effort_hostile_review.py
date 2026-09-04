from __future__ import annotations

"""Frozen R40 global hostile review for the R39 selected-dictionary effort win.

Normative preregistration:
``docs/v030-rnd/R40_SELECTED_DICTIONARY_EFFORT_HOSTILE_REVIEW_PREREG.md``.
Diagnostic/Forge evidence only; no product or release credit.
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

import cmpct.builder as CB
from benchmarks import v030_r39_selected_dictionary_effort_rehabilitation as R39
from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r40-selected-dictionary-effort-hostile-review-v1"
ARMS = ("release-all-exact", "dict12-control", "family-dict9")
REPETITIONS = 5
MAX_LOCALITY = 8.0
SPECIALIZED_RAW_MAX = 65_536
EXPECTED_PUBLIC_WORKLOADS = 15
EXPECTED_REPAIRED_V029_BYTES = 137_499_525
V030_ABSOLUTE_HURDLE_BYTES = 687_783


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _material_runtime_regression(base_s: float, candidate_s: float) -> bool:
    delta = candidate_s - base_s
    return delta > 0.003 and (delta / base_s if base_s > 0 else float("inf")) > 0.05


def _build_arm(arm: str, source: Path, archive: Path) -> tuple[dict, dict, dict]:
    """Re-express frozen R39 mechanism while adding hostile-review nomination accounting."""
    from experiments import entropygraph_v030_release_product as PRODUCT

    class R40Builder(CB.Builder):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.retained_canonical_count = 0
            self.retained_canonical_bytes = 0
            self.regenerated_canonical_count = 0
            self.regenerated_canonical_bytes = 0
            self.retained_secondary_count = 0
            self.retained_secondary_bytes = 0
            self.regenerated_secondary_count = 0
            self.regenerated_secondary_bytes = 0
            self.family_predicate_examinations = 0
            self.specialized_count = 0
            self.specialized_raw_bytes = 0

        @staticmethod
        def _retain(raw_bytes: int, stream_bytes: int) -> bool:
            if arm == "release-all-exact":
                return True
            return stream_bytes >= 65_536 or raw_bytes > int(MAX_LOCALITY * stream_bytes)

        def _prepare_deflate_reuse(self):
            additions = []
            for raw_hash, candidate in list(self.cands.items()):
                if not candidate.deflates:
                    continue
                chosen_hash, (chosen_bytes, _count) = max(
                    candidate.deflates.items(), key=lambda kv: (kv[1][1], -len(kv[1][0]))
                )
                if self._retain(len(candidate.raw), len(chosen_bytes)):
                    self.canonical_deflate[raw_hash] = chosen_hash
                    self.retained_canonical_count += 1
                    self.retained_canonical_bytes += len(chosen_bytes)
                else:
                    self.regenerated_canonical_count += 1
                    self.regenerated_canonical_bytes += len(chosen_bytes)
                for sh, (stream, _count) in candidate.deflates.items():
                    if sh == chosen_hash:
                        continue
                    if self._retain(len(candidate.raw), len(stream)):
                        additions.append((sh, stream))
                        self.retained_secondary_count += 1
                        self.retained_secondary_bytes += len(stream)
                    else:
                        self.regenerated_secondary_count += 1
                        self.regenerated_secondary_bytes += len(stream)
            for sh, stream in additions:
                if sh not in self.cands:
                    self.cands[sh] = CB.Candidate(stream, {".opaque-deflate"}, {})
                else:
                    self.cands[sh].hints.add(".opaque-deflate")
                self.secondary_stream_hashes.add(sh)

        def _is_family(self, h: bytes, c: CB.Candidate) -> bool:
            self.family_predicate_examinations += 1
            return bool(
                c.deflates
                and h not in self.canonical_deflate
                and h not in self.secondary_stream_hashes
                and len(c.raw) < SPECIALIZED_RAW_MAX
                and any(ext in CB.TEXT_EXT for ext in c.hints)
                and self.dictionary
            )

        def _encode_candidate(self, h: bytes, c: CB.Candidate):
            if arm == "release-all-exact":
                return super()._encode_candidate(h, c)
            if (
                not c.deflates
                or h in self.canonical_deflate
                or h in self.secondary_stream_hashes
                or len(c.raw) >= SPECIALIZED_RAW_MAX
            ):
                return super()._encode_candidate(h, c)

            raw = c.raw
            family = self._is_family(h, c)
            if family:
                self.specialized_count += 1
                self.specialized_raw_bytes += len(raw)
            if self.dict_hash is not None and h == self.dict_hash:
                return CB.CODEC_RAW, raw, b""

            best = None

            def consider(codec: int, comp: bytes, meta: bytes = b"") -> None:
                nonlocal best
                total = len(comp) + len(meta)
                if best is None or total < best[0]:
                    best = (total, codec, comp, meta)

            if ".wav" in c.hints:
                wf = CB.wavflac_compress(raw)
                if wf:
                    comp, meta = wf
                    consider(CB.CODEC_WAVFLAC, comp, meta)
                co = CB.zlib.compressobj(9, CB.zlib.DEFLATED, -15)
                dc = co.compress(raw) + co.flush()
                consider(CB.CODEC_DEFLATE, dc, CB.msgpack.packb([b"generated", 9], use_bin_type=True))

            if self.dictionary and any(ext in CB.TEXT_EXT for ext in c.hints):
                level = 9 if arm == "family-dict9" and family else 12
                dc = CB.zcd(raw, self.dictionary, level)
                consider(CB.CODEC_ZSTDDICT, dc, CB.msgpack.packb([level], use_bin_type=True))

            if best and best[0] + 16 < len(raw):
                return best[1], best[2], best[3]
            return CB.CODEC_RAW, raw, b""

    regular_files, largest_member = PRODUCT._regular_user_shape(source)
    dynamic_target = min(PRODUCT.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member) if largest_member else 256 * 1024
    wide_single_file = regular_files == 1 and largest_member >= PRODUCT.R24_RELEASE_WIDE_CHUNK_BYTES
    builder = R40Builder(source, deflate_reuse_min=0)
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
    retention = {
        "retained_canonical_count": builder.retained_canonical_count,
        "retained_canonical_bytes": builder.retained_canonical_bytes,
        "regenerated_canonical_count": builder.regenerated_canonical_count,
        "regenerated_canonical_stream_bytes": builder.regenerated_canonical_bytes,
        "retained_secondary_count": builder.retained_secondary_count,
        "retained_secondary_bytes": builder.retained_secondary_bytes,
        "regenerated_secondary_count": builder.regenerated_secondary_count,
        "regenerated_secondary_stream_bytes": builder.regenerated_secondary_bytes,
    }
    nomination = {
        "candidate_count_after_preparation": len(builder.cands),
        "family_predicate_examinations": builder.family_predicate_examinations,
        "specialized_candidate_count": builder.specialized_count,
        "specialized_raw_bytes": builder.specialized_raw_bytes,
    }
    return stats, retention, nomination


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member
    from experiments import entropygraph_v030_release_product as PRODUCT

    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stats, retention, nomination = _build_arm(arm, source, archive)
    wall = time.perf_counter() - started
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    verified = dict(PRODUCT.strong_verify(archive))
    tree = PRODUCT.treehash(source)
    if not verified.get("ok") or verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R40 {arm} strong verification/tree identity failed")

    virtual_members = R39._zip_members(source)
    locality_rows = []
    for member in virtual_members:
        raw, locality = _observed_product_member(PRODUCT, archive, member)
        decoded = locality.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError(f"R40 {arm} missing locality accounting: {member}")
        locality_rows.append(
            {
                "member": member,
                "member_bytes": len(raw),
                "decoded_context_bytes": int(decoded),
                "amplification": float(locality["max_member_read_amplification"]),
            }
        )

    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": tree,
        "build_wall_s": wall,
        "build_peak_rss_kib": rss,
        "strong_verify_ok": True,
        "locality_available": bool(locality_rows),
        "locality_within_8x": all(row["amplification"] <= MAX_LOCALITY for row in locality_rows),
        "max_virtual_member_amplification": max((row["amplification"] for row in locality_rows), default=None),
        "virtual_member_count": len(locality_rows),
        "deflate_retention": retention,
        "nomination": nomination,
        "build_stats": stats,
    }


def _fresh_worker(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-arm", arm,
            "--source", str(source),
            "--archive", str(archive),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in p.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"R40 worker emitted no JSON: {p.stderr!r}")
    return json.loads(lines[-1])


def _median(rows: list[dict]) -> dict:
    shas = {row["archive_sha256"] for row in rows}
    trees = {row["tree_sha256"] for row in rows}
    if len(shas) != 1 or len(trees) != 1:
        raise RuntimeError("R40 nondeterministic archive or source-tree identity")
    nominations = {json.dumps(row["nomination"], sort_keys=True) for row in rows}
    retentions = {json.dumps(row["deflate_retention"], sort_keys=True) for row in rows}
    if len(nominations) != 1 or len(retentions) != 1:
        raise RuntimeError("R40 nomination/retention accounting drifted across repetitions")
    max_amp = max(
        (float(row["max_virtual_member_amplification"]) for row in rows if row["max_virtual_member_amplification"] is not None),
        default=None,
    )
    return {
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in rows)),
        "archive_sha256": next(iter(shas)),
        "tree_sha256": next(iter(trees)),
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in rows)),
        "build_peak_rss_kib": int(statistics.median(row["build_peak_rss_kib"] for row in rows)),
        "strong_verify_ok": all(row["strong_verify_ok"] for row in rows),
        "locality_available": any(row["locality_available"] for row in rows),
        "locality_within_8x": all(row["locality_within_8x"] for row in rows),
        "max_virtual_member_amplification": max_amp,
        "nomination": json.loads(next(iter(nominations))),
        "deflate_retention": json.loads(next(iter(retentions))),
    }


def _annotate(release: dict, control: dict, candidate: dict) -> None:
    for row in (control, candidate):
        row["bytes_vs_release"] = row["archive_bytes"] - release["archive_bytes"]
        row["build_wall_delta_s_vs_release"] = row["build_wall_s"] - release["build_wall_s"]
        row["build_wall_delta_fraction_vs_release"] = (
            row["build_wall_delta_s_vs_release"] / release["build_wall_s"] if release["build_wall_s"] else None
        )
        row["material_runtime_regression_vs_release"] = _material_runtime_regression(
            release["build_wall_s"], row["build_wall_s"]
        )
        row["rss_regression_over_10pct_vs_release"] = row["build_peak_rss_kib"] > 1.10 * release["build_peak_rss_kib"]
    candidate["bytes_vs_dict12_control"] = candidate["archive_bytes"] - control["archive_bytes"]
    candidate["build_wall_delta_s_vs_dict12_control"] = candidate["build_wall_s"] - control["build_wall_s"]
    candidate["material_runtime_regression_vs_dict12_control"] = _material_runtime_regression(
        control["build_wall_s"], candidate["build_wall_s"]
    )
    inherited_saving = max(0, release["archive_bytes"] - control["archive_bytes"])
    retained_saving = max(0, release["archive_bytes"] - candidate["archive_bytes"])
    candidate["inherited_control_saving_bytes"] = inherited_saving
    candidate["retained_saving_bytes"] = retained_saving
    candidate["fraction_of_control_saving_retained"] = (
        retained_saving / inherited_saving if inherited_saving > 0 else None
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _ = RELEASE_LOCK.CORE.fingerprint(manifest)

    corpora = list(A._build_corpora(work_root / "corpus"))
    if len(corpora) != EXPECTED_PUBLIC_WORKLOADS:
        raise RuntimeError(f"R40 expected 15 public workloads, found {len(corpora)}")
    accepted_total = sum(int(expected["accepted_v029_bytes"]) for _suite, _source, expected in corpora)
    if accepted_total != EXPECTED_REPAIRED_V029_BYTES:
        raise RuntimeError(
            f"R40 accepted repaired-v0.29 aggregate drift: {accepted_total} != {EXPECTED_REPAIRED_V029_BYTES}"
        )

    result = {
        "schema": SCHEMA,
        "status": "hostile-review-only-no-product-or-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "release_fingerprint": fingerprint,
        "repetitions": REPETITIONS,
        "accepted_repaired_v029_bytes": EXPECTED_REPAIRED_V029_BYTES,
        "v030_absolute_hurdle_bytes": V030_ABSOLUTE_HURDLE_BYTES,
        "workloads": [],
        "carrying_cost": {
            "new_reader_grammar_states": 0,
            "new_native_reader_or_c_abi_states": 0,
            "new_platform_parser_copies_allowed": 0,
            "projected_python_encoder_policy_branches": 1,
            "mechanism_uses_existing_zstd_dictionary_metadata": True,
        },
    }

    substrate_failure = False
    for suite, source, expected in corpora:
        observed_tree = A.RC.treehash(source)
        expected_tree = str(expected["tree_sha256"])
        identity_ok = observed_tree == expected_tree
        substrate_failure = substrate_failure or not identity_ok
        arms = {}
        for arm in ARMS:
            reps = []
            for rep in range(1, REPETITIONS + 1):
                row = _fresh_worker(
                    arm,
                    source,
                    work_root / "archives" / suite / source.name / f"{arm}-{rep}.cmpct",
                )
                row["repetition"] = rep
                reps.append(row)
            arms[arm] = {"repetitions": reps, "median": _median(reps)}
        release = arms["release-all-exact"]["median"]
        control = arms["dict12-control"]["median"]
        candidate = arms["family-dict9"]["median"]
        _annotate(release, control, candidate)
        row_valid = identity_ok and all(
            arm["median"]["strong_verify_ok"] and arm["median"]["locality_within_8x"]
            for arm in arms.values()
        )
        substrate_failure = substrate_failure or not row_valid
        result["workloads"].append(
            {
                "suite": suite,
                "name": source.name,
                "logical_bytes": int(expected.get("logical_bytes", 0)),
                "accepted_tree_sha256": expected_tree,
                "observed_tree_sha256": observed_tree,
                "accepted_tree_match": identity_ok,
                "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
                "arms": arms,
                "valid": row_valid,
            }
        )

    rows = result["workloads"]
    activation_rows = [
        row for row in rows
        if row["arms"]["family-dict9"]["median"]["nomination"]["specialized_candidate_count"] > 0
    ]
    false_positive_rows = [
        row for row in activation_rows
        if row["arms"]["family-dict9"]["median"]["archive_bytes"] >= row["arms"]["release-all-exact"]["median"]["archive_bytes"]
    ]
    runtime_red_rows = [
        row for row in rows
        if row["arms"]["family-dict9"]["median"]["material_runtime_regression_vs_release"]
    ]
    rss_red_rows = [
        row for row in rows
        if row["arms"]["family-dict9"]["median"]["rss_regression_over_10pct_vs_release"]
    ]
    lost_control_win_rows = [
        row for row in rows
        if row["arms"]["dict12-control"]["median"]["archive_bytes"] < row["arms"]["release-all-exact"]["median"]["archive_bytes"]
        and row["arms"]["family-dict9"]["median"]["archive_bytes"] >= row["arms"]["release-all-exact"]["median"]["archive_bytes"]
    ]
    inc = next(
        row for row in rows
        if row["suite"] == "neutral_hostile_v1" and row["name"] == "06_incremental_backups"
    )
    inc_release = inc["arms"]["release-all-exact"]["median"]
    inc_candidate = inc["arms"]["family-dict9"]["median"]
    protected_survives = (
        inc_candidate["archive_bytes"] < inc_release["archive_bytes"]
        and not inc_candidate["material_runtime_regression_vs_release"]
        and not inc_candidate["rss_regression_over_10pct_vs_release"]
        and inc_candidate["locality_within_8x"]
    )

    total_logical = sum(int(row["logical_bytes"]) for row in rows)
    total_specialized_raw = sum(
        row["arms"]["family-dict9"]["median"]["nomination"]["specialized_raw_bytes"] for row in rows
    )
    total_examinations = sum(
        row["arms"]["family-dict9"]["median"]["nomination"]["family_predicate_examinations"] for row in rows
    )
    total_specialized_count = sum(
        row["arms"]["family-dict9"]["median"]["nomination"]["specialized_candidate_count"] for row in rows
    )
    positive_control_saving = sum(
        max(0, row["arms"]["release-all-exact"]["median"]["archive_bytes"] - row["arms"]["dict12-control"]["median"]["archive_bytes"])
        for row in rows
    )
    positive_candidate_saving = sum(
        max(0, row["arms"]["release-all-exact"]["median"]["archive_bytes"] - row["arms"]["family-dict9"]["median"]["archive_bytes"])
        for row in rows
    )
    aggregate_erosion = sum(
        row["arms"]["family-dict9"]["median"]["archive_bytes"] - row["arms"]["dict12-control"]["median"]["archive_bytes"]
        for row in rows
    )
    runtime_vs_dict12 = {"improves": 0, "ties_nonmaterial": 0, "worsens_material": 0}
    for row in rows:
        ctl = row["arms"]["dict12-control"]["median"]
        cand = row["arms"]["family-dict9"]["median"]
        if cand["material_runtime_regression_vs_dict12_control"]:
            runtime_vs_dict12["worsens_material"] += 1
        elif cand["build_wall_s"] < ctl["build_wall_s"]:
            runtime_vs_dict12["improves"] += 1
        else:
            runtime_vs_dict12["ties_nonmaterial"] += 1

    result["aggregate"] = {
        "activation_workloads": len(activation_rows),
        "activation_workload_keys": [f"{row['suite']}/{row['name']}" for row in activation_rows],
        "dict9_changes_complete_bytes_workloads": sum(
            row["arms"]["family-dict9"]["median"]["archive_bytes"] != row["arms"]["dict12-control"]["median"]["archive_bytes"]
            for row in rows
        ),
        "runtime_vs_dict12": runtime_vs_dict12,
        "material_runtime_regression_vs_release_workloads": [f"{row['suite']}/{row['name']}" for row in runtime_red_rows],
        "rss_regression_over_10pct_vs_release_workloads": [f"{row['suite']}/{row['name']}" for row in rss_red_rows],
        "lost_dict12_strict_win_workloads": [f"{row['suite']}/{row['name']}" for row in lost_control_win_rows],
        "false_positive_admission_workloads": [f"{row['suite']}/{row['name']}" for row in false_positive_rows],
        "specialized_candidate_count": total_specialized_count,
        "specialized_raw_bytes": total_specialized_raw,
        "logical_input_bytes": total_logical,
        "addressable_opportunity_mass_raw_fraction": total_specialized_raw / total_logical if total_logical else 0.0,
        "family_predicate_examinations": total_examinations,
        "global_nomination_density": total_specialized_count / total_examinations if total_examinations else 0.0,
        "positive_dict12_saving_bytes": positive_control_saving,
        "positive_dict9_saving_bytes": positive_candidate_saving,
        "aggregate_byte_erosion_vs_dict12": aggregate_erosion,
        "protected_incremental_backups_survives": protected_survives,
    }

    if substrate_failure:
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    elif not protected_survives:
        decision = "RETIRE_DICT9_PRODUCT_FAMILY"
    elif lost_control_win_rows:
        decision = "RETIRE_DICT9_PRODUCT_FAMILY"
    elif runtime_red_rows or rss_red_rows or false_positive_rows:
        decision = "REHABILITATE_GLOBAL_CARRYING_COST"
    elif len(activation_rows) < 2 and result["carrying_cost"]["projected_python_encoder_policy_branches"] > 0:
        decision = "REHABILITATE_GLOBAL_CARRYING_COST"
    else:
        decision = "PROMOTE_DICT9_NEXT_PRODUCT_PREREQUISITE"
    result["decision"] = decision
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--worker-arm", choices=ARMS)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--archive", type=Path)
    args = ap.parse_args()
    if args.worker_arm:
        if args.source is None or args.archive is None:
            ap.error("worker mode requires --source and --archive")
        print(json.dumps(_worker(args.worker_arm, args.source, args.archive), sort_keys=True))
        return
    if args.work_root is None or args.output is None:
        ap.error("parent mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
