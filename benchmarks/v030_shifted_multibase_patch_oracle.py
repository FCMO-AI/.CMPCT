from __future__ import annotations

"""R4 Shifted bounded multi-base + patch oracle.

Research-only decisive instrument for the D4/S1 Shifted red. The retired single-anchor
family has a proven optimistic payload floor above solid Zstd-19, so this experiment
changes physical ownership: several deterministic structural bases may coexist and a
member may reference whichever admissible base yields the smallest exact patch.

The representation is content-agnostic. It never reads benchmark names/hashes for
selection. Creation time includes source observation, base selection, every direct
compression, every patch construction, framing, hashing and publication. Every member
retains a direct Zstd-19 fallback and a derived member is admitted only when its decoded
context amplification is <=8x. The complete artifact must round-trip exactly.
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

MAGIC = b"C30MBP1\0"
BASE_COUNTS = (2, 3, 4)
PATCH_LEVEL = 1
MAX_CONTEXT_AMPLIFICATION = 8.0


def _u32(n: int) -> bytes:
    return struct.pack("<I", n)


def _u64(n: int) -> bytes:
    return struct.pack("<Q", n)


def _ru32(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 4 > len(raw):
        raise RuntimeError("truncated multibase u32")
    return struct.unpack_from("<I", raw, off)[0], off + 4


def _ru64(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 8 > len(raw):
        raise RuntimeError("truncated multibase u64")
    return struct.unpack_from("<Q", raw, off)[0], off + 8


def _files(root: Path) -> list[Path]:
    rows = sorted(p for p in root.rglob("*") if p.is_file())
    if len(rows) < 2:
        raise RuntimeError("multibase oracle requires at least two regular files")
    if any(p.is_symlink() for p in rows):
        raise RuntimeError("multibase oracle does not accept symlinks")
    return rows


def _anchors(rows: list[tuple[str, bytes]], count: int) -> list[int]:
    """Deterministic size-quantile bases, tie-broken by content then path."""
    if count < 2 or count > len(rows):
        raise RuntimeError("invalid base count")
    ranked = sorted(
        range(len(rows)),
        key=lambda i: (len(rows[i][1]), hashlib.sha256(rows[i][1]).digest(), rows[i][0]),
    )
    if count == len(rows):
        return sorted(ranked)
    chosen: list[int] = []
    for j in range(count):
        pos = round(j * (len(ranked) - 1) / (count - 1))
        idx = ranked[pos]
        if idx not in chosen:
            chosen.append(idx)
    if len(chosen) != count:
        raise RuntimeError("base quantile selection collapsed")
    return sorted(chosen)


def _zstd(exe: str, args: list[str]) -> None:
    subprocess.run([exe, *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def build(root: Path, artifact: Path, *, base_count: int, work: Path) -> dict:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI is required")
    started = time.perf_counter()
    rows = [(p.relative_to(root).as_posix(), p.read_bytes()) for p in _files(root)]
    base_ids = _anchors(rows, base_count)
    base_set = set(base_ids)

    raw_paths: list[Path] = []
    direct_blobs: list[bytes] = []
    for i, (_name, raw) in enumerate(rows):
        src = work / f"member-{i:03d}.raw"
        src.write_bytes(raw)
        raw_paths.append(src)
        direct = work / f"member-{i:03d}.direct.zst"
        _zstd(exe, ["-19", "-q", "-f", str(src), "-o", str(direct)])
        direct_blobs.append(direct.read_bytes())

    encoded: list[tuple[str, int, bytes, int, int, bytes]] = []
    patch_attempts = 0
    patch_source_bytes = 0
    admitted_patches = 0
    max_context_amp = 1.0

    for i, (name, raw) in enumerate(rows):
        digest = hashlib.sha256(raw).digest()
        best_kind = 0  # 0 = direct zstd, 1 = patch
        best_base = i
        best_blob = direct_blobs[i]
        best_amp = 1.0
        if i not in base_set:
            for base_i in base_ids:
                base_raw = rows[base_i][1]
                amp = (len(base_raw) + len(raw)) / max(1, len(raw))
                if amp > MAX_CONTEXT_AMPLIFICATION:
                    continue
                patch_attempts += 1
                patch_source_bytes += len(raw)
                patch = work / f"member-{i:03d}-base-{base_i:03d}.patch.zst"
                _zstd(
                    exe,
                    [f"-{PATCH_LEVEL}", "--patch-from", str(raw_paths[base_i]), "-q", "-f", str(raw_paths[i]), "-o", str(patch)],
                )
                blob = patch.read_bytes()
                if len(blob) < len(best_blob):
                    best_kind, best_base, best_blob, best_amp = 1, base_i, blob, amp
        if best_kind == 1:
            admitted_patches += 1
            max_context_amp = max(max_context_amp, best_amp)
        encoded.append((name, len(raw), digest, best_kind, best_base, best_blob))

    out = bytearray(MAGIC)
    out += _u32(len(encoded)) + _u32(base_count) + _u32(PATCH_LEVEL)
    for base_i in base_ids:
        out += _u32(base_i)
    for name, raw_size, digest, kind, base_i, blob in encoded:
        name_raw = name.encode("utf-8")
        out += _u32(len(name_raw)) + name_raw
        out += bytes([kind]) + _u32(base_i) + _u64(raw_size) + digest + _u64(len(blob)) + blob
    artifact.write_bytes(out)
    return {
        "archive_bytes": len(out),
        "create_s": time.perf_counter() - started,
        "base_count": base_count,
        "base_indices": base_ids,
        "base_names": [rows[i][0] for i in base_ids],
        "patch_attempts": patch_attempts,
        "patch_source_bytes": patch_source_bytes,
        "admitted_patches": admitted_patches,
        "max_context_amplification": max_context_amp,
        "artifact_sha256": hashlib.sha256(out).hexdigest(),
    }


def extract(artifact: Path, output: Path, *, work: Path) -> None:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI is required")
    raw = memoryview(artifact.read_bytes())
    if bytes(raw[: len(MAGIC)]) != MAGIC:
        raise RuntimeError("bad multibase magic")
    off = len(MAGIC)
    count, off = _ru32(raw, off)
    base_count, off = _ru32(raw, off)
    _patch_level, off = _ru32(raw, off)
    if not count or base_count < 2 or base_count > count:
        raise RuntimeError("invalid multibase header")
    base_ids = []
    for _ in range(base_count):
        base_i, off = _ru32(raw, off)
        if base_i >= count or base_i in base_ids:
            raise RuntimeError("invalid multibase base table")
        base_ids.append(base_i)
    entries = []
    for _ in range(count):
        nlen, off = _ru32(raw, off)
        if not nlen or off + nlen > len(raw):
            raise RuntimeError("invalid multibase path")
        name = bytes(raw[off : off + nlen]).decode("utf-8"); off += nlen
        if off >= len(raw):
            raise RuntimeError("truncated multibase kind")
        kind = int(raw[off]); off += 1
        base_i, off = _ru32(raw, off)
        size, off = _ru64(raw, off)
        if off + 32 > len(raw):
            raise RuntimeError("truncated multibase sha")
        digest = bytes(raw[off : off + 32]); off += 32
        blen, off = _ru64(raw, off)
        if off + blen > len(raw):
            raise RuntimeError("truncated multibase payload")
        blob = bytes(raw[off : off + blen]); off += blen
        entries.append((name, kind, base_i, size, digest, blob))
    if off != len(raw):
        raise RuntimeError("trailing multibase bytes")

    output.mkdir(parents=True, exist_ok=True)
    decoded_bases: dict[int, tuple[Path, bytes]] = {}
    for base_i in base_ids:
        name, kind, owner, size, digest, blob = entries[base_i]
        if kind != 0 or owner != base_i:
            raise RuntimeError("base must be directly owned")
        zst = work / f"base-{base_i:03d}.zst"; dst = work / f"base-{base_i:03d}.raw"
        zst.write_bytes(blob)
        _zstd(exe, ["-d", "-q", "-f", str(zst), "-o", str(dst)])
        data = dst.read_bytes()
        if len(data) != size or hashlib.sha256(data).digest() != digest:
            raise RuntimeError("base integrity mismatch")
        decoded_bases[base_i] = (dst, data)

    for i, (name, kind, base_i, size, digest, blob) in enumerate(entries):
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError("unsafe multibase path")
        if kind == 0:
            zst = work / f"direct-{i:03d}.zst"; dst_tmp = work / f"direct-{i:03d}.raw"
            zst.write_bytes(blob)
            _zstd(exe, ["-d", "-q", "-f", str(zst), "-o", str(dst_tmp)])
            decoded = dst_tmp.read_bytes()
        elif kind == 1:
            if base_i not in decoded_bases:
                raise RuntimeError("patch references non-base member")
            patch = work / f"patch-{i:03d}.zst"; dst_tmp = work / f"patch-{i:03d}.raw"
            patch.write_bytes(blob)
            _zstd(exe, ["-d", "--patch-from", str(decoded_bases[base_i][0]), "-q", "-f", str(patch), "-o", str(dst_tmp)])
            decoded = dst_tmp.read_bytes()
        else:
            raise RuntimeError("invalid multibase member kind")
        if len(decoded) != size or hashlib.sha256(decoded).digest() != digest:
            raise RuntimeError(f"member integrity mismatch: {name}")
        dst = output.joinpath(*Path(name).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(decoded)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    HOSTILE.shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)
    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    if expected_tree != accepted["tree_sha256"]:
        raise RuntimeError("Shifted corpus tree drift")

    normalized_parent = work_root / "normalized-parent"; normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")

    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_result.get("available"):
        raise RuntimeError("solid zstd-19 comparator unavailable")
    v029 = int(accepted["accepted_v029_bytes"])

    arms = []
    for base_count in BASE_COUNTS:
        arm_work = work_root / f"multibase-k{base_count}"; arm_work.mkdir()
        artifact = work_root / f"shifted-multibase-k{base_count}.cmpct-oracle"
        r = build(stage, artifact, base_count=base_count, work=arm_work)
        out = work_root / f"out-k{base_count}"; decode_work = work_root / f"decode-k{base_count}"; decode_work.mkdir()
        extract(artifact, out, work=decode_work)
        tree = CMPCT.treehash(out)
        strict = {
            "beats_v029_size": r["archive_bytes"] < v029,
            "beats_zip_size": r["archive_bytes"] < int(zip_result["archive_bytes"]),
            "beats_zstd19_size": r["archive_bytes"] < int(zstd_result["archive_bytes"]),
            "beats_zip_create": r["create_s"] < float(zip_result["create_s"]),
            "beats_zstd19_create": r["create_s"] < float(zstd_result["create_s"]),
            "locality_le_8x": r["max_context_amplification"] <= MAX_CONTEXT_AMPLIFICATION,
        }
        strict["six_way_win"] = all(strict.values())
        arms.append({**r, "tree_sha256": tree, "tree_verified": tree == expected_tree, "strict": strict})
        print(json.dumps({"base_count": base_count, "archive_bytes": r["archive_bytes"], "create_s": r["create_s"], "admitted_patches": r["admitted_patches"], "strict": strict}, separators=(",", ":")), flush=True)

    best = min(arms, key=lambda a: (a["archive_bytes"], a["create_s"], a["base_count"]))
    winners = [a for a in arms if a["tree_verified"] and a["strict"]["six_way_win"]]
    return {
        "schema": "cmpct-v030-shifted-multibase-patch-oracle-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation": ["S1", "S3"],
        "rps": 91,
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "single_complete_artifact": True,
            "direct_zstd19_fallback_per_member": True,
            "max_context_amplification": MAX_CONTEXT_AMPLIFICATION,
            "creation_prices_all_patch_attempts": True,
            "research_only": True,
            "release_credit": False,
        },
        "tree_sha256": expected_tree,
        "accepted_v029_bytes": v029,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "arms": arms,
        "summary": {
            "strict_wins": len(winners),
            "winning_base_counts": [a["base_count"] for a in winners],
            "best_size_base_count": best["base_count"],
            "best_size_bytes": best["archive_bytes"],
            "best_size_zstd_gap_bytes": best["archive_bytes"] - int(zstd_result["archive_bytes"]),
            "promotion_signal": bool(winners),
            "terminal_decision_if_no_size_win": "RETIRE_FAMILY",
            "terminal_decision_if_size_win_but_time_loss": "REHABILITATE_DEBT",
            "terminal_decision_if_strict_win": "PROMOTE_NEXT_PREREQUISITE",
            "release_credit": False,
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
