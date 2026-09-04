from __future__ import annotations

"""Frozen R39 selected-dictionary effort rehabilitation Builder.

Normative preregistration:
``docs/v030-rnd/R39_SELECTED_DICTIONARY_EFFORT_REHABILITATION_PREREG.md``.
Diagnostic only; no product or release credit.
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
from benchmarks import v030_r32_regenerable_deflate_output_dead_zstd_elision as R32
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r39-selected-dictionary-effort-rehabilitation-v1"
ARMS = ("release-all-exact", "dict12-control", "family-dict9")
REPETITIONS = 5
MAX_LOCALITY = 8.0
SPECIALIZED_RAW_MAX = 65_536
EXPECTED_SPECIALIZED_COUNT = 180
EXPECTED_SPECIALIZED_RAW_BYTES = 980_226


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
    return [
        p.relative_to(root).as_posix()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in {".zip", ".whl"}
    ]


def _build_arm(arm: str, source: Path, archive: Path) -> tuple[dict, dict, dict]:
    import cmpct.builder as CB
    from experiments import entropygraph_v030_release_product as PRODUCT

    class R39Builder(CB.Builder):
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
            # Preserve R32 output-dead ordinary-Zstd elision for the exact-deflate-backed
            # regenerable class. R39 changes only selected dictionary effort for the
            # content-derived text family proven by R38.
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
    builder = R39Builder(source, deflate_reuse_min=0)
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
    specialized = {"candidate_count": builder.specialized_count, "raw_bytes": builder.specialized_raw_bytes}
    return stats, retention, specialized


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from benchmarks.v030_perf_worker_canonical import _observed_product_member
    from experiments import entropygraph_v030_release_product as PRODUCT
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stats, retention, specialized = _build_arm(arm, source, archive)
    wall = time.perf_counter() - started
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok"):
        raise RuntimeError(f"R39 {arm} strong verification failed: {verified!r}")
    tree = PRODUCT.treehash(source)
    if verified.get("tree_sha256") != tree:
        raise RuntimeError(f"R39 {arm} tree mismatch")
    members = []
    for member in _zip_members(source):
        raw, locality = _observed_product_member(PRODUCT, archive, member)
        decoded = locality.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError(f"R39 {arm} missing locality accounting: {member}")
        amp = float(locality["max_member_read_amplification"])
        members.append({"member": member, "member_bytes": len(raw), "decoded_context_bytes": int(decoded), "amplification": amp})
    if not members:
        raise RuntimeError(f"R39 {arm} target contains no virtual member")
    return {
        "arm": arm,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256_file(archive),
        "tree_sha256": tree,
        "build_wall_s": wall,
        "build_peak_rss_kib": rss,
        "strong_verify_ok": True,
        "locality_within_8x": all(row["amplification"] <= MAX_LOCALITY for row in members),
        "max_virtual_member_amplification": max(row["amplification"] for row in members),
        "deflate_retention": retention,
        "specialized": specialized,
        "build_stats": stats,
    }


def _fresh_worker(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker-arm", arm, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in p.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"R39 worker emitted no JSON: {p.stderr!r}")
    return json.loads(lines[-1])


def _median(rows: list[dict]) -> dict:
    shas = {row["archive_sha256"] for row in rows}
    if len(shas) != 1:
        raise RuntimeError(f"R39 nondeterministic archive outputs: {sorted(shas)}")
    return {
        "archive_bytes": int(statistics.median(row["archive_bytes"] for row in rows)),
        "archive_sha256": next(iter(shas)),
        "build_wall_s": float(statistics.median(row["build_wall_s"] for row in rows)),
        "build_peak_rss_kib": int(statistics.median(row["build_peak_rss_kib"] for row in rows)),
        "strong_verify_ok": all(row["strong_verify_ok"] for row in rows),
        "locality_within_8x": all(row["locality_within_8x"] for row in rows),
        "max_virtual_member_amplification": max(row["max_virtual_member_amplification"] for row in rows),
        "specialized_candidate_count": int(statistics.median(row["specialized"]["candidate_count"] for row in rows)),
        "specialized_raw_bytes": int(statistics.median(row["specialized"]["raw_bytes"] for row in rows)),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _ = RELEASE_LOCK.CORE.fingerprint(manifest)
    full = None; expected_tree = None; observed_tree = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == R32.TARGET_SUITE and source.name == R32.TARGET_NAME:
            full = source; expected_tree = str(expected["tree_sha256"]); observed_tree = A.RC.treehash(source); break
    if full is None or observed_tree != expected_tree:
        raise RuntimeError("R39 frozen generator identity failure")
    nested_file = full / R32.NESTED_MEMBER
    nested_sha = _sha256_file(nested_file)
    nested = work_root / "nested-only"; nested.mkdir(parents=True)
    shutil.copyfile(nested_file, nested / R32.NESTED_MEMBER)
    if _sha256_file(nested / R32.NESTED_MEMBER) != nested_sha:
        raise RuntimeError("R39 nested projection identity failure")

    result = {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "evidence_head": os.environ.get("CMPCT_EVIDENCE_HEAD", ""),
        "release_fingerprint": fingerprint,
        "repetitions": REPETITIONS,
        "targets": {},
    }
    substrate_failure = False
    any_runtime_red = False; any_byte_lost = False
    for target_name, source in {"full-backups": full, "nested-only": nested}.items():
        arms = {}
        for arm in ARMS:
            reps = []
            for rep in range(1, REPETITIONS + 1):
                row = _fresh_worker(arm, source, work_root / "archives" / target_name / f"{arm}-{rep}.cmpct")
                row["repetition"] = rep; reps.append(row)
            arms[arm] = {"repetitions": reps, "median": _median(reps)}
        release = arms["release-all-exact"]["median"]
        control = arms["dict12-control"]["median"]
        candidate = arms["family-dict9"]["median"]
        for x in (control, candidate):
            x["bytes_vs_release"] = x["archive_bytes"] - release["archive_bytes"]
            x["build_wall_delta_s_vs_release"] = x["build_wall_s"] - release["build_wall_s"]
            x["build_wall_delta_fraction_vs_release"] = x["build_wall_delta_s_vs_release"] / release["build_wall_s"] if release["build_wall_s"] else None
            x["material_runtime_regression_vs_release"] = _material_runtime_regression(release["build_wall_s"], x["build_wall_s"])
            x["rss_regression_over_10pct_vs_release"] = x["build_peak_rss_kib"] > 1.10 * release["build_peak_rss_kib"]
        candidate["bytes_vs_dict12_control"] = candidate["archive_bytes"] - control["archive_bytes"]
        inherited_saving = release["archive_bytes"] - control["archive_bytes"]
        retained_saving = release["archive_bytes"] - candidate["archive_bytes"]
        candidate["inherited_control_saving_bytes"] = inherited_saving
        candidate["retained_saving_bytes"] = retained_saving
        candidate["fraction_of_control_saving_retained"] = retained_saving / inherited_saving if inherited_saving > 0 else None

        valid = all(x["strong_verify_ok"] and x["locality_within_8x"] for x in (release, control, candidate))
        valid = valid and control["archive_bytes"] < release["archive_bytes"]
        valid = valid and control["specialized_candidate_count"] == EXPECTED_SPECIALIZED_COUNT and control["specialized_raw_bytes"] == EXPECTED_SPECIALIZED_RAW_BYTES
        valid = valid and candidate["specialized_candidate_count"] == EXPECTED_SPECIALIZED_COUNT and candidate["specialized_raw_bytes"] == EXPECTED_SPECIALIZED_RAW_BYTES
        substrate_failure = substrate_failure or not valid
        any_runtime_red = any_runtime_red or candidate["material_runtime_regression_vs_release"]
        any_byte_lost = any_byte_lost or candidate["archive_bytes"] >= release["archive_bytes"]
        result["targets"][target_name] = {"arms": arms, "valid": valid}

    if substrate_failure:
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    elif not any_runtime_red and not any_byte_lost:
        # RSS is part of promotion rather than the byte/runtime taxonomy.
        rss_ok = all(not t["arms"]["family-dict9"]["median"]["rss_regression_over_10pct_vs_release"] for t in result["targets"].values())
        decision = "PROMOTE_DICT9_TO_HOSTILE_REVIEWER" if rss_ok else "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    elif any_runtime_red and not any_byte_lost:
        decision = "DICT9_BYTE_WIN_RUNTIME_DEBT_REMAINS"
    elif not any_runtime_red and any_byte_lost:
        decision = "DICT9_RUNTIME_RECOVERED_BYTE_WIN_LOST"
    else:
        decision = "DICT9_BOTH_DEBTS"
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
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
