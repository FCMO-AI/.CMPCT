from __future__ import annotations

"""Reversible ZIP canonicalization oracle for the v0.30 deflate-family gap.

This is research evidence only. It asks whether already-compressed ZIP payloads can be normalized into their
member contents, compressed across bundles, and reconstructed byte-for-byte. A ZIP is admitted only when this
process proves exact byte reconstruction using Python's deterministic ZIP writer; otherwise it is rejected and
cannot contribute a claimed win.

The candidate is intentionally charged for source scan, ZIP parse, bounded compression-level discovery,
metadata serialization, outer Zstd compression, archive write, decode, and exact-tree verification. It may not
satisfy release authority or change canonical r24/r25 bytes without a separate productization + portability pass.
"""

import argparse
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile
import time
import zipfile

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT

MAGIC = b"ZR01"
LEVELS = (1, 3, 6, 9, 12, 15, 19)
ZIP_LEVELS = (6, 9, 3, 1, 2, 4, 5, 7, 8)


def _write_u32(buf: io.BytesIO, value: int) -> None:
    buf.write(struct.pack("<I", value))


def _write_bytes(buf: io.BytesIO, raw: bytes) -> None:
    _write_u32(buf, len(raw)); buf.write(raw)


def _rebuild_zip(entries: list[dict], level: int) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        for e in entries:
            info = zipfile.ZipInfo(e["name"], date_time=tuple(e["date_time"]))
            info.compress_type = int(e["compress_type"])
            info.comment = bytes.fromhex(e["comment_hex"])
            info.extra = bytes.fromhex(e["extra_hex"])
            info.internal_attr = int(e["internal_attr"])
            info.external_attr = int(e["external_attr"])
            info.create_system = int(e["create_system"])
            info.flag_bits = int(e["flag_bits"])
            zf.writestr(info, e["data"], compress_type=info.compress_type, compresslevel=level)
        zf.comment = bytes.fromhex(entries[0]["archive_comment_hex"]) if entries else b""
    return out.getvalue()


def _normalize_zip(path: Path) -> tuple[dict | None, float]:
    started = time.perf_counter()
    original = path.read_bytes()
    try:
        with zipfile.ZipFile(io.BytesIO(original), "r") as zf:
            archive_comment = zf.comment.hex()
            entries = []
            for info in zf.infolist():
                if info.is_dir():
                    return None, time.perf_counter() - started
                entries.append({
                    "name": info.filename,
                    "date_time": list(info.date_time),
                    "compress_type": info.compress_type,
                    "comment_hex": info.comment.hex(),
                    "extra_hex": info.extra.hex(),
                    "internal_attr": info.internal_attr,
                    "external_attr": info.external_attr,
                    "create_system": info.create_system,
                    "flag_bits": info.flag_bits,
                    "archive_comment_hex": archive_comment,
                    "data": zf.read(info.filename),
                })
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return None, time.perf_counter() - started

    found = None
    for level in ZIP_LEVELS:
        rebuilt = _rebuild_zip(entries, level)
        if rebuilt == original:
            found = level
            break
    if found is None:
        return None, time.perf_counter() - started
    return {"level": found, "entries": entries, "original_bytes": len(original)}, time.perf_counter() - started


def _serialize(root: Path) -> tuple[bytes | None, dict, float]:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.suffix.lower() != ".zip" for p in files):
        return None, {"reason": "not-all-zip"}, time.perf_counter() - started
    normalized = []
    discovery_s = 0.0
    for path in files:
        item, elapsed = _normalize_zip(path); discovery_s += elapsed
        if item is None:
            return None, {"reason": f"non-reproducible-zip:{path.name}", "discovery_s": discovery_s}, time.perf_counter() - started
        normalized.append((path.relative_to(root).as_posix(), item))

    buf = io.BytesIO(); buf.write(MAGIC); _write_u32(buf, len(normalized))
    for rel, item in normalized:
        _write_bytes(buf, rel.encode("utf-8")); _write_u32(buf, item["level"]); _write_u32(buf, len(item["entries"]))
        archive_comment = bytes.fromhex(item["entries"][0]["archive_comment_hex"]) if item["entries"] else b""
        _write_bytes(buf, archive_comment)
        for e in item["entries"]:
            _write_bytes(buf, e["name"].encode("utf-8"))
            for v in e["date_time"]: buf.write(struct.pack("<H", v))
            buf.write(struct.pack("<HIIIB", e["compress_type"], e["internal_attr"], e["external_attr"], e["create_system"], e["flag_bits"] & 0xFF))
            _write_bytes(buf, bytes.fromhex(e["comment_hex"])); _write_bytes(buf, bytes.fromhex(e["extra_hex"])); _write_bytes(buf, e["data"])
    elapsed = time.perf_counter() - started
    return buf.getvalue(), {"zip_files": len(normalized), "discovery_s": discovery_s}, elapsed


def _read_u32(raw: memoryview, at: int) -> tuple[int, int]:
    return struct.unpack_from("<I", raw, at)[0], at + 4


def _read_bytes(raw: memoryview, at: int) -> tuple[bytes, int]:
    n, at = _read_u32(raw, at); return bytes(raw[at:at+n]), at + n


def _restore(serialized: bytes, out: Path) -> None:
    raw = memoryview(serialized); at = 0
    if bytes(raw[:4]) != MAGIC: raise ValueError("bad magic")
    at = 4; count, at = _read_u32(raw, at)
    for _ in range(count):
        rel_b, at = _read_bytes(raw, at); level, at = _read_u32(raw, at); entry_count, at = _read_u32(raw, at); archive_comment, at = _read_bytes(raw, at)
        entries = []
        for _ in range(entry_count):
            name_b, at = _read_bytes(raw, at)
            date_time = list(struct.unpack_from("<6H", raw, at)); at += 12
            compress_type, internal_attr, external_attr, create_system, flag_bits = struct.unpack_from("<HIIIB", raw, at); at += struct.calcsize("<HIIIB")
            comment, at = _read_bytes(raw, at); extra, at = _read_bytes(raw, at); data, at = _read_bytes(raw, at)
            entries.append({"name": name_b.decode(), "date_time": date_time, "compress_type": compress_type, "comment_hex": comment.hex(), "extra_hex": extra.hex(), "internal_attr": internal_attr, "external_attr": external_attr, "create_system": create_system, "flag_bits": flag_bits, "archive_comment_hex": archive_comment.hex(), "data": data})
        target = out / rel_b.decode(); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(_rebuild_zip(entries, level))
    if at != len(raw): raise ValueError("trailing bytes")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); root = corpus / "04_deflate_family"
    expected_tree = CORPUS.tree_hash(root)
    with tempfile.TemporaryDirectory(prefix="cmpct-zr-", dir=work_root) as td:
        td = Path(td); stage = EXT._normalized_stage(root, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)
        serialized, normalize, normalization_s = _serialize(stage)
        candidates = []
        if serialized is not None:
            for level in LEVELS:
                archive = td / f"candidate-{level}.zst"
                started = time.perf_counter(); compressed = zstd.ZstdCompressor(level=level, threads=0).compress(serialized); archive.write_bytes(compressed); compression_s = time.perf_counter() - started
                create_s = normalization_s + compression_s
                decoded = zstd.ZstdDecompressor().decompress(archive.read_bytes())
                restored = td / f"restore-{level}"; restored.mkdir(); _restore(decoded, restored)
                tree_ok = CORPUS.tree_hash(restored) == expected_tree
                candidate = {"level": level, "archive_bytes": archive.stat().st_size, "normalization_s": normalization_s, "compression_write_s": compression_s, "create_s": create_s, "tree_verified": tree_ok}
                candidate.update({
                    "beats_zip_size": candidate["archive_bytes"] < zip_result["archive_bytes"],
                    "beats_zstd19_size": candidate["archive_bytes"] < zstd_result["archive_bytes"],
                    "beats_zip_create": candidate["create_s"] < zip_result["create_s"],
                    "beats_zstd19_create": candidate["create_s"] < zstd_result["create_s"],
                })
                candidate["viable"] = tree_ok and all(candidate[k] for k in ("beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"))
                candidates.append(candidate)
        viable = [c for c in candidates if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"])) if viable else None
        return {
            "schema": "cmpct-v030-zip-reinflate-oracle-v1",
            "claim_boundary": "research-only reversible transform; cannot authorize canonical r25 without product/native/Android integration",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "tree_sha256": expected_tree,
            "normalization": normalize,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_candidate": best,
            "gate": {"exact_tree_reconstructed": bool(candidates) and all(c["tree_verified"] for c in candidates), "four_way_win_found": best is not None, "passed": bool(candidates) and all(c["tree_verified"] for c in candidates)},
        }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zip-reinflate-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zip-reinflate.json")); a = p.parse_args()
    result = run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n"); print(json.dumps({"viable_candidate": result["viable_candidate"], "gate": result["gate"]}, indent=2))
    if not result["gate"]["passed"]: raise SystemExit("ZIP reinflate oracle correctness gate failed")


if __name__ == "__main__": main()
