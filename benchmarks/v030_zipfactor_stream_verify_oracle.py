from __future__ import annotations

"""Exact A/B for materialized versus streaming ZIP-factor logical verification.

Both paths verify the same binary-control-v3 archive. The streaming path must produce the exact same per-member
(size, SHA-256) identities, semantic tree, locality accounting and decode-unit bound as the reference verifier.
Only the temporary reconstructed-ZIP allocation/copy is removed. No release threshold or verification fact changes.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_zipfactor_stream_verify as STREAM

REPEATS = 21


def _stream_scan(archive: Path) -> dict:
    manifest_raw, manifest, template_raw, groups = V3._open(archive)
    template = BASE._parse_template(template_raw)
    identities = {FS.FILESYSTEM_MANIFEST: (len(manifest_raw), hashlib.sha256(manifest_raw).digest())}
    seen: set[str] = set()
    max_amp = 1.0
    max_decode = len(manifest_raw)

    for raw_size, expected_group_sha, paths, blob in groups:
        group_raw = V3._decompress(blob, raw_size, "group")
        if hashlib.sha256(group_raw).digest() != expected_group_sha:
            raise RuntimeError("streaming verifier group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != V3.GROUP_MAGIC:
            raise RuntimeError("streaming verifier group magic")
        at = 4
        count, at = BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("streaming verifier group count")
        context = len(template_raw) + len(group_raw)
        if context > V3.MAX_DECODE:
            raise RuntimeError("streaming verifier decode-unit ceiling")
        max_decode = max(max_decode, context)

        for rel in paths:
            if rel in seen or rel not in manifest["regular"]:
                raise RuntimeError("streaming verifier logical path mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("streaming verifier truncated dynamics")
                import struct
                crc, csize, usize = struct.unpack_from("<III", view, at)
                at += 12
                if csize > V3.MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("streaming verifier truncated payload")
                payload = bytes(view[at:at + csize])
                at += csize
                dynamics.append((crc, csize, usize, payload))

            expected_size, expected_sha = manifest["regular"][rel]
            got_size, got_sha = STREAM.rebuilt_zip_identity(template, dynamics)
            if got_size != expected_size or got_sha != expected_sha:
                raise RuntimeError(f"streaming verifier reconstructed identity mismatch: {rel}")
            amp = context / max(1, got_size)
            if amp > V3.MAX_AMP:
                raise RuntimeError(f"streaming verifier locality ceiling: {rel}")
            max_amp = max(max_amp, amp)
            seen.add(rel)
            identities[rel] = (got_size, got_sha)
        if at != len(view):
            raise RuntimeError("streaming verifier group trailing bytes")

    if seen != set(manifest["regular"]):
        raise RuntimeError("streaming verifier membership mismatch")
    return {
        "ok": True,
        "manifest": manifest,
        "identities": identities,
        "verified_user_files": len(seen),
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_decode,
    }


def _timed(fn, archive: Path) -> tuple[dict, list[float]]:
    result = fn(archive)
    samples: list[float] = []
    for _ in range(REPEATS):
        started = time.perf_counter()
        result = fn(archive)
        samples.append(time.perf_counter() - started)
    return result, samples


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-stream-verify-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        archive = td / "candidate-v3.cmpct"
        V3.build(stage, archive, level=6, group_size=7)

        reference, reference_times = _timed(V3.verify_and_identities, archive)
        streaming, streaming_times = _timed(_stream_scan, archive)
        source_semantic = CANON._semantic_tree_sha(reference["manifest"])
        streaming_semantic = CANON._semantic_tree_sha(streaming["manifest"])

        identity_exact = reference["identities"] == streaming["identities"]
        locality_exact = (
            reference["verified_user_files"] == streaming["verified_user_files"]
            and reference["max_member_read_amplification"] == streaming["max_member_read_amplification"]
            and reference["max_decode_unit_bytes"] == streaming["max_decode_unit_bytes"]
        )
        ref_median = statistics.median(reference_times)
        stream_median = statistics.median(streaming_times)
        ratio = stream_median / ref_median if ref_median else float("inf")

        result = {
            "schema": "cmpct-v030-zipfactor-stream-verify-oracle-v1",
            "claim_boundary": "verification implementation A/B only; no selector/native/Android/recovery promotion",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "archive_bytes": archive.stat().st_size,
            "repeats": REPEATS,
            "reference": {
                "median_verify_s": ref_median,
                "min_verify_s": min(reference_times),
                "semantic_tree_sha256": source_semantic,
            },
            "streaming": {
                "median_verify_s": stream_median,
                "min_verify_s": min(streaming_times),
                "semantic_tree_sha256": streaming_semantic,
                "max_member_read_amplification": streaming["max_member_read_amplification"],
                "max_decode_unit_bytes": streaming["max_decode_unit_bytes"],
            },
            "delta": {
                "median_verify_s": stream_median - ref_median,
                "median_ratio": ratio,
                "median_improvement_pct": (1.0 - ratio) * 100.0,
            },
            "gate": {
                "identity_exact": identity_exact,
                "semantic_tree_exact": source_semantic == streaming_semantic,
                "locality_accounting_exact": locality_exact,
                "strong_identity_count_exact": len(reference["identities"]) == len(streaming["identities"]),
                "streaming_faster_median": stream_median < ref_median,
            },
        }
        result["gate"]["passed"] = all(result["gate"].values())
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-verify-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-verify.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"delta": result["delta"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor streaming verification oracle failed")


if __name__ == "__main__":
    main()
