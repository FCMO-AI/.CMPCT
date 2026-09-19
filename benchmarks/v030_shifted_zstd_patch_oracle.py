from __future__ import annotations

"""R4 Shifted-versions base+patch representation oracle.

This is deliberately research-only.  It tests a representation family that is materially different from
PrefixGraph, shared dictionaries, and solid cluster ownership: one deterministic structural anchor is stored once,
and every other regular member is represented as a native Zstd patch from that anchor.

The oracle charges source scanning, anchor selection, base compression, every patch construction, framing,
hashing, and final publication inside candidate creation time.  It emits one complete self-describing artifact,
reconstructs every member through the reciprocal native patch decoder, and requires exact logical-tree identity.
No benchmark identity is consulted by the representation itself.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_authoritative as CMPCT

MAGIC = b"C30BP1\0"
LEVELS = (1, 3, 6, 9)


def _u32(n: int) -> bytes:
    return struct.pack("<I", n)


def _u64(n: int) -> bytes:
    return struct.pack("<Q", n)


def _read_u32(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 4 > len(raw):
        raise RuntimeError("truncated base-patch u32")
    return struct.unpack_from("<I", raw, off)[0], off + 4


def _read_u64(raw: memoryview, off: int) -> tuple[int, int]:
    if off + 8 > len(raw):
        raise RuntimeError("truncated base-patch u64")
    return struct.unpack_from("<Q", raw, off)[0], off + 8


def _files(root: Path) -> list[Path]:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError("base-patch oracle requires at least one regular file")
    if any(p.is_symlink() for p in files):
        raise RuntimeError("base-patch oracle does not accept symlinks")
    return files


def _anchor(rows: list[tuple[str, bytes]]) -> int:
    # Structural and deterministic: closest raw size to the median, then content SHA, then relative path.
    sizes = sorted(len(raw) for _, raw in rows)
    median = sizes[len(sizes) // 2]
    ranked = sorted(
        range(len(rows)),
        key=lambda i: (abs(len(rows[i][1]) - median), hashlib.sha256(rows[i][1]).digest(), rows[i][0]),
    )
    return ranked[0]


def _zstd(exe: str, args: list[str]) -> None:
    subprocess.run([exe, *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def build(root: Path, artifact: Path, *, patch_level: int, work: Path) -> dict:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI is required")
    if patch_level not in LEVELS:
        raise RuntimeError("unsupported patch level")

    started = time.perf_counter()
    rows = [(p.relative_to(root).as_posix(), p.read_bytes()) for p in _files(root)]
    anchor_i = _anchor(rows)
    anchor_name, anchor_raw = rows[anchor_i]
    anchor_sha = hashlib.sha256(anchor_raw).digest()

    anchor_src = work / "anchor.raw"
    anchor_src.write_bytes(anchor_raw)
    anchor_zst = work / "anchor.zst"
    _zstd(exe, ["-19", "-q", "-f", str(anchor_src), "-o", str(anchor_zst)])
    anchor_blob = anchor_zst.read_bytes()

    encoded: list[tuple[str, int, bytes, int, bytes]] = []
    patch_raw_total = 0
    patch_blob_total = 0
    for i, (name, raw) in enumerate(rows):
        digest = hashlib.sha256(raw).digest()
        if i == anchor_i:
            blob = anchor_blob
            kind = 0
        else:
            src = work / f"target-{i:03d}.raw"
            patch = work / f"target-{i:03d}.patch.zst"
            src.write_bytes(raw)
            _zstd(
                exe,
                [f"-{patch_level}", "--patch-from", str(anchor_src), "-q", "-f", str(src), "-o", str(patch)],
            )
            blob = patch.read_bytes()
            kind = 1
            patch_raw_total += len(raw)
            patch_blob_total += len(blob)
        encoded.append((name, len(raw), digest, kind, blob))

    out = bytearray(MAGIC)
    out += _u32(len(encoded)) + _u32(anchor_i) + _u32(patch_level)
    for name, raw_size, digest, kind, blob in encoded:
        name_raw = name.encode("utf-8")
        out += _u32(len(name_raw)) + name_raw
        out += bytes([kind]) + _u64(raw_size) + digest + _u64(len(blob)) + blob
    artifact.write_bytes(out)
    create_s = time.perf_counter() - started
    return {
        "archive_bytes": len(out),
        "create_s": create_s,
        "anchor_index": anchor_i,
        "anchor_name": anchor_name,
        "anchor_raw_bytes": len(anchor_raw),
        "anchor_zstd19_bytes": len(anchor_blob),
        "patch_raw_total": patch_raw_total,
        "patch_blob_total": patch_blob_total,
        "artifact_sha256": hashlib.sha256(out).hexdigest(),
    }


def extract(artifact: Path, output: Path, *, work: Path) -> None:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI is required")
    raw = memoryview(artifact.read_bytes())
    if bytes(raw[: len(MAGIC)]) != MAGIC:
        raise RuntimeError("bad base-patch magic")
    off = len(MAGIC)
    count, off = _read_u32(raw, off)
    anchor_i, off = _read_u32(raw, off)
    _level, off = _read_u32(raw, off)
    if not count or anchor_i >= count:
        raise RuntimeError("invalid base-patch header")
    entries = []
    for _ in range(count):
        nlen, off = _read_u32(raw, off)
        if not nlen or off + nlen > len(raw):
            raise RuntimeError("invalid base-patch path")
        name = bytes(raw[off : off + nlen]).decode("utf-8")
        off += nlen
        if off >= len(raw):
            raise RuntimeError("truncated base-patch kind")
        kind = int(raw[off]); off += 1
        size, off = _read_u64(raw, off)
        if off + 32 > len(raw):
            raise RuntimeError("truncated base-patch sha")
        digest = bytes(raw[off : off + 32]); off += 32
        blen, off = _read_u64(raw, off)
        if off + blen > len(raw):
            raise RuntimeError("truncated base-patch payload")
        blob = bytes(raw[off : off + blen]); off += blen
        entries.append((name, kind, size, digest, blob))
    if off != len(raw):
        raise RuntimeError("trailing base-patch bytes")
    if entries[anchor_i][1] != 0 or sum(1 for e in entries if e[1] == 0) != 1:
        raise RuntimeError("invalid base-patch anchor ownership")

    output.mkdir(parents=True, exist_ok=True)
    anchor_blob = work / "decoded-anchor.zst"
    anchor_raw_path = work / "decoded-anchor.raw"
    anchor_blob.write_bytes(entries[anchor_i][4])
    _zstd(exe, ["-d", "-q", "-f", str(anchor_blob), "-o", str(anchor_raw_path)])
    anchor_raw = anchor_raw_path.read_bytes()

    for i, (name, kind, size, digest, blob) in enumerate(entries):
        if name.startswith("/") or ".." in Path(name).parts:
            raise RuntimeError("unsafe base-patch path")
        if i == anchor_i:
            decoded = anchor_raw
        else:
            if kind != 1:
                raise RuntimeError("invalid base-patch member kind")
            patch = work / f"decode-{i:03d}.patch.zst"
            target = work / f"decode-{i:03d}.raw"
            patch.write_bytes(blob)
            _zstd(
                exe,
                ["-d", "--patch-from", str(anchor_raw_path), "-q", "-f", str(patch), "-o", str(target)],
            )
            decoded = target.read_bytes()
        if len(decoded) != size or hashlib.sha256(decoded).digest() != digest:
            raise RuntimeError(f"base-patch member integrity mismatch: {name}")
        dst = output.joinpath(*Path(name).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(decoded)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    HOSTILE.shifted_versions(corpus.parent)
    source = corpus.parent / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)

    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    expected_accepted_tree = accepted["tree_sha256"]
    if expected_tree != expected_accepted_tree:
        raise RuntimeError("Shifted corpus tree drift")

    normalized_parent = work_root / "normalized-parent"
    normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")

    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_result.get("available"):
        raise RuntimeError("solid zstd-19 comparator unavailable")

    accepted_v029_bytes = int(accepted["accepted_v029_bytes"])
    arms = []
    for level in LEVELS:
        arm_work = work_root / f"patch-l{level}"; arm_work.mkdir()
        artifact = work_root / f"shifted-base-patch-l{level}.cmpct-oracle"
        result = build(stage, artifact, patch_level=level, work=arm_work)
        extracted = work_root / f"patch-out-l{level}"
        decode_work = work_root / f"patch-decode-l{level}"; decode_work.mkdir()
        extract(artifact, extracted, work=decode_work)
        tree = CMPCT.treehash(extracted)
        strict = {
            "beats_v029_size": result["archive_bytes"] < accepted_v029_bytes,
            "beats_zip_size": result["archive_bytes"] < int(zip_result["archive_bytes"]),
            "beats_zstd19_size": result["archive_bytes"] < int(zstd_result["archive_bytes"]),
            "beats_zip_create": result["create_s"] < float(zip_result["create_s"]),
            "beats_zstd19_create": result["create_s"] < float(zstd_result["create_s"]),
        }
        strict["five_way_win"] = all(strict.values())
        arms.append({"level": level, **result, "tree_sha256": tree, "tree_verified": tree == expected_tree, "strict": strict})
        print(json.dumps({"level": level, "archive_bytes": result["archive_bytes"], "create_s": result["create_s"], "strict": strict}, separators=(",", ":")), flush=True)

    winning = [arm for arm in arms if arm["tree_verified"] and arm["strict"]["five_way_win"]]
    best = min(arms, key=lambda a: (a["archive_bytes"], a["create_s"], a["level"]))
    return {
        "schema": "cmpct-v030-shifted-zstd-base-patch-oracle-v1",
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "single_complete_artifact": True,
            "creation_includes_source_scan_anchor_selection_patch_construction_framing_hashing_publication": True,
            "rounds": 1,
            "research_only": True,
            "release_credit": False,
        },
        "tree_sha256": expected_tree,
        "accepted_v029_bytes": accepted_v029_bytes,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "arms": arms,
        "summary": {
            "strict_five_way_wins": len(winning),
            "winning_levels": [a["level"] for a in winning],
            "best_size_level": best["level"],
            "best_size_bytes": best["archive_bytes"],
            "best_size_zstd_gap_bytes": best["archive_bytes"] - int(zstd_result["archive_bytes"]),
            "promotion_signal": bool(winning),
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
