from __future__ import annotations

"""R4 Shifted capacity test: one complete base plus bounded-drift sequential edits.

The latent + delta-program family is retired: even one shared patch compression context
remains larger than exact solid Zstd-19. This experiment changes the reconstruction
representation itself. It stores one complete member selected only by logical-content
SHA-256 and represents every sibling as long sequential copies separated by sparse
replacement/insert/delete runs. All edit programs share one bounded compression context.

The decisive question is whether removing rolling-block delta instruction entropy can
cross the strict size floor *without* exporting locality/decode-unit debt. Research only;
a win advances the next productization/runtime prerequisite and grants no release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks.resemblance_hostile_corpus_v1 import shifted_versions, tree_hash
from benchmarks import v030_shifted_latent_consensus_floor as LAT

SYNC = 48
MAX_RESYNC = 1024
COMMON_CHUNK = 4096
LEVEL = 19
MAX_DECODE = 8 * 1024 * 1024


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative varint")
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(buf) or shift > 63:
            raise ValueError("malformed varint")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, pos
        shift += 7


def _common_prefix_len(a: bytes, b: bytes, ai: int, bi: int) -> int:
    limit = min(len(a) - ai, len(b) - bi)
    n = 0
    while n + COMMON_CHUNK <= limit and a[ai + n:ai + n + COMMON_CHUNK] == b[bi + n:bi + n + COMMON_CHUNK]:
        n += COMMON_CHUNK
    while n < limit and a[ai + n] == b[bi + n]:
        n += 1
    return n


def _find_resync(base: bytes, target: bytes, i: int, j: int) -> tuple[int, int]:
    """Return (delete_from_base, insert_from_target) for the smallest bounded exact resync.

    Three generic edit shapes are considered: same-width replacement, insertion into the
    target, and deletion from the base. The search is content-only and bounded; failure
    falls back to a bounded same-width replacement so construction always makes progress.
    """
    rem_b = len(base) - i
    rem_t = len(target) - j
    diag_limit = min(MAX_RESYNC, rem_b, rem_t)
    for k in range(1, diag_limit + 1):
        if min(rem_b - k, rem_t - k) < SYNC:
            break
        if base[i + k:i + k + SYNC] == target[j + k:j + k + SYNC]:
            return k, k

    candidates: list[tuple[int, int]] = []
    if rem_b >= SYNC:
        token = base[i:i + SYNC]
        end = min(len(target), j + MAX_RESYNC + SYNC)
        pos_t = target.find(token, j + 1, end)
        if pos_t >= 0:
            candidates.append((0, pos_t - j))
    if rem_t >= SYNC:
        token = target[j:j + SYNC]
        end = min(len(base), i + MAX_RESYNC + SYNC)
        pos_b = base.find(token, i + 1, end)
        if pos_b >= 0:
            candidates.append((pos_b - i, 0))
    if candidates:
        return min(candidates, key=lambda x: (x[0] + x[1], max(x), x))

    # Exact bounded fallback. It is intentionally simple and fully priced; frequent use
    # is evidence against this representation rather than a reason to hide more search.
    step = min(256, rem_b, rem_t)
    if step:
        return step, step
    return rem_b, rem_t


def _encode_edit(base: bytes, target: bytes) -> tuple[bytes, dict]:
    i = j = 0
    records: list[tuple[int, int, bytes]] = []
    copied = inserted = deleted = fallback_like = 0
    while i < len(base) or j < len(target):
        common = _common_prefix_len(base, target, i, j) if i < len(base) and j < len(target) else 0
        i += common
        j += common
        copied += common
        if i == len(base) and j == len(target):
            records.append((common, 0, b""))
            break
        if i == len(base):
            literal = target[j:]
            records.append((common, 0, literal))
            inserted += len(literal)
            j = len(target)
            continue
        if j == len(target):
            delete_n = len(base) - i
            records.append((common, delete_n, b""))
            deleted += delete_n
            i = len(base)
            continue
        delete_n, insert_n = _find_resync(base, target, i, j)
        literal = target[j:j + insert_n]
        if delete_n == insert_n == min(256, len(base) - i, len(target) - j) and delete_n:
            fallback_like += 1
        records.append((common, delete_n, literal))
        i += delete_n
        j += insert_n
        deleted += delete_n
        inserted += insert_n

    out = bytearray()
    _put_varint(out, len(records))
    for copy_n, delete_n, literal in records:
        _put_varint(out, copy_n)
        _put_varint(out, delete_n)
        _put_varint(out, len(literal))
        out.extend(literal)
    return bytes(out), {
        "records": len(records),
        "copied_bytes": copied,
        "deleted_bytes": deleted,
        "inserted_bytes": inserted,
        "fallback_like_records": fallback_like,
    }


def _decode_edit(base: bytes, program: bytes, expected_size: int) -> bytes:
    pos = 0
    count, pos = _get_varint(program, pos)
    cursor = 0
    out = bytearray()
    for _ in range(count):
        copy_n, pos = _get_varint(program, pos)
        delete_n, pos = _get_varint(program, pos)
        insert_n, pos = _get_varint(program, pos)
        if cursor + copy_n + delete_n > len(base) or pos + insert_n > len(program):
            raise ValueError("bounded edit exceeds input")
        out.extend(base[cursor:cursor + copy_n])
        cursor += copy_n + delete_n
        out.extend(program[pos:pos + insert_n])
        pos += insert_n
        if len(out) > MAX_DECODE:
            raise ValueError("bounded edit exceeds decode unit")
    if pos != len(program) or cursor != len(base) or len(out) != expected_size:
        raise ValueError("bounded edit terminal mismatch")
    return bytes(out)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = tree_hash(source)
    rows = [(p.name, p.read_bytes()) for p in sorted(source.iterdir())]
    if len(rows) != 18:
        raise AssertionError("frozen Shifted file count drift")

    base_name, base = min(rows, key=lambda x: hashlib.sha256(x[1]).digest())
    if len(base) > MAX_DECODE:
        raise AssertionError("base violates decode-unit bound")

    candidate_started = time.perf_counter()
    phase_started = time.perf_counter()
    programs: list[tuple[str, int, bytes, bytes, dict]] = []
    for name, target in rows:
        digest = hashlib.sha256(target).digest()
        if name == base_name:
            programs.append((name, len(target), b"", digest, {"records": 0, "copied_bytes": len(base), "deleted_bytes": 0, "inserted_bytes": 0, "fallback_like_records": 0}))
            continue
        program, stats = _encode_edit(base, target)
        programs.append((name, len(target), program, digest, stats))
    edit_construction_s = time.perf_counter() - phase_started

    patch_raw = b"".join(program for _, _, program, _, _ in programs)
    if len(patch_raw) > MAX_DECODE:
        raise AssertionError("shared edit context exceeds decode-unit bound")

    phase_started = time.perf_counter()
    base_stored = zstd.ZstdCompressor(level=LEVEL, threads=0, write_checksum=True).compress(base)
    base_compress_s = time.perf_counter() - phase_started
    phase_started = time.perf_counter()
    patch_stored = zstd.ZstdCompressor(level=LEVEL, threads=0, write_checksum=True).compress(patch_raw)
    patch_compress_s = time.perf_counter() - phase_started

    artifact = bytearray(b"CMPNXBDE1")
    base_nb = base_name.encode()
    _put_varint(artifact, len(base_nb)); artifact.extend(base_nb)
    artifact.extend(hashlib.sha256(base).digest())
    _put_varint(artifact, len(base)); _put_varint(artifact, len(base_stored)); artifact.extend(base_stored)
    _put_varint(artifact, len(patch_raw)); _put_varint(artifact, len(patch_stored)); artifact.extend(patch_stored)
    _put_varint(artifact, len(programs))
    for name, logical_n, program, digest, _ in programs:
        nb = name.encode()
        _put_varint(artifact, len(nb)); artifact.extend(nb)
        _put_varint(artifact, logical_n)
        _put_varint(artifact, len(program))
        artifact.extend(digest)
    artifact.extend(bytes.fromhex(expected_tree))
    candidate_create_s = time.perf_counter() - candidate_started

    unpacked = zstd.ZstdDecompressor().decompress(patch_stored, max_output_size=MAX_DECODE)
    if unpacked != patch_raw:
        raise AssertionError("shared edit context round trip mismatch")
    verify = work_root / "verify"
    verify.mkdir()
    pos = 0
    for name, logical_n, program, digest, _ in programs:
        if name == base_name:
            rebuilt = base
        else:
            got_program = unpacked[pos:pos + len(program)]
            rebuilt = _decode_edit(base, got_program, logical_n)
            pos += len(program)
        if hashlib.sha256(rebuilt).digest() != digest:
            raise AssertionError("member digest mismatch")
        (verify / name).write_bytes(rebuilt)
    if pos != len(unpacked) or tree_hash(verify) != expected_tree:
        raise AssertionError("exact tree mismatch")

    zip_row = LAT.COMP._zip_deflate(source, work_root / "competitor.zip")
    zstd_row = LAT.COMP._solid_tar_zstd(source, work_root / "competitor.tar.zst")
    if not zip_row.get("available") or not zstd_row.get("available"):
        raise RuntimeError("required external comparator unavailable")

    payload_floor = len(base_stored) + len(patch_stored)
    max_logical = max(len(data) for _, data in rows)
    max_amp = max((len(base) + len(patch_raw) + len(data)) / max(1, len(data)) for _, data in rows)
    zbytes = int(zstd_row["bytes"])
    strict = (
        len(artifact) < int(zip_row["bytes"])
        and len(artifact) < zbytes
        and candidate_create_s < float(zip_row["create_s"])
        and candidate_create_s < float(zstd_row["create_s"])
    )
    if strict:
        terminal = "PROMOTE_NEXT_PREREQUISITE"
        next_test = "generalize content-only admission and canonical reader/recovery semantics before any selector credit"
    elif payload_floor >= zbytes:
        terminal = "RETIRE_FAMILY"
        next_test = "retire bounded-drift single-base ownership and invent a multi-base or non-base reconstruction boundary"
    elif len(artifact) >= zbytes:
        terminal = "ITERATE_SAME_FAMILY"
        next_test = "reduce generic framing/control bytes because the exact payload floor already crosses Zstd"
    else:
        terminal = "REHABILITATE_DEBT"
        next_test = "move the byte-identical edit construction/compression hot path native or single-pass to cross the external creation budget"

    total_stats = {
        key: sum(int(stats[key]) for _, _, _, _, stats in programs)
        for key in ("records", "copied_bytes", "deleted_bytes", "inserted_bytes", "fallback_like_records")
    }
    return {
        "schema": "cmpct-v030-shifted-bounded-drift-edit-floor-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local",
        "strict_target": "15/15: each workload strictly smaller and faster than ZIP/Deflate and solid Zstd-19; ties fail",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation_inherited": ["S1", "S3", "S4"],
        "rps": 100,
        "referee": {
            "causal_hypothesis": "rolling-block delta instruction entropy, not the shared base itself, is the remaining Shifted size tax",
            "strongest_control": "retired latent + one shared delta context, whose complete artifact remained 12,303 B above exact Zstd-19",
            "disproof": "the optimistic base+shared-edit payload floor remains >= exact solid Zstd-19 bytes",
            "strongest_failure": "a size win can still lose the strict contract if bounded Python edit construction exceeds ZIP/Zstd creation time",
        },
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "base_selection": "minimum logical-content SHA-256",
            "sequential_copy_edit_grammar": True,
            "sync_bytes": SYNC,
            "max_resync_bytes": MAX_RESYNC,
            "single_shared_edit_context": True,
            "max_chain_depth": 1,
            "release_credit": False,
        },
        "workload": {"files": len(rows), "logical_bytes": sum(len(d) for _, d in rows), "tree_sha256": expected_tree},
        "timing": {
            "edit_construction_s": edit_construction_s,
            "base_compress_s": base_compress_s,
            "patch_compress_s": patch_compress_s,
            "candidate_create_s": candidate_create_s,
        },
        "candidate": {
            "base_name": base_name,
            "base_logical_bytes": len(base),
            "base_stored_bytes": len(base_stored),
            "edit_raw_bytes": len(patch_raw),
            "edit_stored_bytes": len(patch_stored),
            "payload_floor_bytes": payload_floor,
            "archive_bytes": len(artifact),
            "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
            "create_seconds": candidate_create_s,
            "tree_verified": True,
            "max_chain_depth": 1,
            "max_decode_unit_bytes": max(len(base), len(patch_raw), max_logical),
            "max_member_read_amplification": max_amp,
            **total_stats,
        },
        "comparators": {"zip_deflate9": zip_row, "tar_zstd19_solid": zstd_row},
        "hostile_reviewer": {
            "all_edit_construction_is_inside_candidate_timing": True,
            "base_and_edit_compression_are_inside_candidate_timing": True,
            "verification_and_comparators_are_outside_candidate_timing_symmetrically": True,
            "bounded_fallback_is_counted": True,
            "shared_context_decode_work_is_charged_in_member_amplification": True,
            "remaining_unpriced_debt": "canonical/recovery/native/Android semantics receive no release credit from this research grammar",
        },
        "decision": {
            "payload_floor_zstd_gap_bytes": payload_floor - zbytes,
            "archive_zstd_gap_bytes": len(artifact) - zbytes,
            "strict_four_way_win": strict,
            "terminal": terminal,
            "release_credit": False,
            "next_decisive_test": next_test,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
