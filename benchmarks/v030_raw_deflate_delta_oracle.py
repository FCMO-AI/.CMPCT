from __future__ import annotations

"""Cross-version raw-DEFLATE delta oracle for the v0.30 deflate-family frontier.

``v030_raw_deflate_segment_oracle`` proved that direct local-header parsing can preserve nested ZIPs exactly and
finish faster than both ZIP and Zstd, but compressed payloads remain too entropic for plain outer Zstd.  This
oracle keeps the same no-inflate boundary and exploits the stronger fact present in versioned ZIP families:
corresponding members have the same names and their *raw DEFLATE streams* may still share byte structure.

Within each independently decodable group the first ZIP is a base.  Later ZIPs keep their exact framing/tail bytes
and encode each compressed payload as XOR(base-prefix, target-prefix) plus any target tail.  The whole bounded
group is then Zstd-compressed.  Restore reverses XOR and concatenates the original ZIP bytes exactly.

Creation time includes source reads, ZIP parsing, delta construction, compression and archive write.  Candidates
must remain <=8x for every member and <=8 MiB per decode unit.  This file is research evidence only and cannot
change canonical/native/Android release bytes by itself.
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
from benchmarks import v030_raw_deflate_segment_oracle as RAW

MAGIC = b"RDD1"
SEG_MAGIC = b"RDG1"
LEVELS = (1, 3, 6)
GROUP_SIZES = (2, 3, 4, 6)
MAX_AMP = 8.0
MAX_DECODE = 8 * 1024 * 1024


def _u32(buf: io.BytesIO, value: int) -> None:
    buf.write(struct.pack("<I", value))


def _blob(buf: io.BytesIO, raw: bytes) -> None:
    _u32(buf, len(raw)); buf.write(raw)


def _read_u32(raw: memoryview, at: int) -> tuple[int, int]:
    if at + 4 > len(raw): raise ValueError("truncated u32")
    return struct.unpack_from("<I", raw, at)[0], at + 4


def _read_blob(raw: memoryview, at: int) -> tuple[bytes, int]:
    n, at = _read_u32(raw, at)
    if at + n > len(raw): raise ValueError("truncated blob")
    return bytes(raw[at:at+n]), at + n


def _frame_name(frame: bytes) -> bytes:
    if len(frame) < 30: raise ValueError("short ZIP local frame")
    name_len, extra_len = struct.unpack_from("<HH", frame, 26)
    if 30 + name_len + extra_len != len(frame): raise ValueError("local frame length mismatch")
    return frame[30:30+name_len]


def _parse_sources(root: Path) -> tuple[list[tuple[str, dict]] | None, float, str | None]:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.suffix.lower() != ".zip" for p in files):
        return None, time.perf_counter() - started, "not-all-zip"
    items = []
    for path in files:
        split = RAW._split_zip(path.read_bytes())
        if split is None:
            return None, time.perf_counter() - started, f"unsupported-zip:{path.name}"
        split = dict(split)
        split["names"] = [_frame_name(frame) for frame, _payload in split["pieces"]]
        items.append((path.relative_to(root).as_posix(), split))
    return items, time.perf_counter() - started, None


def _xor_prefix(base: bytes, target: bytes) -> tuple[bytes, bytes]:
    n = min(len(base), len(target))
    residual = bytes(a ^ b for a, b in zip(base[:n], target[:n]))
    return residual, target[n:]


def _serialize_group(group: list[tuple[str, dict]]) -> bytes:
    if not group: raise ValueError("empty group")
    base_rel, base = group[0]
    buf = io.BytesIO(); buf.write(SEG_MAGIC); _u32(buf, len(group))
    _blob(buf, base_rel.encode()); _u32(buf, int(base["raw_size"])); _u32(buf, len(base["pieces"]))
    for frame, payload in base["pieces"]:
        _blob(buf, frame); _blob(buf, payload)
    _blob(buf, base["tail"])

    for rel, item in group[1:]:
        if item["names"] != base["names"] or len(item["pieces"]) != len(base["pieces"]):
            raise ValueError("cross-version ZIP member layout mismatch")
        _blob(buf, rel.encode()); _u32(buf, int(item["raw_size"])); _u32(buf, len(item["pieces"]))
        for (base_frame, base_payload), (frame, payload) in zip(base["pieces"], item["pieces"], strict=True):
            # Frame bytes are retained exactly: versions may alter CRCs, sizes or other local-header fields.
            _blob(buf, frame)
            residual, extra = _xor_prefix(base_payload, payload)
            _u32(buf, len(payload)); _blob(buf, residual); _blob(buf, extra)
        _blob(buf, item["tail"])
    return buf.getvalue()


def _build_candidate(items: list[tuple[str, dict]], group_size: int, level: int, archive: Path, parse_s: float) -> dict:
    started_delta = time.perf_counter()
    groups = [items[i:i+group_size] for i in range(0, len(items), group_size)]
    serialized = [_serialize_group(group) for group in groups]
    delta_s = time.perf_counter() - started_delta

    started = time.perf_counter()
    packed = [zstd.ZstdCompressor(level=level, threads=0).compress(segment) for segment in serialized]
    out = io.BytesIO(); out.write(MAGIC); _u32(out, len(packed))
    for segment, compressed in zip(serialized, packed, strict=True):
        _u32(out, len(segment)); _blob(out, compressed)
    archive.write_bytes(out.getvalue())
    compression_write_s = time.perf_counter() - started

    max_decode = max(map(len, serialized), default=0)
    max_amp = 0.0
    for group, segment in zip(groups, serialized, strict=True):
        smallest = min(int(item[1]["raw_size"]) for item in group)
        max_amp = max(max_amp, len(segment) / max(1, smallest))
    return {
        "group_size": group_size, "level": level, "archive_bytes": archive.stat().st_size,
        "parse_s": parse_s, "delta_serialize_s": delta_s, "compression_write_s": compression_write_s,
        "create_s": parse_s + delta_s + compression_write_s,
        "max_decode_unit_bytes": max_decode, "max_member_read_amplification": max_amp,
        "locality_green": max_decode <= MAX_DECODE and max_amp <= MAX_AMP,
    }


def _restore_segment(segment: bytes, out_root: Path) -> None:
    raw = memoryview(segment); at = 0
    if bytes(raw[:4]) != SEG_MAGIC: raise ValueError("bad segment magic")
    at = 4; count, at = _read_u32(raw, at)
    if count < 1: raise ValueError("empty segment")

    rel_b, at = _read_blob(raw, at); raw_size, at = _read_u32(raw, at); piece_count, at = _read_u32(raw, at)
    base_pieces = [];
    rebuilt = io.BytesIO()
    for _ in range(piece_count):
        frame, at = _read_blob(raw, at); payload, at = _read_blob(raw, at)
        base_pieces.append((frame, payload)); rebuilt.write(frame); rebuilt.write(payload)
    tail, at = _read_blob(raw, at); rebuilt.write(tail)
    base_zip = rebuilt.getvalue()
    if len(base_zip) != raw_size: raise ValueError("base ZIP size mismatch")
    target = out_root / rel_b.decode(); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(base_zip)

    for _ in range(count - 1):
        rel_b, at = _read_blob(raw, at); raw_size, at = _read_u32(raw, at); target_piece_count, at = _read_u32(raw, at)
        if target_piece_count != piece_count: raise ValueError("target piece-count mismatch")
        rebuilt = io.BytesIO()
        for index in range(piece_count):
            frame, at = _read_blob(raw, at); target_len, at = _read_u32(raw, at)
            residual, at = _read_blob(raw, at); extra, at = _read_blob(raw, at)
            base_payload = base_pieces[index][1]
            n = min(len(base_payload), target_len)
            if len(residual) != n or len(extra) != target_len - n: raise ValueError("delta payload length mismatch")
            prefix = bytes(a ^ b for a, b in zip(base_payload[:n], residual))
            payload = prefix + extra
            rebuilt.write(frame); rebuilt.write(payload)
        tail, at = _read_blob(raw, at); rebuilt.write(tail)
        restored = rebuilt.getvalue()
        if len(restored) != raw_size: raise ValueError("target ZIP size mismatch")
        target = out_root / rel_b.decode(); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(restored)
    if at != len(raw): raise ValueError("segment trailing bytes")


def _restore(archive: Path, out_root: Path) -> None:
    raw = memoryview(archive.read_bytes()); at = 0
    if bytes(raw[:4]) != MAGIC: raise ValueError("bad archive magic")
    at = 4; count, at = _read_u32(raw, at)
    for _ in range(count):
        expected, at = _read_u32(raw, at); packed, at = _read_blob(raw, at)
        segment = zstd.ZstdDecompressor().decompress(packed, max_output_size=expected)
        if len(segment) != expected: raise ValueError("segment size mismatch")
        _restore_segment(segment, out_root)
    if at != len(raw): raise ValueError("archive trailing bytes")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); source = corpus / "04_deflate_family"
    expected_tree = CORPUS.tree_hash(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-rdd-", dir=work_root) as td_raw:
        td = Path(td_raw); stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)
        items, parse_s, reason = _parse_sources(stage)
        candidates = []
        if items is not None:
            for group_size in GROUP_SIZES:
                for level in LEVELS:
                    archive = td / f"candidate-g{group_size}-l{level}.rdd"
                    c = _build_candidate(items, group_size, level, archive, parse_s)
                    restored = td / f"restore-g{group_size}-l{level}"; restored.mkdir(); _restore(archive, restored)
                    c["tree_verified"] = CORPUS.tree_hash(restored) == expected_tree
                    c["beats_zip_size"] = c["archive_bytes"] < zip_result["archive_bytes"]
                    c["beats_zstd19_size"] = c["archive_bytes"] < zstd_result["archive_bytes"]
                    c["beats_zip_create"] = c["create_s"] < zip_result["create_s"]
                    c["beats_zstd19_create"] = c["create_s"] < zstd_result["create_s"]
                    c["viable"] = c["tree_verified"] and c["locality_green"] and all(c[k] for k in (
                        "beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"))
                    candidates.append(c)
        viable = [c for c in candidates if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"])) if viable else None
        return {
            "schema": "cmpct-v030-raw-deflate-delta-oracle-v1",
            "claim_boundary": "research-only cross-version raw-DEFLATE delta; no canonical/native/Android promotion implied",
            "workload": "resemblance_hostile_v1/04_deflate_family", "tree_sha256": expected_tree,
            "source_parse_s": parse_s, "parse_rejection": reason, "source_zip_files": len(items) if items else 0,
            "zip": zip_result, "tar_zstd19": zstd_result, "candidates": candidates, "viable_candidate": best,
            "gate": {
                "source_admitted": items is not None,
                "all_candidates_exact_tree": bool(candidates) and all(c["tree_verified"] for c in candidates),
                "all_candidates_locality_green": bool(candidates) and all(c["locality_green"] for c in candidates),
                "four_way_win_found": best is not None,
                "passed": items is not None and bool(candidates) and all(c["tree_verified"] for c in candidates) and all(c["locality_green"] for c in candidates),
            },
        }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-raw-deflate-delta-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-raw-deflate-delta.json")); a = p.parse_args()
    result = run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"viable_candidate": result["viable_candidate"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]: raise SystemExit("raw-DEFLATE delta oracle correctness/locality gate failed")


if __name__ == "__main__": main()
