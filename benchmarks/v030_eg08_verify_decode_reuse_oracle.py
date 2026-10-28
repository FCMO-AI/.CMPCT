from __future__ import annotations

"""Exact-semantics EG08 decoded-pack reuse oracle.

The Office C25EG08 stage breakdown shows strong verification alone is larger than the
remaining ZIP creation gap. EG07's fused verifier authenticates and decodes every
physical pack once, then invokes the inherited V25 extractor, which decodes those same
pack payloads a second time while reconstructing the logical profile.

This research-only A/B keeps both reads, all metadata authentication, CRC32, SHA-256,
logical reconstruction, canonical filesystem restoration and both tree comparisons.
The candidate merely reuses a raw pack *after* the second read presents the exact same
compressed payload bytes and declared raw size. A cache miss delegates to the original
Zstd decoder. Corruption rejection is compared against the baseline verifier.

No archive byte, policy, selector, recovery/locality rule, timing boundary or release
threshold changes. A material result only identifies a safe productization target.
"""

import argparse
import json
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
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

ROUNDS = 15
MIN_RELATIVE_IMPROVEMENT = 0.15
MIN_ABSOLUTE_SAVING_S = 0.005


def _eg07_reuse_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    """EG07 strong verification with exact compressed-byte keyed decode reuse."""
    with EG07._variant():
        with EG07.EG06._variant():
            owner = EG07.EG06.EG05
            V25 = owner.V25
            control = owner._metadata_control(archive)
            decoded: dict[tuple[bytes, int], bytes] = {}

            with owner._engine(archive.resolve()):
                stream, metadata, packs = V25.open_ar()
                try:
                    for index, (offset, codec, usize, csize, crc, expected_sha) in enumerate(packs):
                        stream.seek(offset)
                        payload = stream.read(csize)
                        if len(payload) != csize:
                            raise RuntimeError(f"truncated pack {index}")
                        raw = V25.zd(payload, usize) if codec == 1 else payload
                        if len(raw) != usize:
                            raise RuntimeError(f"pack size {index}")
                        if (V25.binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                            raise RuntimeError(f"pack CRC {index}")
                        if V25.H(raw) != expected_sha:
                            raise RuntimeError(f"pack SHA-256 {index}")
                        if codec == 1:
                            decoded[(payload, int(usize))] = raw
                    inner_expected = str(metadata["tree_sha256"])
                    metadata_version = int(metadata["v"])
                finally:
                    stream.close()

            original_zd = V25.zd

            def cached_zd(payload: bytes, raw_size: int) -> bytes:
                cached = decoded.get((payload, int(raw_size)))
                if cached is not None:
                    return cached
                return original_zd(payload, raw_size)

            with tempfile.TemporaryDirectory(prefix="cmpct-eg07-reuse-verify-") as td:
                restored = Path(td) / "restored"
                with owner._engine(archive.resolve()):
                    V25.zd = cached_zd
                    try:
                        V25.extract(restored)
                    finally:
                        V25.zd = original_zd
                inner_tree = V25.treehash(restored)
                if inner_tree != inner_expected:
                    raise RuntimeError(
                        f"logical tree SHA-256 mismatch: {inner_tree} != {inner_expected}"
                    )
                decoded_control = owner._restore_profile(restored, control)
                canonical_tree = owner._treehash(restored)

    if expected_tree is not None and canonical_tree != expected_tree:
        raise RuntimeError(f"canonical user-tree mismatch: {canonical_tree} != {expected_tree}")
    return {
        "ok": True,
        "profile": "federated-eg07-hybrid-rle-fs",
        "canonical_user_tree_sha256": canonical_tree,
        "filesystem_entries": len(decoded_control["manifest"]["entries"]),
        "logical_reconstruction_passes": 1,
        "physical_pack_decode_reuse": True,
        "decoded_pack_cache_entries": len(decoded),
        "inner": {
            "ok": True,
            "tree_sha256": inner_tree,
            "packs": len(packs),
            "metadata_version": metadata_version,
            "physical_pack_sha256_verified": True,
        },
    }


def _candidate_verify(archive: Path, *, expected_tree: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-reuse-") as td:
        expanded = Path(td) / "expanded.cmpct"
        parsed = EG08._expand_to_eg07(archive, expanded)
        result = dict(_eg07_reuse_verify(expanded, expected_tree=expected_tree))
    result.update(
        {
            "profile": "federated-eg08-compact-physical-framing",
            "compact_pack_count": len(parsed["packs"]),
            "recovered_from_tail": parsed["primary_error"] is not None,
        }
    )
    return result


def _identity(result: dict) -> tuple:
    return (
        bool(result.get("ok")),
        result.get("canonical_user_tree_sha256", result.get("tree_sha256")),
        result.get("profile"),
        int(result.get("compact_pack_count", -1)),
        bool(result.get("recovered_from_tail")),
        bool(result.get("inner", {}).get("physical_pack_sha256_verified")),
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-reuse-oracle-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        expected_tree = EG07._treehash(stage)
        raw_eg07, _ = DV5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = DV4._raw_eg07_parts(raw_eg07)
        features = V3._pack_features(raws)
        payload_table = V3._payload_table(raws)
        comparators = V1._comparators(stage, root / "comparators")
        size_ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )
        rules, vector, projected_bytes, _search = V5POL._search_full_frontier(
            features, meta_comp, payload_table, size_ceiling
        )
        if rules is None or vector is None or projected_bytes is None:
            raise RuntimeError("office EG08 generic policy unexpectedly lost its size win")
        archive = root / "office.c25eg08"
        emitted = V1._emit(raw_eg07, archive, V3._selection_dict(vector))
        if int(emitted["archive_bytes"]) != int(projected_bytes):
            raise RuntimeError("EG08 decode-reuse archive disagrees with exact projected bytes")

        baseline_samples: list[float] = []
        candidate_samples: list[float] = []
        reference_identity = None
        cache_entries = 0
        for index in range(ROUNDS):
            if index % 2 == 0:
                started = time.perf_counter(); baseline = EG08.strong_verify(archive, expected_tree=expected_tree); baseline_s = time.perf_counter() - started
                started = time.perf_counter(); candidate = _candidate_verify(archive, expected_tree=expected_tree); candidate_s = time.perf_counter() - started
            else:
                started = time.perf_counter(); candidate = _candidate_verify(archive, expected_tree=expected_tree); candidate_s = time.perf_counter() - started
                started = time.perf_counter(); baseline = EG08.strong_verify(archive, expected_tree=expected_tree); baseline_s = time.perf_counter() - started
            if not baseline.get("ok") or not candidate.get("ok"):
                raise RuntimeError("EG08 decode-reuse oracle failed strong verification")
            if _identity(baseline) != _identity(candidate):
                raise RuntimeError("decoded-pack reuse changed verification identity")
            if reference_identity is None:
                reference_identity = _identity(baseline)
            elif _identity(baseline) != reference_identity:
                raise RuntimeError("EG08 verification identity is nondeterministic")
            cache_entries = int(candidate.get("decoded_pack_cache_entries", 0))
            baseline_samples.append(float(baseline_s))
            candidate_samples.append(float(candidate_s))

        corrupt = root / "corrupt.c25eg08"
        blob = bytearray(archive.read_bytes())
        parsed = EG08._parse(archive)
        first_payload = bytes(parsed["packs"][0][5])
        at = bytes(blob).find(first_payload)
        if at < 0 or not first_payload:
            raise RuntimeError("could not locate first EG08 payload for corruption proof")
        blob[at + len(first_payload) // 2] ^= 0x01
        corrupt.write_bytes(blob)
        rejected = []
        for verifier in (
            lambda: EG08.strong_verify(corrupt, expected_tree=expected_tree),
            lambda: _candidate_verify(corrupt, expected_tree=expected_tree),
        ):
            try:
                result = verifier()
                rejected.append(not bool(result.get("ok")))
            except Exception:
                rejected.append(True)
        if rejected != [True, True]:
            raise RuntimeError("decoded-pack reuse weakened corruption rejection")

    baseline_median = statistics.median(baseline_samples)
    candidate_median = statistics.median(candidate_samples)
    saving = baseline_median - candidate_median
    relative = saving / max(baseline_median, 1e-12)
    material = saving >= MIN_ABSOLUTE_SAVING_S and relative >= MIN_RELATIVE_IMPROVEMENT
    return {
        "schema": "cmpct-v030-eg08-verify-decode-reuse-v1",
        "archive_bytes": int(projected_bytes),
        "rounds": ROUNDS,
        "decoded_pack_cache_entries": cache_entries,
        "baseline_verify_s": baseline_samples,
        "candidate_verify_s": candidate_samples,
        "median_baseline_verify_s": float(baseline_median),
        "median_candidate_verify_s": float(candidate_median),
        "absolute_saving_s": float(saving),
        "relative_improvement": float(relative),
        "minimum_material_relative_improvement": MIN_RELATIVE_IMPROVEMENT,
        "minimum_material_absolute_saving_s": MIN_ABSOLUTE_SAVING_S,
        "gate": {
            "exact_verification_identity": True,
            "physical_corruption_rejected_by_both": True,
            "second_archive_read_preserved": True,
            "physical_pack_sha256_preserved": True,
            "logical_and_canonical_tree_checks_preserved": True,
            "experiment_valid": True,
            "material_speedup": bool(material),
            "promotion_signal": bool(material),
            "release_credit": False,
        },
        "claim_boundary": (
            "Research-only exact-payload decode-reuse A/B. Both verifiers reread the published archive, authenticate "
            "metadata, CRC32 and SHA-256 every physical pack, reconstruct the logical profile and prove inner and "
            "canonical trees. The candidate skips only a second Zstd decode when the second read presents byte-for-byte "
            "the same compressed payload and raw-size declaration already strongly verified. No release credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-verify-decode-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-verify-decode-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("EG08 decoded-pack reuse experiment was invalid")


if __name__ == "__main__":
    main()
