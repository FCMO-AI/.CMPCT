from __future__ import annotations

"""Exact A/B for parallel strong verification of the bounded ZIP-factor v3 candidate.

The canonical ZIP-factor candidate already splits the deflate-family workload into independently decodable
locality-bounded groups. This oracle changes no bytes and no integrity rule: it compares the shipping serial
verification algorithm with a bounded thread-parallel implementation that verifies each authenticated group
independently, then deterministically merges the resulting logical identities.

Experiment validity and promotion are intentionally separate. Exact authenticated filesystem identity, complete
logical identities, locality accounting, decode bounds and deterministic repeated measurements are mandatory for
a valid experiment. The parallel path earns a promotion signal only when it is also strictly faster. A valid but
slower result is durable negative evidence with zero release/selector credit; it must not remain a permanent-red CI
lane or be misrepresented as a performance win.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import statistics
import struct
import time

from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_product_fs as FS

ROUNDS = 31
MAX_WORKERS = 4


def _verify_group(
    template: dict,
    template_raw: bytes,
    manifest: dict,
    descriptor: tuple[int, bytes, list[str], bytes],
) -> tuple[dict[str, tuple[int, bytes]], float, int]:
    raw_size, expected_group_sha, paths, blob = descriptor
    group_raw = V3._decompress(blob, raw_size, "group")
    if V3._sha(group_raw) != expected_group_sha:
        raise RuntimeError("parallel ZIP-factor group authentication")
    view = memoryview(group_raw)
    if bytes(view[:4]) != V3.GROUP_MAGIC:
        raise RuntimeError("bad parallel ZIP-factor group magic")
    at = 4
    count, at = BASE._read_uvarint(view, at)
    if count != len(paths):
        raise RuntimeError("parallel ZIP-factor group count mismatch")

    context = len(template_raw) + len(group_raw)
    if context > V3.MAX_DECODE:
        raise RuntimeError("parallel ZIP-factor decode-unit ceiling")
    identities: dict[str, tuple[int, bytes]] = {}
    max_amp = 1.0
    seen: set[str] = set()

    for rel in paths:
        if rel in seen or rel not in manifest["regular"]:
            raise RuntimeError("parallel ZIP-factor logical path mismatch")
        dynamics = []
        for _row in template["rows"]:
            if at + 12 > len(view):
                raise RuntimeError("truncated parallel ZIP-factor dynamics")
            crc, csize, usize = struct.unpack_from("<III", view, at)
            at += 12
            if csize > V3.MAX_DECODE or at + csize > len(view):
                raise RuntimeError("truncated parallel ZIP-factor payload")
            payload = bytes(view[at : at + csize])
            at += csize
            dynamics.append((crc, csize, usize, payload))
        restored = BASE._rebuild_zip(template, dynamics)
        expected_size, expected_sha = manifest["regular"][rel]
        got_sha = V3._sha(restored)
        if len(restored) != expected_size or got_sha != expected_sha:
            raise RuntimeError(f"parallel ZIP-factor reconstructed identity mismatch: {rel}")
        amp = context / max(1, len(restored))
        if amp > V3.MAX_AMP:
            raise RuntimeError(f"parallel ZIP-factor locality ceiling: {rel}")
        max_amp = max(max_amp, amp)
        identities[rel] = (len(restored), got_sha)
        seen.add(rel)

    if at != len(view):
        raise RuntimeError("parallel ZIP-factor group trailing bytes")
    return identities, max_amp, context


def parallel_verify_and_identities(archive: Path) -> dict:
    manifest_raw, manifest, template_raw, groups = V3._open(archive)
    template = BASE._parse_template(template_raw)
    identities: dict[str, tuple[int, bytes]] = {
        FS.FILESYSTEM_MANIFEST: (len(manifest_raw), V3._sha(manifest_raw))
    }
    max_amp = 1.0
    max_decode = len(manifest_raw)

    workers = min(MAX_WORKERS, len(groups))
    if workers <= 1:
        results = [_verify_group(template, template_raw, manifest, group) for group in groups]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-zf-verify") as pool:
            futures = [pool.submit(_verify_group, template, template_raw, manifest, group) for group in groups]
            # Consume in archive order so identity merging is deterministic even though work runs concurrently.
            results = [future.result() for future in futures]

    seen: set[str] = set()
    for group_identities, group_amp, group_decode in results:
        overlap = seen.intersection(group_identities)
        if overlap:
            raise RuntimeError(f"parallel ZIP-factor duplicate identities: {sorted(overlap)!r}")
        seen.update(group_identities)
        identities.update(group_identities)
        max_amp = max(max_amp, group_amp)
        max_decode = max(max_decode, group_decode)

    if seen != set(manifest["regular"]):
        raise RuntimeError("parallel ZIP-factor manifest/content membership mismatch")
    return {
        "ok": True,
        "format_revision": V3.REVISION,
        "format_profile": V3.PROFILE,
        "manifest_raw": manifest_raw,
        "manifest": manifest,
        "identities": identities,
        "verified_user_files": len(seen),
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_decode,
        "workers": workers,
    }


def _snapshot(result: dict) -> dict:
    identities = {
        path: [size, digest.hex()]
        for path, (size, digest) in sorted(result["identities"].items())
    }
    return {
        "manifest_sha256": hashlib.sha256(result["manifest_raw"]).hexdigest(),
        "identities": identities,
        "verified_user_files": result["verified_user_files"],
        "max_member_read_amplification": result["max_member_read_amplification"],
        "max_decode_unit_bytes": result["max_decode_unit_bytes"],
    }


def _measure(function, archive: Path, rounds: int) -> tuple[list[float], dict]:
    times: list[float] = []
    snapshot = None
    for _ in range(rounds):
        started = time.perf_counter()
        result = function(archive)
        elapsed = time.perf_counter() - started
        if not result.get("ok"):
            raise RuntimeError(f"ZIP-factor verifier returned non-green result: {result!r}")
        current = _snapshot(result)
        if snapshot is None:
            snapshot = current
        elif current != snapshot:
            raise RuntimeError("ZIP-factor verifier is nondeterministic across repeated rounds")
        times.append(elapsed)
    assert snapshot is not None
    return times, snapshot


def run(work_root: Path, rounds: int = ROUNDS) -> dict:
    if rounds < 9 or rounds % 2 == 0:
        raise ValueError("rounds must be an odd integer >= 9")
    work_root.mkdir(parents=True, exist_ok=True)
    workload_root = work_root / "corpus"
    EXT.shutil.rmtree(workload_root, ignore_errors=True)
    workload_root.mkdir(parents=True)

    hostile = EXT.GENERAL.V029._load(
        EXT.GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_zipfactor_parallel_verify_hostile",
    )
    hostile.build(workload_root)
    source = workload_root / "04_deflate_family"
    archive = work_root / "candidate.cmpct"
    build = V3.build(source, archive, level=3, group_size=7)

    # Alternate measurement order across two full blocks to reduce a fixed warm-cache/order advantage.
    serial_a, serial_snapshot_a = _measure(V3.verify_and_identities, archive, rounds)
    parallel_a, parallel_snapshot_a = _measure(parallel_verify_and_identities, archive, rounds)
    parallel_b, parallel_snapshot_b = _measure(parallel_verify_and_identities, archive, rounds)
    serial_b, serial_snapshot_b = _measure(V3.verify_and_identities, archive, rounds)

    if not (serial_snapshot_a == serial_snapshot_b == parallel_snapshot_a == parallel_snapshot_b):
        raise RuntimeError("parallel ZIP-factor verifier changed canonical verification facts")

    serial_times = serial_a + serial_b
    parallel_times = parallel_a + parallel_b
    serial_median = statistics.median(serial_times)
    parallel_median = statistics.median(parallel_times)
    improvement_s = serial_median - parallel_median
    improvement_pct = 100.0 * improvement_s / serial_median
    exact = serial_snapshot_a == parallel_snapshot_a
    bounds_ok = (
        serial_snapshot_a["verified_user_files"] == int(build["user_files"])
        and serial_snapshot_a["max_member_read_amplification"] <= V3.MAX_AMP
        and serial_snapshot_a["max_decode_unit_bytes"] <= V3.MAX_DECODE
    )
    faster = parallel_median < serial_median
    experiment_valid = exact and bounds_ok
    promotion_signal = experiment_valid and faster

    gate = {
        "exact_manifest_and_logical_identities": exact,
        "bounds_and_membership_valid": bounds_ok,
        "parallel_strictly_faster": faster,
        "serial_median_s": serial_median,
        "parallel_median_s": parallel_median,
        "improvement_s": improvement_s,
        "improvement_pct": improvement_pct,
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "release_credit": False,
        # Backward-compatible diagnostic only. Release/promotion consumers must use promotion_signal.
        "passed": promotion_signal,
    }
    return {
        "schema": "cmpct-v030-zipfactor-parallel-verify-oracle-v2",
        "candidate": build,
        "rounds_per_order": rounds,
        "total_samples_per_implementation": len(serial_times),
        "serial": {
            "median_s": serial_median,
            "min_s": min(serial_times),
            "max_s": max(serial_times),
        },
        "parallel": {
            "median_s": parallel_median,
            "min_s": min(parallel_times),
            "max_s": max(parallel_times),
            "workers": min(MAX_WORKERS, int(build["groups"])),
        },
        "verification_snapshot": serial_snapshot_a,
        "gate": gate,
        "claim_boundary": (
            "Research A/B only. experiment_valid proves exact bounded measurement; promotion_signal additionally "
            "requires bounded parallel verification to be strictly faster. A valid negative result has zero release "
            "or selector credit. Canonical ZIP-factor dispatch, recovery, native/Android promotion and release remain "
            "separate mandatory blockers."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel-verify-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-parallel-verify.json"))
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    args = parser.parse_args()
    result = run(args.work_root, args.rounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("ZIP-factor parallel verification experiment was invalid")


if __name__ == "__main__":
    main()
