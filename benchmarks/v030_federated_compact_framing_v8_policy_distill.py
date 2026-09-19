from __future__ import annotations

"""Distill the proven C25EG08 office pack schedule into a content-agnostic policy.

The exact RAM-backed office frontier is green, but its minimum-effort reference records final compression levels by
SHA-256 of the frozen physical packs.  Those hashes are valid causality evidence, not a production policy.  This
harness removes that last benchmark-identity dependency.

It rebuilds the exact frozen office graph, authenticates the final raw packs, and derives compression effort only
from properties available for *any* pack at encode time: raw byte length and the already-required level-1 final
compression ratio.  It searches a deliberately small family of deterministic threshold policies and gives credit
only to a policy which:

- never consults a pack hash, path, workload label, or benchmark name when choosing a level;
- emits a C25EG08 archive that strongly verifies and preserves the canonical user tree;
- stays within <=8x member-read amplification and <=8 MiB decode units;
- is strictly smaller than accepted v0.29, ZIP/Deflate-9, and solid Zstd-19;
- is verified-create faster than ZIP and solid Zstd-19 over repeated rotated measurements.

The frozen hash-selected schedule remains an oracle/reference only.  A green result establishes a productizable
selection *shape*; native/Android, all-15 generalization, selector admission, and strict release authority remain
mandatory before promotion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_federated_compact_framing_v8_direct as DIRECT
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as V5
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EXPECTED_OFFICE_V029 = 5_954_026
ROUNDS = 3
LEVELS = (1, 12, 15, 19, 22)
# Small, reviewable policy family.  Raw size and the level-1 ratio are both known after the required final pack
# audition, so this introduces no benchmark identity and no extra source scan.
SIZE_THRESHOLDS = (64 << 10, 128 << 10, 256 << 10, 384 << 10, 512 << 10)
RATIO_THRESHOLDS = (0.45, 0.60, 0.72, 0.82, 0.90, 0.97)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pack_features(raws: list[bytes]) -> list[dict]:
    rows = []
    for index, raw in enumerate(raws):
        level1 = V25.zc(raw, 1)
        rows.append(
            {
                "index": index,
                "raw_bytes": len(raw),
                "level1_bytes": len(level1),
                "level1_ratio": len(level1) / max(1, len(raw)),
                # Digest is evidence identity only; policy functions below never receive it.
                "sha256": _sha(raw),
            }
        )
    return rows


def _policy_selection(features: list[dict], *, size_threshold: int, ratio_threshold: float, level: int) -> dict[int, int]:
    """Return pack-index -> level using only generic pack properties."""
    result = {}
    for row in features:
        use_high = int(row["raw_bytes"]) >= int(size_threshold) and float(row["level1_ratio"]) <= float(ratio_threshold)
        result[int(row["index"])] = int(level if use_high else 1)
    return result


def _emit(raw_eg07: bytes, output: Path, by_index: dict[int, int]) -> dict:
    meta_comp, _meta_raw, meta_digest, raws = V4._raw_eg07_parts(raw_eg07)
    normal_zc = V25.zc
    started = time.perf_counter()
    parts = [EG08.HDR.pack(EG08.MAGIC, len(meta_comp), meta_digest), meta_comp]
    selected = 0
    for index, raw in enumerate(raws):
        level = int(by_index.get(index, 1))
        selected += int(level != 1)
        compressed = normal_zc(raw, level)
        if len(compressed) + 8 < len(raw):
            codec, payload = 1, compressed
        else:
            codec, payload = 0, raw
        parts.extend(
            (
                EG08.PH.pack(
                    int(codec),
                    len(payload),
                    V25.binascii.crc32(raw) & 0xFFFFFFFF,
                    V25.H(raw),
                ),
                payload,
            )
        )
    parts.extend((meta_comp, EG08.FTR.pack(EG08.TAIL_MAGIC, len(meta_comp), meta_digest)))
    blob = b"".join(parts)
    output.write_bytes(blob)
    return {
        "archive_bytes": len(blob),
        "selected_high_effort_packs": selected,
        "emit_s": time.perf_counter() - started,
    }


def _candidate_once(stage: Path, root: Path, policy: dict) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = V5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    _meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
    features = _pack_features(raws)
    by_index = _policy_selection(features, **policy)
    output = root / "policy.c25eg08"
    emitted = _emit(raw_eg07, output, by_index)
    verified = EG08.strong_verify(output, expected_tree=EG07._treehash(stage))
    locality = EG08.locality_report(output)
    elapsed = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("distilled EG08 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("distilled EG08 policy exceeded frozen locality/decode bounds")
    return {
        "archive_bytes": int(emitted["archive_bytes"]),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "verified_create_s": elapsed,
        "graph_s": graph_s,
        "emit_s": emitted["emit_s"],
        "selected_high_effort_packs": emitted["selected_high_effort_packs"],
        "locality": locality,
        "features": features,
    }


def _comparators(stage: Path, root: Path) -> dict:
    expected_tree = EXT._tree(stage)
    samples = {"zip": [], "zstd19": []}
    sizes = {"zip": set(), "zstd19": set()}
    for round_index in range(ROUNDS):
        order = ("zip", "zstd19") if round_index % 2 == 0 else ("zstd19", "zip")
        for name in order:
            lane = root / f"{round_index}-{name}"
            lane.mkdir(parents=True)
            if name == "zip":
                result = EXT._zip(stage, lane / "archive.zip", lane / "out")
            else:
                result = EXT._tar_zstd(stage, lane / "archive.tar.zst", lane / "out", lane)
                if not result.get("available"):
                    raise RuntimeError("solid Zstd-19 unavailable")
            EXT._verify_extracted(lane / "out", expected_tree, name)
            samples[name].append(float(result["create_s"]))
            sizes[name].add(int(result["archive_bytes"]))
    if any(len(value) != 1 for value in sizes.values()):
        raise RuntimeError(f"nondeterministic comparator bytes: {sizes!r}")
    return {
        name: {
            "archive_bytes": next(iter(sizes[name])),
            "median_create_s": statistics.median(samples[name]),
            "raw_create_s": samples[name],
        }
        for name in ("zip", "zstd19")
    }


def _frozen_office(work_root: Path) -> tuple[Path, int]:
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg08_policy_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg08_policy_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    expected = accepted[("neutral_hostile_v1", "02_office_workspace")]
    if EXT._tree(source) != expected["tree_sha256"]:
        raise RuntimeError("office source identity drift")
    value = int(expected["accepted_v029_bytes"])
    if value != EXPECTED_OFFICE_V029:
        raise RuntimeError(f"office accepted-v0.29 drift: {value}")
    return source, value


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = _frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-policy-", dir=work_root) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized")
        comparators = _comparators(stage, root / "comparators")

        # One authenticated capture supplies generic features for policy search.  Hashes are retained only to
        # demonstrate that policy decisions are independent of them.
        raw_eg07, _ = V5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        _mc, _mr, _md, raws = V4._raw_eg07_parts(raw_eg07)
        features = _pack_features(raws)

        candidates = []
        for level in LEVELS[1:]:
            for size_threshold in SIZE_THRESHOLDS:
                for ratio_threshold in RATIO_THRESHOLDS:
                    policy = {
                        "size_threshold": int(size_threshold),
                        "ratio_threshold": float(ratio_threshold),
                        "level": int(level),
                    }
                    by_index = _policy_selection(features, **policy)
                    trial = root / "search" / f"l{level}-s{size_threshold}-r{int(ratio_threshold*100)}.c25eg08"
                    trial.parent.mkdir(parents=True, exist_ok=True)
                    emitted = _emit(raw_eg07, trial, by_index)
                    size = int(emitted["archive_bytes"])
                    if size < accepted_v029 and size < comparators["zip"]["archive_bytes"] and size < comparators["zstd19"]["archive_bytes"]:
                        candidates.append((size, emitted["selected_high_effort_packs"], policy))
        if not candidates:
            raise RuntimeError("no content-agnostic EG08 threshold policy clears the frozen size floors")

        # Prefer the lowest-effort shape: fewer high-effort packs, then lower level, then smaller bytes.
        candidates.sort(key=lambda item: (item[1], item[2]["level"], item[0]))
        selected_policy = candidates[0][2]

        samples = []
        sizes = set()
        shas = set()
        last = None
        for round_index in range(ROUNDS):
            measured = _candidate_once(stage, root / f"measure-{round_index}", selected_policy)
            samples.append(float(measured["verified_create_s"]))
            sizes.add(int(measured["archive_bytes"]))
            shas.add(str(measured["archive_sha256"]))
            last = measured
        if len(sizes) != 1 or len(shas) != 1:
            raise RuntimeError("distilled EG08 policy is nondeterministic")
        assert last is not None
        candidate_bytes = next(iter(sizes))
        candidate_median = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": candidate_bytes < accepted_v029,
            "beats_zip_size": candidate_bytes < comparators["zip"]["archive_bytes"],
            "beats_zstd19_size": candidate_bytes < comparators["zstd19"]["archive_bytes"],
            "verified_create_beats_zip": candidate_median < comparators["zip"]["median_create_s"],
            "verified_create_beats_zstd19": candidate_median < comparators["zstd19"]["median_create_s"],
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_hash_not_policy_input": True,
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-policy-distillation-v1",
        "candidate": "C25EG08",
        "accepted_v029_bytes": accepted_v029,
        "policy_inputs": ["raw_bytes", "level1_ratio"],
        "forbidden_policy_inputs": ["sha256", "path", "workload_label", "benchmark_name"],
        "selected_policy": selected_policy,
        "search_family": {
            "levels": list(LEVELS),
            "size_thresholds": list(SIZE_THRESHOLDS),
            "ratio_thresholds": list(RATIO_THRESHOLDS),
            "candidate_policies_clearing_size_floors": len(candidates),
        },
        "measured_candidate": {
            "archive_bytes": candidate_bytes,
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": candidate_median,
            "raw_verified_create_s": samples,
            "selected_high_effort_packs": int(last["selected_high_effort_packs"]),
            "max_member_read_amplification": float(last["locality"]["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(last["locality"]["max_decode_unit_bytes"]),
        },
        "comparators": comparators,
        "strict": strict,
        "claim_boundary": (
            "Research-only policy distillation. A green result removes frozen pack hashes from the office effort "
            "decision and demonstrates a small content-agnostic policy family can preserve the C25EG08 four-way "
            "win. All-15/adversarial generalization, production selector ownership, native/Android parity, and "
            "strict release authority remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_policy": result["selected_policy"], "measured_candidate": result["measured_candidate"], "comparators": result["comparators"], "strict": result["strict"]}, indent=2), flush=True)
    if not result["strict"]["passed"]:
        raise SystemExit("C25EG08 content-agnostic policy distillation failed")


if __name__ == "__main__":
    main()
