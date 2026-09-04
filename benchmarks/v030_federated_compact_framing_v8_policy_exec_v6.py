from __future__ import annotations

"""Exact-byte feature-pruned executor for the generic C25EG08 office policy.

The full-frontier search proved a useful negative result: searching deeper rules did not
reduce the 15 high-effort packs.  Its selected policy only depends on ``raw_bytes``, yet
the v4 executor still computes *all* policy features for every final pack, including a
level-1 Zstd compression, entropy histogram, zero fraction and printable fraction, then
compresses selected packs again at their final high level.

This experiment removes only work that the selected generic policy provably does not
observe.  It derives the feature dependency set from the rules themselves.  A level-1
compression is performed only when ``level1_ratio`` is actually required by a rule or
when level 1 is the final selected payload.  Entropy/byte-class scans are likewise paid
only when referenced.  Final pack bytes, compression levels, physical framing,
integrity, recovery and locality are unchanged.

Timing receives zero credit unless the complete C25EG08 output is byte-for-byte and
SHA-256 identical to the ordinary serial implementation of the same content-agnostic
policy.  This is research/promotion evidence only; it cannot authorize selector,
native/Android or release promotion by itself.
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
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v5 as V5POL
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as DV4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

ROUNDS = V3.ROUNDS
MAX_WORKERS = 8


def _required_features(rules: list[dict]) -> frozenset[str]:
    return frozenset(str(rule["feature"]) for rule in rules)


def _feature_row(index: int, raw: bytes, required: frozenset[str]) -> tuple[dict, bytes | None]:
    """Compute exactly and only policy-observable features."""
    n = max(1, len(raw))
    row: dict = {"index": int(index), "raw_bytes": int(len(raw))}
    level1: bytes | None = None

    if "level1_ratio" in required:
        level1 = V25.zc(raw, 1)
        row["level1_ratio"] = float(len(level1) / n)
    if "entropy_bits_per_byte" in required:
        counts = Counter(raw)
        row["entropy_bits_per_byte"] = (
            0.0 if not raw else -sum((count / n) * math.log2(count / n) for count in counts.values())
        )
    if "zero_fraction" in required:
        row["zero_fraction"] = float(raw.count(0) / n)
    if "printable_fraction" in required:
        printable = sum(1 for value in raw if value in (9, 10, 13) or 32 <= value <= 126)
        row["printable_fraction"] = float(printable / n)
    return row, level1


def _level_for(row: dict, rules: list[dict]) -> int:
    level = 1
    for rule in rules:
        if V3._matches(row, rule):
            level = max(level, int(rule["level"]))
    return level


def _emit_pruned(raw_eg07: bytes, output: Path, rules: list[dict]) -> dict:
    meta_comp, _meta_raw, meta_digest, raws = DV4._raw_eg07_parts(raw_eg07)
    required = _required_features(rules)
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1, len(raws)))

    def encode(item: tuple[int, bytes]):
        index, raw = item
        feature, cached_level1 = _feature_row(index, raw, required)
        level = _level_for(feature, rules)
        if level == 1:
            compressed = cached_level1 if cached_level1 is not None else V25.zc(raw, 1)
        else:
            compressed = V25.zc(raw, level)
        if len(compressed) + 8 < len(raw):
            codec, payload = 1, compressed
        else:
            codec, payload = 0, raw
        return index, feature, level, codec, raw, payload

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-eg08-pruned") as pool:
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
        "compression_s": float(compression_s),
        "publication_s": float(publication_s),
        "required_features": sorted(required),
        "level1_ratio_compressions_required": "level1_ratio" in required,
        "selected_high_effort_packs": sum(1 for row in rows if int(row[2]) != 1),
        "selected_levels": [int(row[2]) for row in rows],
    }


def _candidate_once(stage: Path, root: Path, rules: list[dict], reference: bytes, vector: tuple[int, ...]) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = DV5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    output = root / "policy-v6.c25eg08"
    emitted = _emit_pruned(raw_eg07, output, rules)
    verified = EG08.strong_verify(output, expected_tree=EG07._treehash(stage))
    locality = EG08.locality_report(output)
    elapsed = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("feature-pruned EG08 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("feature-pruned EG08 policy exceeded frozen locality/decode limits")
    raw = output.read_bytes()
    if raw != reference:
        raise RuntimeError("feature pruning changed EG08 archive bytes")
    selected = tuple(int(level) for level in emitted["selected_levels"])
    if selected != vector:
        raise RuntimeError("feature pruning changed selected compression levels")
    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_create_s": float(elapsed),
        "graph_s": float(graph_s),
        "parallel_compression_s": float(emitted["compression_s"]),
        "publication_s": float(emitted["publication_s"]),
        "workers": int(emitted["workers"]),
        "required_features": list(emitted["required_features"]),
        "level1_ratio_compressions_required": bool(emitted["level1_ratio_compressions_required"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": list(selected),
        "exact_bytes_vs_serial_reference": True,
        "locality": locality,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-policy-v6-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")
        raw_eg07, _ = DV5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = DV4._raw_eg07_parts(raw_eg07)
        features = V3._pack_features(raws)
        payload_table = V3._payload_table(raws)
        size_ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )
        rules, vector, projected_bytes, search = V5POL._search_full_frontier(
            features, meta_comp, payload_table, size_ceiling
        )
        if rules is None or vector is None or projected_bytes is None:
            raise RuntimeError("full-frontier policy unexpectedly lost the frozen office size win")

        reference_path = root / "serial-reference.c25eg08"
        serial = V1._emit(raw_eg07, reference_path, V3._selection_dict(vector))
        reference = reference_path.read_bytes()
        if int(serial["archive_bytes"]) != int(projected_bytes):
            raise RuntimeError("serial reference disagrees with exact projected bytes")

        samples: list[float] = []
        compression_samples: list[float] = []
        shas: set[str] = set()
        last = None
        for round_index in range(ROUNDS):
            measured = _candidate_once(stage, root / f"measure-{round_index}", rules, reference, vector)
            samples.append(float(measured["verified_create_s"]))
            compression_samples.append(float(measured["parallel_compression_s"]))
            shas.add(str(measured["archive_sha256"]))
            last = measured
        if len(shas) != 1:
            raise RuntimeError("feature-pruned EG08 output is nondeterministic")
        assert last is not None
        candidate_median = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": len(reference) < int(accepted_v029),
            "beats_zip_size": len(reference) < int(comparators["zip"]["archive_bytes"]),
            "beats_zstd19_size": len(reference) < int(comparators["zstd19"]["archive_bytes"]),
            "verified_create_beats_zip": candidate_median < float(comparators["zip"]["median_create_s"]),
            "verified_create_beats_zstd19": candidate_median < float(comparators["zstd19"]["median_create_s"]),
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_identity_not_policy_input": True,
            "exact_serial_archive_identity": bool(last["exact_bytes_vs_serial_reference"]),
            "same_selected_level_vector": tuple(last["selected_levels"]) == tuple(vector),
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-policy-exec-v6",
        "candidate": "C25EG08",
        "accepted_v029_bytes": int(accepted_v029),
        "selected_policy": {"rules": rules, "overlap_resolution": "max_level"},
        "search": search,
        "execution_change": {
            "type": "dependency-pruned-policy-feature-evaluation",
            "required_features": list(last["required_features"]),
            "unused_policy_features_not_evaluated": True,
            "level1_ratio_compressions_required": bool(last["level1_ratio_compressions_required"]),
            "final_high_effort_pack_compressed_once": True,
            "archive_identity_required": True,
        },
        "measured_candidate": {
            "archive_bytes": len(reference),
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": float(candidate_median),
            "raw_verified_create_s": samples,
            "median_parallel_compression_s": float(statistics.median(compression_samples)),
            "workers": int(last["workers"]),
            "graph_s": float(last["graph_s"]),
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
            "Research-only exact-byte execution optimization. It removes only feature/precompression work that the "
            "selected content-agnostic policy does not observe. All archive bytes, selected levels, verification, "
            "recovery and locality semantics remain unchanged. Ordinary all-15, native/Android and strict release "
            "authority remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v6-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v6.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": result["selected_policy"],
        "execution_change": result["execution_change"],
        "measured_candidate": result["measured_candidate"],
        "strict": result["strict"],
    }, indent=2), flush=True)
    if not result["strict"]["passed"]:
        raise SystemExit("feature-pruned C25EG08 executor did not satisfy the four-way office contract")


if __name__ == "__main__":
    main()
