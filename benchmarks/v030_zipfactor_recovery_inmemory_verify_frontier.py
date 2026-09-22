from __future__ import annotations

"""Research-only in-memory verification frontier for recovered ZIP-factor v3.

The recovered ZIP-factor candidate already crosses ZIP and Zstd-19 in bytes, while its complete creation boundary
misses ZIP by only a few milliseconds. The current recovery verifier reconstructs the exact v3 bytes through a
TemporaryDirectory + filesystem write, then the v3 verifier immediately rereads those bytes. This oracle removes
only that avoidable filesystem round trip: it applies the same v3 parser, decompression, authentication, logical
identity, locality and decode-unit checks directly to the reconstructed bytes in memory.

No archive byte, recovery rule, comparator boundary, selector or release contract changes here. A positive result
may justify moving this byte verifier into the shared implementation; a negative result identifies actual parsing /
reconstruction verification as the remaining CPU owner rather than temporary-file overhead.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import struct
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_recovery_oracle as REC
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED

ROUNDS = 9
LEVEL = 3
GROUP_SIZE = 7


def _open_bytes(candidate: bytes) -> tuple[bytes, dict, bytes, list[tuple[int, bytes, list[str], bytes]]]:
    raw = memoryview(candidate)
    if len(raw) < len(V3.MAGIC) + V3._HEADER.size or bytes(raw[: len(V3.MAGIC)]) != V3.MAGIC:
        raise RuntimeError("not a binary-control ZIP-factor profile")
    at = len(V3.MAGIC)
    manifest_size, manifest_sha, template_size, template_sha, group_count = V3._HEADER.unpack_from(raw, at)
    at += V3._HEADER.size
    if manifest_size > V3.MAX_DECODE or template_size > V3.MAX_DECODE or not 1 <= group_count <= V3.MAX_FILES:
        raise RuntimeError("binary-control ZIP-factor fixed header exceeds policy")

    descriptors: list[tuple[int, bytes, int]] = []
    for _ in range(group_count):
        if at + V3._GROUP.size > len(raw):
            raise RuntimeError("truncated binary-control ZIP-factor group descriptor")
        raw_size, raw_sha, member_count = V3._GROUP.unpack_from(raw, at)
        at += V3._GROUP.size
        if raw_size > V3.MAX_DECODE or not 1 <= member_count <= V3.MAX_FILES:
            raise RuntimeError("binary-control ZIP-factor group descriptor exceeds policy")
        descriptors.append((raw_size, raw_sha, member_count))

    manifest_blob, at = V3.BASE._read_blob(raw, at)
    template_blob, at = V3.BASE._read_blob(raw, at)
    group_blobs: list[bytes] = []
    for _ in range(group_count):
        blob, at = V3.BASE._read_blob(raw, at)
        group_blobs.append(blob)
    if at != len(raw):
        raise RuntimeError("binary-control ZIP-factor trailing archive bytes")

    manifest_raw = V3._decompress(manifest_blob, manifest_size, "manifest")
    template_raw = V3._decompress(template_blob, template_size, "template")
    if V3._sha(manifest_raw) != manifest_sha or V3._sha(template_raw) != template_sha:
        raise RuntimeError("binary-control ZIP-factor direct-member authentication")
    manifest = V3.FS.decode_manifest(manifest_raw, max_path_bytes=V3.MAX_PATH, max_entries=V3.MAX_FILES + 1024)
    regular_paths = sorted(manifest["regular"])
    if sum(member_count for _raw_size, _raw_sha, member_count in descriptors) != len(regular_paths):
        raise RuntimeError("binary-control ZIP-factor manifest/group membership mismatch")

    groups: list[tuple[int, bytes, list[str], bytes]] = []
    cursor = 0
    for (raw_size, raw_sha, member_count), blob in zip(descriptors, group_blobs, strict=True):
        paths = regular_paths[cursor : cursor + member_count]
        cursor += member_count
        groups.append((raw_size, raw_sha, paths, blob))
    return manifest_raw, manifest, template_raw, groups


def _verify_v3_bytes(candidate: bytes) -> dict:
    manifest_raw, manifest, template_raw, groups = _open_bytes(candidate)
    template = V3.BASE._parse_template(template_raw)
    identities = {V3.FS.FILESYSTEM_MANIFEST: (len(manifest_raw), V3._sha(manifest_raw))}
    seen: set[str] = set()
    max_amp = 1.0
    max_decode = len(manifest_raw)

    for raw_size, expected_group_sha, paths, blob in groups:
        group_raw = V3._decompress(blob, raw_size, "group")
        if V3._sha(group_raw) != expected_group_sha:
            raise RuntimeError("binary-control ZIP-factor group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != V3.GROUP_MAGIC:
            raise RuntimeError("bad binary-control ZIP-factor group magic")
        at = 4
        count, at = V3.BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("binary-control ZIP-factor group count mismatch")
        context = len(template_raw) + len(group_raw)
        if context > V3.MAX_DECODE:
            raise RuntimeError("binary-control ZIP-factor decode-unit ceiling")
        max_decode = max(max_decode, context)

        for rel in paths:
            if rel in seen or rel not in manifest["regular"]:
                raise RuntimeError("binary-control ZIP-factor logical path mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor dynamics")
                crc, csize, usize = struct.unpack_from("<III", view, at)
                at += 12
                if csize > V3.MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor payload")
                payload = bytes(view[at : at + csize])
                at += csize
                dynamics.append((crc, csize, usize, payload))
            restored = V3.BASE._rebuild_zip(template, dynamics)
            expected_size, expected_sha = manifest["regular"][rel]
            got_sha = V3._sha(restored)
            if len(restored) != expected_size or got_sha != expected_sha:
                raise RuntimeError(f"binary-control ZIP-factor reconstructed identity mismatch: {rel}")
            amp = context / max(1, len(restored))
            if amp > V3.MAX_AMP:
                raise RuntimeError(f"binary-control ZIP-factor locality ceiling: {rel}")
            max_amp = max(max_amp, amp)
            seen.add(rel)
            identities[rel] = (len(restored), got_sha)
        if at != len(view):
            raise RuntimeError("binary-control ZIP-factor group trailing bytes")

    if seen != set(manifest["regular"]):
        raise RuntimeError("binary-control ZIP-factor manifest/content membership mismatch")
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
    }


def recover_verify_inmemory(path: Path) -> dict:
    raw = Path(path).read_bytes()
    errors: dict[str, str] = {}
    try:
        primary_len = REC._control_len_from_primary(raw)
        tail_len, tail_start, _tail_sha = REC._tail_layout(raw)
        if tail_len != primary_len:
            raise RuntimeError("ZIP-factor recovery control copy length mismatch")
        primary = raw[8 : 8 + primary_len]
        candidate = REC._v3_candidate(raw, primary, 8 + primary_len, tail_start)
        result = _verify_v3_bytes(candidate)
        return {"ok": True, "recovered_from": "primary", "result": result}
    except Exception as exc:
        errors["primary"] = repr(exc)

    try:
        control, tail_start = REC._tail_control(raw)
        body_start = 8 + len(control)
        candidate = REC._v3_candidate(raw, control, body_start, tail_start)
        result = _verify_v3_bytes(candidate)
        return {"ok": True, "recovered_from": "tail", "result": result, "primary_error": errors.get("primary")}
    except Exception as exc:
        errors["tail"] = repr(exc)
        return {"ok": False, "errors": errors}


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-rec-memory-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        expected_external_tree = EXT._tree(stage)
        cmpct_samples: list[float] = []
        build_samples: list[float] = []
        verify_samples: list[float] = []
        legacy_verify_samples: list[float] = []
        zip_samples: list[float] = []
        zstd_samples: list[float] = []
        candidate_sizes: set[int] = set()
        candidate_sha: set[str] = set()
        snapshots: set[str] = set()
        stats: dict | None = None

        order = ("cmpct", "zip", "zstd")
        original_build = V3.build
        V3.build = FUSED.build
        try:
            for round_index in range(ROUNDS):
                rotated = order[round_index % 3 :] + order[: round_index % 3]
                for kind in rotated:
                    if kind == "cmpct":
                        archive = td / f"candidate-{round_index}.cmpct"
                        t0 = time.perf_counter()
                        stats = REC.build_recovery(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
                        t1 = time.perf_counter()
                        verified = recover_verify_inmemory(archive)
                        t2 = time.perf_counter()
                        if not verified.get("ok"):
                            raise RuntimeError(f"in-memory recovery verification failed: {verified!r}")
                        snapshot = REC._snapshot(verified)
                        snapshots.add(json.dumps(snapshot, sort_keys=True))
                        candidate_sizes.add(int(archive.stat().st_size))
                        candidate_sha.add(hashlib.sha256(archive.read_bytes()).hexdigest())
                        build_samples.append(t1 - t0)
                        verify_samples.append(t2 - t1)
                        cmpct_samples.append(t2 - t0)
                        legacy_t0 = time.perf_counter()
                        legacy = REC.recover_verify(archive)
                        legacy_t1 = time.perf_counter()
                        if not legacy.get("ok") or REC._snapshot(legacy) != snapshot:
                            raise RuntimeError("in-memory verifier diverged from legacy recovery verifier")
                        legacy_verify_samples.append(legacy_t1 - legacy_t0)
                    elif kind == "zip":
                        result = EXT._zip(stage, td / f"archive-{round_index}.zip", td / f"zip-out-{round_index}")
                        EXT._verify_extracted(td / f"zip-out-{round_index}", expected_external_tree, "zf-rec-memory-zip")
                        zip_samples.append(float(result["create_s"]))
                    else:
                        work = td / f"zstd-work-{round_index}"
                        work.mkdir()
                        result = EXT._tar_zstd(stage, td / f"archive-{round_index}.tar.zst", td / f"zstd-out-{round_index}", work)
                        if not result.get("available"):
                            raise RuntimeError("solid Zstd-19 unavailable")
                        EXT._verify_extracted(td / f"zstd-out-{round_index}", expected_external_tree, "zf-rec-memory-zstd")
                        zstd_samples.append(float(result["create_s"]))
        finally:
            V3.build = original_build

        if len(candidate_sizes) != 1 or len(candidate_sha) != 1 or len(snapshots) != 1 or stats is None:
            raise RuntimeError("in-memory recovery candidate was not deterministic")

        zip_size = EXT._zip(stage, td / "size.zip", td / "size-zip-out")
        zw = td / "size-zstd-work"
        zw.mkdir()
        zstd_size = EXT._tar_zstd(stage, td / "size.tar.zst", td / "size-zstd-out", zw)
        if not zstd_size.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable for size ratchet")

        cmpct_bytes = next(iter(candidate_sizes))
        zip_bytes = int(zip_size["archive_bytes"])
        zstd_bytes = int(zstd_size["archive_bytes"])
        med_cmpct = _median(cmpct_samples)
        med_zip = _median(zip_samples)
        med_zstd = _median(zstd_samples)
        strict = cmpct_bytes < zip_bytes and cmpct_bytes < zstd_bytes and med_cmpct < med_zip and med_cmpct < med_zstd
        return {
            "schema": "cmpct-v030-zipfactor-recovery-inmemory-verify-frontier-v1",
            "contract": {
                "rounds": ROUNDS,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "archive_bytes_changed": False,
                "recovery_semantics_changed": False,
                "verification_semantics": "same-v3-parse-auth-identity-locality-decode-unit-checks-directly-on-reconstructed-bytes",
                "legacy_verifier_cross_checked_each_round": True,
                "ties_fail": True,
                "selector_change": False,
                "release_credit": False,
            },
            "sizes": {"cmpct": cmpct_bytes, "zip": zip_bytes, "zstd19": zstd_bytes},
            "medians_s": {"cmpct": med_cmpct, "zip": med_zip, "zstd19": med_zstd},
            "cmpct_phase_medians_s": {
                "build": _median(build_samples),
                "inmemory_verify": _median(verify_samples),
                "legacy_verify_control": _median(legacy_verify_samples),
            },
            "samples_s": {"cmpct": cmpct_samples, "zip": zip_samples, "zstd19": zstd_samples},
            "strict_four_way_win": strict,
            "experiment_valid": (
                len(cmpct_samples) == len(zip_samples) == len(zstd_samples) == ROUNDS
                and len(legacy_verify_samples) == ROUNDS
                and cmpct_bytes < zip_bytes
                and cmpct_bytes < zstd_bytes
                and float(stats["max_member_read_amplification"]) <= 8.0
                and int(stats["max_decode_unit_bytes"]) <= 8 * 1024 * 1024
            ),
            "promotion_signal": strict,
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor in-memory verification frontier invalid")


if __name__ == "__main__":
    main()
