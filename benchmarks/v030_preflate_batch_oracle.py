from __future__ import annotations

"""Single-process preflate frontier oracle for the frozen deflate-family workload.

The reversible plaintext ZIP experiment showed large size headroom but ~96 ms of Python inflate/rebuild overhead.
CMPCT already has an audited, bounded Rust preflate transform that reconstructs DEFLATE containers exactly.  Its
existing one-file CLI pays process startup once per object, so this oracle uses the companion batch front door to
amortize orchestration across the 14-version ZIP family while preserving per-item pack->recreate verification.

After one batch transform, preflate payloads are serialized into independently decodable groups and outer-Zstd
compressed.  Candidate creation time includes source discovery, the complete verified native batch invocation,
payload reads, serialization, compression and archive write.  Restore decompresses a group and delegates each
preflate payload to the existing bounded bridge before exact-tree verification.

Research only: a four-way win does not authorize canonical/native/Android promotion by itself.
"""

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT

MAGIC = b"PFB1"
SEG_MAGIC = b"PFS1"
GROUP_SIZES = (2, 3, 4, 6)
LEVELS = (1, 3, 6)
MAX_AMP = 8.0
MAX_DECODE = 8 * 1024 * 1024


def _batch_bridge() -> Path:
    override = os.environ.get("CMPCT_PREFLATE_BATCH")
    candidates = [
        Path(override) if override else None,
        Path("native/preflate-bridge/target/release/cmpct-preflate-batch"),
    ]
    for path in candidates:
        if path is not None and path.is_file() and os.access(path, os.X_OK):
            return path.resolve()
    raise RuntimeError("cmpct-preflate-batch binary not found")


def _single_bridge() -> Path:
    override = os.environ.get("CMPCT_PREFLATE_BRIDGE")
    candidates = [
        Path(override) if override else None,
        Path("native/preflate-bridge/target/release/cmpct-preflate-bridge"),
    ]
    for path in candidates:
        if path is not None and path.is_file() and os.access(path, os.X_OK):
            return path.resolve()
    raise RuntimeError("cmpct-preflate-bridge binary not found")


def _u32(buf: io.BytesIO, n: int) -> None: buf.write(struct.pack("<I", n))
def _u64(buf: io.BytesIO, n: int) -> None: buf.write(struct.pack("<Q", n))
def _blob(buf: io.BytesIO, raw: bytes) -> None: _u32(buf, len(raw)); buf.write(raw)


def _read_u32(raw: memoryview, at: int) -> tuple[int, int]:
    if at + 4 > len(raw): raise ValueError("truncated u32")
    return struct.unpack_from("<I", raw, at)[0], at + 4


def _read_u64(raw: memoryview, at: int) -> tuple[int, int]:
    if at + 8 > len(raw): raise ValueError("truncated u64")
    return struct.unpack_from("<Q", raw, at)[0], at + 8


def _read_blob(raw: memoryview, at: int) -> tuple[bytes, int]:
    n, at = _read_u32(raw, at)
    if at + n > len(raw): raise ValueError("truncated blob")
    return bytes(raw[at:at+n]), at + n


def _serialize_group(group: list[tuple[str, int, bytes]]) -> bytes:
    buf = io.BytesIO(); buf.write(SEG_MAGIC); _u32(buf, len(group))
    for rel, source_size, payload in group:
        _blob(buf, rel.encode("utf-8")); _u64(buf, source_size); _blob(buf, payload)
    return buf.getvalue()


def _batch_pack(stage: Path, work: Path) -> tuple[list[tuple[str, int, bytes]], float]:
    started = time.perf_counter()
    files = sorted(p for p in stage.rglob("*") if p.is_file())
    if not files or any(p.suffix.lower() != ".zip" for p in files):
        raise RuntimeError("preflate batch oracle requires an all-ZIP source tree")
    outdir = work / "preflate"
    subprocess.run([str(_batch_bridge()), str(outdir), *(str(p) for p in files)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    items = []
    for index, path in enumerate(files):
        payload_path = outdir / f"{index:04d}.pflt"
        if not payload_path.is_file(): raise RuntimeError("batch bridge omitted output")
        items.append((path.relative_to(stage).as_posix(), path.stat().st_size, payload_path.read_bytes()))
    return items, time.perf_counter() - started


def _candidate(items, batch_s: float, group_size: int, level: int, archive: Path) -> dict:
    started = time.perf_counter()
    groups = [items[i:i+group_size] for i in range(0, len(items), group_size)]
    serialized = [_serialize_group(group) for group in groups]
    packed = [zstd.ZstdCompressor(level=level, threads=0).compress(segment) for segment in serialized]
    out = io.BytesIO(); out.write(MAGIC); _u32(out, len(packed))
    for segment, compressed in zip(serialized, packed, strict=True):
        _u32(out, len(segment)); _blob(out, compressed)
    archive.write_bytes(out.getvalue())
    post_batch_s = time.perf_counter() - started

    max_decode = max(map(len, serialized), default=0)
    max_amp = 0.0
    for group, segment in zip(groups, serialized, strict=True):
        # A selected read decodes the outer group and reconstructs the requested original ZIP. Charge both.
        for _rel, source_size, _payload in group:
            max_amp = max(max_amp, (len(segment) + source_size) / max(1, source_size))
    return {
        "group_size": group_size, "level": level, "archive_bytes": archive.stat().st_size,
        "batch_pack_verify_s": batch_s, "post_batch_s": post_batch_s, "create_s": batch_s + post_batch_s,
        "max_decode_unit_bytes": max_decode, "max_member_read_amplification": max_amp,
        "locality_green": max_decode <= MAX_DECODE and max_amp <= MAX_AMP,
    }


def _restore(archive: Path, out_root: Path, work: Path) -> None:
    raw = memoryview(archive.read_bytes()); at = 0
    if bytes(raw[:4]) != MAGIC: raise ValueError("bad archive magic")
    at = 4; count, at = _read_u32(raw, at)
    bridge = _single_bridge()
    item_index = 0
    for _ in range(count):
        expected, at = _read_u32(raw, at); compressed, at = _read_blob(raw, at)
        segment = zstd.ZstdDecompressor().decompress(compressed, max_output_size=expected)
        if len(segment) != expected: raise ValueError("segment size mismatch")
        seg = memoryview(segment); sat = 0
        if bytes(seg[:4]) != SEG_MAGIC: raise ValueError("bad segment magic")
        sat = 4; members, sat = _read_u32(seg, sat)
        for _ in range(members):
            rel_b, sat = _read_blob(seg, sat); source_size, sat = _read_u64(seg, sat); payload, sat = _read_blob(seg, sat)
            packed = work / f"restore-{item_index:04d}.pflt"; packed.write_bytes(payload)
            target = out_root / rel_b.decode("utf-8"); target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(bridge), "unpack", str(packed), str(target)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if target.stat().st_size != source_size: raise RuntimeError("preflate restored wrong source size")
            item_index += 1
        if sat != len(seg): raise ValueError("segment trailing bytes")
    if at != len(raw): raise ValueError("archive trailing bytes")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); source = corpus / "04_deflate_family"
    expected_tree = CORPUS.tree_hash(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-pfb-", dir=work_root) as td_raw:
        td = Path(td_raw); stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)
        items, batch_s = _batch_pack(stage, td)
        candidates = []
        for group_size in GROUP_SIZES:
            for level in LEVELS:
                archive = td / f"candidate-g{group_size}-l{level}.pfb"
                c = _candidate(items, batch_s, group_size, level, archive)
                restored = td / f"restore-g{group_size}-l{level}"; restored.mkdir(); _restore(archive, restored, td)
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
            "schema": "cmpct-v030-preflate-batch-oracle-v1",
            "claim_boundary": "research-only verified batch preflate plus bounded outer segments",
            "workload": "resemblance_hostile_v1/04_deflate_family", "tree_sha256": expected_tree,
            "source_zip_files": len(items), "batch_pack_verify_s": batch_s,
            "zip": zip_result, "tar_zstd19": zstd_result, "candidates": candidates, "viable_candidate": best,
            "gate": {
                "exact_workload": len(items) == 14,
                "all_candidates_exact_tree": all(c["tree_verified"] for c in candidates),
                "all_candidates_locality_green": all(c["locality_green"] for c in candidates),
                "four_way_win_found": best is not None,
            },
        }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-preflate-batch-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-preflate-batch.json")); a=p.parse_args()
    result=run(a.work_root); result["gate"]["passed"]=all(v for k,v in result["gate"].items() if k!="four_way_win_found")
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"batch_s":result["batch_pack_verify_s"],"best":result["viable_candidate"],"gate":result["gate"]},indent=2),flush=True)
    if not result["gate"]["passed"]: raise SystemExit("preflate batch correctness/locality gate failed")

if __name__=="__main__": main()
