from __future__ import annotations

"""R4 Shifted joint edit-stream representation oracle.

Research-only falsifier for a representation family not covered by the retired native Zstd
patch sweeps.  One structurally selected member is stored as an anchor.  Every other
member becomes an exact bounded alignment + sparse substitution program.  The anchor
and all edit programs are then compressed *jointly* as one <=8 MiB decode unit, so the
compressor may exploit redundancy inside the transformed representation instead of
paying independently compressed patch ownership.

The representation never consults benchmark names, hashes, or frozen-pack identity.
All source scanning, anchor selection, alignment search, edit construction, compression,
framing, hashing and publication are charged to candidate creation time.  A research
win earns no release credit; it only advances the next productization prerequisite.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_authoritative as CMPCT

MAGIC = b"C30JE1\0"
TRANSFORM_MAGIC = b"JES1"
LEVELS = (1, 3, 6, 9, 12, 19)
MAX_ALIGNMENT = 64
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_LOCALITY = 8.0


def _u32(n: int) -> bytes:
    return struct.pack("<I", n)


def _u64(n: int) -> bytes:
    return struct.pack("<Q", n)


def _read_u32(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 4 > len(raw):
        raise RuntimeError("truncated joint-edit u32")
    return struct.unpack_from("<I", raw, off)[0], off + 4


def _read_u64(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 8 > len(raw):
        raise RuntimeError("truncated joint-edit u64")
    return struct.unpack_from("<Q", raw, off)[0], off + 8


def _files(root: Path) -> list[Path]:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError("joint-edit oracle requires regular files")
    if any(p.is_symlink() for p in files):
        raise RuntimeError("joint-edit oracle does not accept symlinks")
    return files


def _anchor(rows: list[tuple[str, bytes]]) -> int:
    # Pure structural selection: nearest to median size, then content digest.  Paths and
    # benchmark identity do not participate in the choice.
    sizes = sorted(len(raw) for _, raw in rows)
    median = sizes[len(sizes) // 2]
    return min(
        range(len(rows)),
        key=lambda i: (abs(len(rows[i][1]) - median), hashlib.sha256(rows[i][1]).digest()),
    )


def _alignment(anchor: bytes, target: bytes) -> tuple[int, int]:
    """Choose a small relative prefix displacement using bounded content samples."""
    best: tuple[int, int, int, int] | None = None
    for delta in range(-MAX_ALIGNMENT, MAX_ALIGNMENT + 1):
        a_skip = max(0, -delta)
        t_skip = max(0, delta)
        overlap = min(len(anchor) - a_skip, len(target) - t_skip)
        if overlap <= 0:
            continue
        # Score at most 192 short blocks.  Full exact mismatches are constructed only
        # for the winning displacement; this keeps the structural search bounded.
        samples = min(192, max(1, overlap // 256))
        stride = max(1, overlap // samples)
        mismatched_blocks = 0
        compared = 0
        pos = 0
        while pos < overlap and compared < samples:
            width = min(32, overlap - pos)
            if anchor[a_skip + pos : a_skip + pos + width] != target[t_skip + pos : t_skip + pos + width]:
                mismatched_blocks += 1
            compared += 1
            pos += stride
        unaligned = a_skip + t_skip + (len(anchor) - a_skip - overlap) + (len(target) - t_skip - overlap)
        score = (mismatched_blocks, unaligned, abs(delta), delta)
        if best is None or score < best:
            best = score
    if best is None:
        raise RuntimeError("no bounded alignment")
    delta = best[3]
    return max(0, -delta), max(0, delta)


def _patch(anchor: bytes, target: bytes) -> bytes:
    a_skip, t_skip = _alignment(anchor, target)
    overlap = min(len(anchor) - a_skip, len(target) - t_skip)
    prefix = target[:t_skip]
    suffix = target[t_skip + overlap :]

    mismatches: list[tuple[int, int]] = []
    # Equal 64 KiB blocks are rejected in C by bytes comparison; only differing blocks
    # pay the Python byte scan.  The hostile Shifted family is intentionally sparse.
    block = 64 * 1024
    for start in range(0, overlap, block):
        end = min(overlap, start + block)
        aa = anchor[a_skip + start : a_skip + end]
        tt = target[t_skip + start : t_skip + end]
        if aa == tt:
            continue
        mismatches.extend((start + j, tv) for j, (av, tv) in enumerate(zip(aa, tt)) if av != tv)

    out = bytearray()
    out += _u32(a_skip) + _u32(len(prefix)) + prefix + _u64(overlap)
    out += _u32(len(mismatches))
    previous = 0
    for i, (pos, value) in enumerate(mismatches):
        delta = pos if i == 0 else pos - previous
        out += _u32(delta) + bytes([value])
        previous = pos
    out += _u32(len(suffix)) + suffix
    return bytes(out)


def _apply_patch(anchor: bytes, patch: bytes, expected_size: int) -> bytes:
    raw = memoryview(patch)
    off = 0
    a_skip, off = _read_u32(raw, off)
    plen, off = _read_u32(raw, off)
    if off + plen > len(raw):
        raise RuntimeError("truncated joint-edit prefix")
    prefix = bytes(raw[off : off + plen]); off += plen
    overlap, off = _read_u64(raw, off)
    if a_skip + overlap > len(anchor):
        raise RuntimeError("joint-edit anchor range outside anchor")
    count, off = _read_u32(raw, off)
    body = bytearray(anchor[a_skip : a_skip + overlap])
    pos = 0
    for i in range(count):
        delta, off = _read_u32(raw, off)
        pos = delta if i == 0 else pos + delta
        if pos >= len(body) or off >= len(raw):
            raise RuntimeError("joint-edit substitution outside overlap")
        body[pos] = int(raw[off]); off += 1
    slen, off = _read_u32(raw, off)
    if off + slen != len(raw):
        raise RuntimeError("truncated or trailing joint-edit suffix")
    suffix = bytes(raw[off : off + slen])
    decoded = prefix + bytes(body) + suffix
    if len(decoded) != expected_size:
        raise RuntimeError("joint-edit reconstructed size mismatch")
    return decoded


def _transform(rows: list[tuple[str, bytes]], anchor_i: int) -> tuple[bytes, dict]:
    anchor = rows[anchor_i][1]
    out = bytearray(TRANSFORM_MAGIC)
    out += _u32(anchor_i) + _u64(len(anchor)) + anchor + _u32(len(rows) - 1)
    patch_raw_total = 0
    mismatch_program_total = 0
    for i, (_name, target) in enumerate(rows):
        if i == anchor_i:
            continue
        patch = _patch(anchor, target)
        reconstructed = _apply_patch(anchor, patch, len(target))
        if reconstructed != target:
            raise RuntimeError("joint-edit construction failed exact roundtrip")
        out += _u32(i) + _u64(len(patch)) + patch
        patch_raw_total += len(target)
        mismatch_program_total += len(patch)
    return bytes(out), {
        "anchor_raw_bytes": len(anchor),
        "patch_target_raw_total": patch_raw_total,
        "edit_program_total_bytes": mismatch_program_total,
    }


def _decode_transform(raw: bytes, rows_meta: list[tuple[str, int, bytes]]) -> list[bytes]:
    view = memoryview(raw)
    if bytes(view[: len(TRANSFORM_MAGIC)]) != TRANSFORM_MAGIC:
        raise RuntimeError("bad joint-edit transform magic")
    off = len(TRANSFORM_MAGIC)
    anchor_i, off = _read_u32(view, off)
    anchor_len, off = _read_u64(view, off)
    if anchor_i >= len(rows_meta) or off + anchor_len > len(view):
        raise RuntimeError("invalid joint-edit transform anchor")
    anchor = bytes(view[off : off + anchor_len]); off += anchor_len
    patch_count, off = _read_u32(view, off)
    if patch_count != len(rows_meta) - 1:
        raise RuntimeError("invalid joint-edit patch count")
    decoded: list[bytes | None] = [None] * len(rows_meta)
    decoded[anchor_i] = anchor
    seen: set[int] = set()
    for _ in range(patch_count):
        idx, off = _read_u32(view, off)
        plen, off = _read_u64(view, off)
        if idx >= len(rows_meta) or idx == anchor_i or idx in seen or off + plen > len(view):
            raise RuntimeError("invalid joint-edit patch ownership")
        patch = bytes(view[off : off + plen]); off += plen
        decoded[idx] = _apply_patch(anchor, patch, rows_meta[idx][1])
        seen.add(idx)
    if off != len(view) or any(item is None for item in decoded):
        raise RuntimeError("trailing or incomplete joint-edit transform")
    return [item for item in decoded if item is not None]


def _zstd_blob(exe: str, raw: bytes, level: int, work: Path) -> bytes:
    src = work / "transform.raw"
    dst = work / "transform.zst"
    src.write_bytes(raw)
    subprocess.run([exe, f"-{level}", "-q", "-f", str(src), "-o", str(dst)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return dst.read_bytes()


def build(root: Path, artifact: Path, *, level: int, work: Path) -> dict:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI required")
    started = time.perf_counter()
    rows = [(p.relative_to(root).as_posix(), p.read_bytes()) for p in _files(root)]
    anchor_i = _anchor(rows)
    transform, stats = _transform(rows, anchor_i)
    if len(transform) > MAX_DECODE_UNIT:
        raise RuntimeError("joint-edit transform exceeds 8 MiB decode-unit law")
    blob = _zstd_blob(exe, transform, level, work)

    out = bytearray(MAGIC)
    out += _u32(len(rows)) + _u32(anchor_i) + _u32(level) + _u64(len(transform)) + _u64(len(blob))
    for name, member in rows:
        name_raw = name.encode("utf-8")
        out += _u32(len(name_raw)) + name_raw + _u64(len(member)) + hashlib.sha256(member).digest()
    out += blob
    artifact.write_bytes(out)
    elapsed = time.perf_counter() - started
    min_member = min(len(raw) for _, raw in rows)
    locality = len(transform) / max(1, min_member)
    return {
        **stats,
        "anchor_index": anchor_i,
        "transform_raw_bytes": len(transform),
        "transform_zstd_bytes": len(blob),
        "archive_bytes": len(out),
        "create_s": elapsed,
        "artifact_sha256": hashlib.sha256(out).hexdigest(),
        "max_decode_unit_bytes": len(transform),
        "max_locality_amplification": locality,
    }


def extract(artifact: Path, output: Path, *, work: Path) -> None:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI required")
    view = memoryview(artifact.read_bytes())
    if bytes(view[: len(MAGIC)]) != MAGIC:
        raise RuntimeError("bad joint-edit artifact magic")
    off = len(MAGIC)
    count, off = _read_u32(view, off)
    anchor_i, off = _read_u32(view, off)
    _level, off = _read_u32(view, off)
    transform_len, off = _read_u64(view, off)
    blob_len, off = _read_u64(view, off)
    if not count or anchor_i >= count or transform_len > MAX_DECODE_UNIT:
        raise RuntimeError("invalid joint-edit artifact header")
    meta: list[tuple[str, int, bytes]] = []
    seen_names: set[str] = set()
    for _ in range(count):
        nlen, off = _read_u32(view, off)
        if not nlen or off + nlen > len(view):
            raise RuntimeError("invalid joint-edit path")
        name = bytes(view[off : off + nlen]).decode("utf-8"); off += nlen
        if name.startswith("/") or ".." in Path(name).parts or name in seen_names:
            raise RuntimeError("unsafe or duplicate joint-edit path")
        seen_names.add(name)
        size, off = _read_u64(view, off)
        if off + 32 > len(view):
            raise RuntimeError("truncated joint-edit digest")
        digest = bytes(view[off : off + 32]); off += 32
        meta.append((name, size, digest))
    if off + blob_len != len(view):
        raise RuntimeError("truncated or trailing joint-edit compressed stream")
    blob = bytes(view[off : off + blob_len])
    zst = work / "transform.zst"; raw_path = work / "transform.raw"
    zst.write_bytes(blob)
    subprocess.run([exe, "-d", "-q", "-f", str(zst), "-o", str(raw_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    transform = raw_path.read_bytes()
    if len(transform) != transform_len:
        raise RuntimeError("joint-edit transform length mismatch")
    decoded = _decode_transform(transform, meta)
    output.mkdir(parents=True, exist_ok=True)
    for (name, size, digest), member in zip(meta, decoded):
        if len(member) != size or hashlib.sha256(member).digest() != digest:
            raise RuntimeError(f"joint-edit member integrity mismatch: {name}")
        dst = output.joinpath(*Path(name).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(member)


def _self_test() -> None:
    anchor = b"abcdefgh" * 1024
    target = b"XYZ" + bytearray(anchor)
    target = bytearray(target)
    target[123] ^= 0x5A
    target = bytes(target) + b"tail"
    patch = _patch(anchor, target)
    assert _apply_patch(anchor, patch, len(target)) == target
    try:
        _apply_patch(anchor, patch + b"x", len(target))
    except RuntimeError:
        pass
    else:
        raise AssertionError("joint-edit parser accepted trailing patch bytes")


def run(work_root: Path) -> dict:
    _self_test()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    HOSTILE.shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)
    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    if expected_tree != accepted["tree_sha256"]:
        raise RuntimeError("Shifted corpus tree drift")

    normalized_parent = work_root / "normalized"; normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")

    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zw = work_root / "solid-zstd-work"; zw.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zw)
    if not zstd_result.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable")

    accepted_bytes = int(accepted["accepted_v029_bytes"])
    arms = []
    for level in LEVELS:
        arm_work = work_root / f"joint-l{level}"; arm_work.mkdir()
        artifact = work_root / f"joint-l{level}.cmpct-oracle"
        result = build(stage, artifact, level=level, work=arm_work)
        out = work_root / f"joint-out-l{level}"
        decode_work = work_root / f"joint-decode-l{level}"; decode_work.mkdir()
        extract(artifact, out, work=decode_work)
        tree = CMPCT.treehash(out)
        strict = {
            "beats_v029_size": result["archive_bytes"] < accepted_bytes,
            "beats_zip_size": result["archive_bytes"] < int(zip_result["archive_bytes"]),
            "beats_zstd19_size": result["archive_bytes"] < int(zstd_result["archive_bytes"]),
            "beats_zip_create": result["create_s"] < float(zip_result["create_s"]),
            "beats_zstd19_create": result["create_s"] < float(zstd_result["create_s"]),
            "locality_le_8x": result["max_locality_amplification"] <= MAX_LOCALITY,
            "decode_unit_le_8mib": result["max_decode_unit_bytes"] <= MAX_DECODE_UNIT,
        }
        strict["seven_way_win"] = all(strict.values())
        row = {"level": level, **result, "tree_sha256": tree, "tree_verified": tree == expected_tree, "strict": strict}
        arms.append(row)
        print(json.dumps({"level": level, "archive_bytes": result["archive_bytes"], "create_s": result["create_s"], "strict": strict}, separators=(",", ":")), flush=True)

    best = min(arms, key=lambda a: (a["archive_bytes"], a["create_s"], a["level"]))
    winners = [a for a in arms if a["tree_verified"] and a["strict"]["seven_way_win"]]
    size_winners = [a for a in arms if a["tree_verified"] and a["strict"]["beats_zstd19_size"] and a["strict"]["beats_zip_size"] and a["strict"]["beats_v029_size"]]
    decision = "PROMOTE_NEXT_PREREQUISITE" if size_winners else "RETIRE_FAMILY"
    return {
        "schema": "cmpct-v030-shifted-joint-edit-stream-oracle-v1",
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "source_commit": subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(),
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "research_only": True,
            "release_credit": False,
            "creation_includes_scan_selection_alignment_edit_build_compression_framing_hash_publication": True,
            "single_joint_transformed_decode_unit": True,
        },
        "tree_sha256": expected_tree,
        "accepted_v029_bytes": accepted_bytes,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "arms": arms,
        "summary": {
            "strict_seven_way_wins": len(winners),
            "winning_levels": [a["level"] for a in winners],
            "size_winning_levels": [a["level"] for a in size_winners],
            "best_level": best["level"],
            "best_bytes": best["archive_bytes"],
            "best_zstd_gap_bytes": best["archive_bytes"] - int(zstd_result["archive_bytes"]),
            "best_v029_gap_bytes": best["archive_bytes"] - accepted_bytes,
            "promotion_signal": bool(size_winners),
            "release_credit": False,
        },
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "saturation_triggers": ["S2", "S3", "S4"],
            "research_priority_score": 98,
            "pre_mortem": "Joint coding can still lose if one-anchor entropy or transform framing exceeds the narrow Zstd gap; creation search and all edit construction must remain inside timing.",
            "builder": "Encode one structural anchor plus exact bounded-alignment sparse edits and compress the transformed representation jointly across six levels.",
            "hostile_review": "A payload-size win is not product proof: generic admission, canonical semantics, recovery, native/Android parity and exact all-15 authority remain mandatory, and level audition cost cannot be hidden in a selector.",
            "measured_gap_change_bytes": int(zstd_result["archive_bytes"]) - int(best["archive_bytes"]),
            "terminal_decision": decision,
            "next_decisive_test": "If size-positive, freeze one content-agnostic level/admission rule and measure single-pass creation against ZIP and Zstd without multi-arm audition; otherwise retire joint one-anchor edit-stream ownership.",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
