from __future__ import annotations

"""Raw-DEFLATE segmented oracle for the v0.30 deflate-family frontier.

The earlier reversible ZIP reinflate experiment proved that normalizing ZIP members to plaintext can close the
size gap, but its inflate/recompress discovery cost is far too high to beat ZIP creation time.  This oracle asks a
narrower question: can CMPCT exploit cross-archive similarity *without inflating a single DEFLATE stream*?

Only a deliberately small ZIP subset is admitted: ordinary local-file headers, no encryption, no data descriptors,
and methods STORED/DEFLATE.  Each source ZIP is split into framing bytes plus the original compressed payloads.
Those exact bytes are serialized into independently-decodable groups and each group is Zstd-compressed.  Restore
concatenates the original framing and payload bytes, so successful candidates reproduce every input ZIP byte-for-byte.

This is research evidence only.  A candidate is interesting only when it simultaneously:
- restores the exact frozen logical tree;
- remains within <=8x decoded-context amplification and <=8 MiB decode units;
- is strictly smaller than deterministic ZIP/Deflate-9 and solid tar+Zstd-19;
- is strictly faster to create than both competitors, including source scan, ZIP parsing, serialization and writes.

No result from this file changes canonical r24/r25 bytes or release authority by itself.
"""

import argparse
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT

MAGIC = b"RDS1"
SEG_MAGIC = b"RSG1"
LOCAL = 0x04034B50
CENTRAL = 0x02014B50
EOCD = 0x06054B50
LEVELS = (1, 3, 6)
GROUP_SIZES = (2, 3, 4, 6)
MAX_AMP = 8.0
MAX_DECODE = 8 * 1024 * 1024


def _u32(buf: io.BytesIO, value: int) -> None:
    buf.write(struct.pack("<I", value))


def _blob(buf: io.BytesIO, raw: bytes) -> None:
    _u32(buf, len(raw)); buf.write(raw)


def _read_u32(raw: memoryview, at: int) -> tuple[int, int]:
    if at + 4 > len(raw):
        raise ValueError("truncated u32")
    return struct.unpack_from("<I", raw, at)[0], at + 4


def _read_blob(raw: memoryview, at: int) -> tuple[bytes, int]:
    n, at = _read_u32(raw, at)
    if at + n > len(raw):
        raise ValueError("truncated blob")
    return bytes(raw[at:at + n]), at + n


def _split_zip(raw: bytes) -> dict | None:
    """Split a simple ZIP into exact framing and raw compressed payloads without inflating them."""
    at = 0
    pieces: list[tuple[bytes, bytes]] = []
    while at + 4 <= len(raw) and struct.unpack_from("<I", raw, at)[0] == LOCAL:
        if at + 30 > len(raw):
            return None
        (
            _sig,
            _version,
            flags,
            method,
            _mtime,
            _mdate,
            _crc,
            compressed_size,
            _uncompressed_size,
            name_len,
            extra_len,
        ) = struct.unpack_from("<IHHHHHIIIHH", raw, at)
        # Reject encrypted streams and data descriptors: compressed_size must be authoritative in the local header.
        if flags & 0x0001 or flags & 0x0008:
            return None
        if method not in (0, 8):
            return None
        payload_at = at + 30 + name_len + extra_len
        payload_end = payload_at + compressed_size
        if payload_at > len(raw) or payload_end > len(raw):
            return None
        pieces.append((raw[at:payload_at], raw[payload_at:payload_end]))
        at = payload_end
    if not pieces or at + 4 > len(raw):
        return None
    tail_sig = struct.unpack_from("<I", raw, at)[0]
    if tail_sig not in (CENTRAL, EOCD):
        return None
    tail = raw[at:]
    rebuilt = b"".join(frame + payload for frame, payload in pieces) + tail
    if rebuilt != raw:
        raise AssertionError("raw ZIP split failed exact reconstruction")
    return {"pieces": pieces, "tail": tail, "raw_size": len(raw)}


def _serialize_segment(items: list[tuple[str, dict]]) -> bytes:
    buf = io.BytesIO(); buf.write(SEG_MAGIC); _u32(buf, len(items))
    for rel, item in items:
        _blob(buf, rel.encode("utf-8")); _u32(buf, int(item["raw_size"])); _u32(buf, len(item["pieces"]))
        for frame, payload in item["pieces"]:
            _blob(buf, frame); _blob(buf, payload)
        _blob(buf, item["tail"])
    return buf.getvalue()


def _parse_sources(root: Path) -> tuple[list[tuple[str, dict]] | None, float, str | None]:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.suffix.lower() != ".zip" for p in files):
        return None, time.perf_counter() - started, "not-all-zip"
    items: list[tuple[str, dict]] = []
    for path in files:
        raw = path.read_bytes()
        split = _split_zip(raw)
        if split is None:
            return None, time.perf_counter() - started, f"unsupported-zip:{path.name}"
        items.append((path.relative_to(root).as_posix(), split))
    return items, time.perf_counter() - started, None


def _build_candidate(items: list[tuple[str, dict]], group_size: int, level: int, archive: Path, parse_s: float) -> dict:
    started_serial = time.perf_counter()
    serialized = [_serialize_segment(items[i:i + group_size]) for i in range(0, len(items), group_size)]
    serialization_s = time.perf_counter() - started_serial

    started = time.perf_counter()
    compressed = [zstd.ZstdCompressor(level=level, threads=0).compress(segment) for segment in serialized]
    out = io.BytesIO(); out.write(MAGIC); _u32(out, len(compressed))
    for raw_segment, packed in zip(serialized, compressed):
        _u32(out, len(raw_segment)); _blob(out, packed)
    archive.write_bytes(out.getvalue())
    compression_write_s = time.perf_counter() - started

    max_decode = max((len(segment) for segment in serialized), default=0)
    max_amp = 0.0
    for group_at, segment in zip(range(0, len(items), group_size), serialized):
        group = items[group_at:group_at + group_size]
        smallest = min(int(item[1]["raw_size"]) for item in group)
        max_amp = max(max_amp, len(segment) / max(1, smallest))

    return {
        "group_size": group_size,
        "level": level,
        "archive_bytes": archive.stat().st_size,
        "parse_s": parse_s,
        "serialization_s": serialization_s,
        "compression_write_s": compression_write_s,
        "create_s": parse_s + serialization_s + compression_write_s,
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "locality_green": max_decode <= MAX_DECODE and max_amp <= MAX_AMP,
    }


def _restore(archive: Path, out_root: Path) -> None:
    raw = memoryview(archive.read_bytes()); at = 0
    if bytes(raw[:4]) != MAGIC:
        raise ValueError("bad archive magic")
    at = 4; segment_count, at = _read_u32(raw, at)
    for _ in range(segment_count):
        expected_size, at = _read_u32(raw, at); packed, at = _read_blob(raw, at)
        segment = zstd.ZstdDecompressor().decompress(packed, max_output_size=expected_size)
        if len(segment) != expected_size:
            raise ValueError("segment size mismatch")
        seg = memoryview(segment); sat = 0
        if bytes(seg[:4]) != SEG_MAGIC:
            raise ValueError("bad segment magic")
        sat = 4; file_count, sat = _read_u32(seg, sat)
        for _ in range(file_count):
            rel_b, sat = _read_blob(seg, sat); expected_raw, sat = _read_u32(seg, sat); piece_count, sat = _read_u32(seg, sat)
            rebuilt = io.BytesIO()
            for _ in range(piece_count):
                frame, sat = _read_blob(seg, sat); payload, sat = _read_blob(seg, sat)
                rebuilt.write(frame); rebuilt.write(payload)
            tail, sat = _read_blob(seg, sat); rebuilt.write(tail)
            restored = rebuilt.getvalue()
            if len(restored) != expected_raw:
                raise ValueError("restored ZIP size mismatch")
            target = out_root / rel_b.decode("utf-8")
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(restored)
        if sat != len(seg):
            raise ValueError("segment trailing bytes")
    if at != len(raw):
        raise ValueError("archive trailing bytes")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); source = corpus / "04_deflate_family"
    expected_tree = CORPUS.tree_hash(source)

    with tempfile.TemporaryDirectory(prefix="cmpct-rds-", dir=work_root) as td_raw:
        td = Path(td_raw); stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)
        items, parse_s, reason = _parse_sources(stage)
        candidates: list[dict] = []
        if items is not None:
            for group_size in GROUP_SIZES:
                for level in LEVELS:
                    archive = td / f"candidate-g{group_size}-l{level}.rds"
                    c = _build_candidate(items, group_size, level, archive, parse_s)
                    restored = td / f"restore-g{group_size}-l{level}"; restored.mkdir()
                    _restore(archive, restored)
                    c["tree_verified"] = CORPUS.tree_hash(restored) == expected_tree
                    c["beats_zip_size"] = c["archive_bytes"] < zip_result["archive_bytes"]
                    c["beats_zstd19_size"] = c["archive_bytes"] < zstd_result["archive_bytes"]
                    c["beats_zip_create"] = c["create_s"] < zip_result["create_s"]
                    c["beats_zstd19_create"] = c["create_s"] < zstd_result["create_s"]
                    c["viable"] = c["tree_verified"] and c["locality_green"] and all(c[k] for k in (
                        "beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"
                    ))
                    candidates.append(c)
        viable = [c for c in candidates if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"])) if viable else None
        return {
            "schema": "cmpct-v030-raw-deflate-segment-oracle-v1",
            "claim_boundary": "research-only raw-DEFLATE transform; no canonical/native/Android promotion implied",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "tree_sha256": expected_tree,
            "source_parse_s": parse_s,
            "parse_rejection": reason,
            "source_zip_files": len(items) if items is not None else 0,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_candidate": best,
            "gate": {
                "source_admitted": items is not None,
                "all_candidates_exact_tree": bool(candidates) and all(c["tree_verified"] for c in candidates),
                "all_candidates_locality_green": bool(candidates) and all(c["locality_green"] for c in candidates),
                "four_way_win_found": best is not None,
                "passed": items is not None and bool(candidates) and all(c["tree_verified"] for c in candidates) and all(c["locality_green"] for c in candidates),
            },
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-raw-deflate-segment-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-raw-deflate-segment.json"))
    a = p.parse_args(); result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"viable_candidate": result["viable_candidate"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("raw-DEFLATE segment oracle correctness/locality gate failed")


if __name__ == "__main__":
    main()
