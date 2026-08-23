from __future__ import annotations

"""Parallel exact-byte execution proof for the identity-free C25EG08 office policy.

The v3 distillation found a genuinely content-agnostic policy that clears every frozen office size floor:
``raw_bytes >= 64 KiB -> Zstd-19``.  Its measured candidate nevertheless failed the creation contract because
feature evaluation and fifteen high-effort final-pack compressions were executed serially.

This v4 proof changes *only scheduling*.  It re-runs the same bounded v3 policy search using the same permitted
features, then applies the selected policy independently to final physical packs in a bounded thread pool.  Each
worker pays the level-1 compression needed to derive ``level1_ratio`` and, when selected, the high-effort final
compression.  The final C25EG08 archive receives timing credit only when it is byte-for-byte and SHA-256 identical
to the ordinary serial implementation of the exact same generic policy.

No pack hash, path, filename, workload label or benchmark name may influence the compression level.  Graph/search
behavior, archive grammar, integrity, recovery, locality and the immutable v0.29/ZIP/Zstd thresholds are unchanged.
A green result remains promotion-incomplete until all-15/adversarial generalization, selector ownership,
native/Android parity and strict release authority pass on the same exact candidate.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as V5
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

ROUNDS = V3.ROUNDS
MAX_WORKERS = 8


def _feature_and_level1(index: int, raw: bytes) -> tuple[dict, bytes]:
    """Compute exactly the policy-visible feature row plus its already-paid level-1 payload."""
    n = max(1, len(raw))
    level1 = V25.zc(raw, 1)
    counts = Counter(raw)
    entropy = 0.0 if not raw else -sum((count / n) * math.log2(count / n) for count in counts.values())
    printable = sum(1 for value in raw if value in (9, 10, 13) or 32 <= value <= 126)
    return (
        {
            "index": int(index),
            "raw_bytes": int(len(raw)),
            "level1_ratio": float(len(level1) / n),
            "entropy_bits_per_byte": float(entropy),
            "zero_fraction": float(raw.count(0) / n),
            "printable_fraction": float(printable / n),
        },
        level1,
    )


def _level_for(row: dict, rules: list[dict]) -> int:
    level = 1
    for rule in rules:
        if V3._matches(row, rule):
            level = max(level, int(rule["level"]))
    return level


def _parallel_emit(raw_eg07: bytes, output: Path, rules: list[dict]) -> dict:
    """Evaluate the generic policy and compress independent final packs concurrently."""
    meta_comp, _meta_raw, meta_digest, raws = V4._raw_eg07_parts(raw_eg07)
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1, len(raws)))

    def encode(item: tuple[int, bytes]):
        index, raw = item
        feature, level1 = _feature_and_level1(index, raw)
        level = _level_for(feature, rules)
        compressed = level1 if level == 1 else V25.zc(raw, level)
        if len(compressed) + 8 < len(raw):
            codec, payload = 1, compressed
        else:
            codec, payload = 0, raw
        return index, feature, level, codec, raw, payload

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-eg08-policy") as pool:
        rows = list(pool.map(encode, enumerate(raws)))
    rows.sort(key=lambda item: item[0])
    compression_s = time.perf_counter() - started

    started = time.perf_counter()
    parts = [EG08.HDR.pack(EG08.MAGIC, len(meta_comp), meta_digest), meta_comp]
    for _index, _feature, _level, codec, raw, payload in rows:
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
    publication_s = time.perf_counter() - started

    return {
        "archive_bytes": len(blob),
        "workers": workers,
        "compression_s": compression_s,
        "publication_s": publication_s,
        "selected_high_effort_packs": sum(1 for row in rows if int(row[2]) != 1),
        "selected_levels": [int(row[2]) for row in rows],
        "policy_feature_rows": [row[1] for row in rows],
    }


def _parallel_candidate_once(
    stage: Path,
    root: Path,
    rules: list[dict],
    reference_bytes: bytes,
    expected_vector: tuple[int, ...],
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = V5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    output = root / "policy-v4.c25eg08"
    emitted = _parallel_emit(raw_eg07, output, rules)
    verified = EG08.strong_verify(output, expected_tree=EG07._treehash(stage))
    locality = EG08.locality_report(output)
    elapsed = time.perf_counter() - started

    if not verified.get("ok"):
        raise RuntimeError("parallel identity-free EG08 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("parallel identity-free EG08 policy exceeded frozen locality/decode limits")
    raw = output.read_bytes()
    if raw != reference_bytes:
        raise RuntimeError("parallel identity-free EG08 policy changed bytes versus serial reference")
    vector = tuple(int(level) for level in emitted["selected_levels"])
    if vector != expected_vector:
        raise RuntimeError("parallel identity-free EG08 policy changed the selected level vector")

    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_create_s": float(elapsed),
        "graph_s": float(graph_s),
        "parallel_compression_s": float(emitted["compression_s"]),
        "publication_s": float(emitted["publication_s"]),
        "workers": int(emitted["workers"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": list(vector),
        "exact_bytes_vs_serial_reference": True,
        "locality": locality,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-policy-v4-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")

        raw_eg07, _ = V5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
        features = V3._pack_features(raws)
        payload_table = V3._payload_table(raws)
        size_ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )
        rules, projected_vector, projected_bytes, search = V3._search(
            features,
            meta_comp,
            payload_table,
            size_ceiling,
        )
        if rules is None or projected_vector is None or projected_bytes is None:
            raise RuntimeError("identity-free v3 policy search no longer clears the frozen office size floors")

        # Serial output is an untimed byte oracle for exactly the same generic policy.  The parallel path gets no
        # credit unless every final byte is identical to this ordinary implementation.
        reference = root / "serial-reference.c25eg08"
        serial = V1._emit(raw_eg07, reference, V3._selection_dict(projected_vector))
        reference_bytes = reference.read_bytes()
        if int(serial["archive_bytes"]) != int(projected_bytes):
            raise RuntimeError("serial generic-policy bytes disagree with exact size projection")

        samples: list[float] = []
        sizes: set[int] = set()
        shas: set[str] = set()
        last = None
        for round_index in range(ROUNDS):
            measured = _parallel_candidate_once(
                stage,
                root / f"measure-{round_index}",
                rules,
                reference_bytes,
                projected_vector,
            )
            samples.append(float(measured["verified_create_s"]))
            sizes.add(int(measured["archive_bytes"]))
            shas.add(str(measured["archive_sha256"]))
            last = measured
        if len(sizes) != 1 or len(shas) != 1:
            raise RuntimeError("parallel identity-free EG08 policy is nondeterministic")
        assert last is not None

        candidate_bytes = next(iter(sizes))
        candidate_median = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": candidate_bytes < int(accepted_v029),
            "beats_zip_size": candidate_bytes < int(comparators["zip"]["archive_bytes"]),
            "beats_zstd19_size": candidate_bytes < int(comparators["zstd19"]["archive_bytes"]),
            "verified_create_beats_zip": candidate_median < float(comparators["zip"]["median_create_s"]),
            "verified_create_beats_zstd19": candidate_median < float(comparators["zstd19"]["median_create_s"]),
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_identity_not_policy_input": True,
            "exact_size_projection": candidate_bytes == int(projected_bytes),
            "exact_serial_parallel_archive_identity": bool(last["exact_bytes_vs_serial_reference"]),
            "same_selected_level_vector": tuple(last["selected_levels"]) == tuple(projected_vector),
            "rule_count_within_bound": len(rules) <= V3.MAX_RULES,
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-policy-distillation-v4",
        "candidate": "C25EG08",
        "accepted_v029_bytes": int(accepted_v029),
        "policy_inputs": [
            "raw_bytes",
            "level1_ratio",
            "entropy_bits_per_byte",
            "zero_fraction",
            "printable_fraction",
        ],
        "forbidden_policy_inputs": ["sha256", "path", "filename", "workload_label", "benchmark_name"],
        "predecessor_v3_size_green_speed_red": True,
        "selected_policy": {"rules": rules, "overlap_resolution": "max_level"},
        "search_family": {"max_rules": V3.MAX_RULES, **search},
        "schedule": {
            "type": "bounded-parallel-per-pack-policy-and-final-compression",
            "max_workers": MAX_WORKERS,
            "level1_feature_compression_counted": True,
            "high_effort_compression_counted": True,
            "serial_reference_untimed": True,
            "archive_identity_required": True,
        },
        "measured_candidate": {
            "archive_bytes": int(candidate_bytes),
            "projected_archive_bytes": int(projected_bytes),
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": float(candidate_median),
            "raw_verified_create_s": samples,
            "workers": int(last["workers"]),
            "graph_s": float(last["graph_s"]),
            "parallel_compression_s": float(last["parallel_compression_s"]),
            "publication_s": float(last["publication_s"]),
            "selected_high_effort_packs": int(last["selected_high_effort_packs"]),
            "selected_levels": list(last["selected_levels"]),
            "max_member_read_amplification": float(last["locality"]["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(last["locality"]["max_decode_unit_bytes"]),
            "exact_bytes_vs_serial_reference": True,
        },
        "comparators": comparators,
        "strict": strict,
        "claim_boundary": (
            "Research-only exact-byte parallel execution proof for the identity-free EG08 policy. Compression-level "
            "decisions use only generic pack statistics; frozen identity is forbidden. Feature-level1 work and "
            "selected high-effort compression are both charged inside the candidate wall-clock and executed in a "
            "bounded pool. Timing receives credit only after exact archive identity with the ordinary serial policy, "
            "mandatory strong verification and locality audit. All-15/adversarial generalization, selector, native/" 
            "Android and strict release authority remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v4-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v4.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_policy": result["selected_policy"],
                "schedule": result["schedule"],
                "measured_candidate": result["measured_candidate"],
                "comparators": result["comparators"],
                "strict": result["strict"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["strict"]["passed"]:
        raise SystemExit("parallel identity-free C25EG08 policy did not satisfy the four-way office contract")


if __name__ == "__main__":
    main()
