from __future__ import annotations

"""Persisted-metadata / physical-pread falsifier for the v0.30 R4 lazy interval reader.

Mission Lock / Referee
======================
The frozen lazy-interval candidate at 93dce32 proved exact reconstruction on 938 aligned and 69
preregistered unaligned 4 KiB reads with <=3.8045x modeled metadata+payload I/O, but its anchor/block
objects were handed to the reader by the builder. That is not yet a cold product reader.

Hypothesis: serialize the *same* 4 KiB anchors and DEFLATE block state into fixed-directory,
independently SHA-256-authenticated compressed frames, then run the unchanged LazyIntervalReader
through lazy sequence proxies backed by os.pread. Back the compressed DEFLATE owner with a 512-byte
pread cache instead of a resident bytes object. Exact cold reads should remain <=8x when actual unique
metadata and payload bytes fetched from disk are charged.

Disproof: any byte mismatch, metadata-frame verification failure on pristine bytes, >32,768 physical
bytes for a 4 KiB request, >128 recursion, or loss of the v0.29 Analytics density margin falsifies this
physicalization. A deliberately corrupted touched metadata frame MUST fail closed. No page/IO/cache
size or threshold sweep is allowed after result-bearing execution begins.

Scope limit: this experiment authenticates persisted selective metadata frames but does NOT yet provide
archive-rooted chunk authentication/recovery for arbitrary compressed-payload subranges. Therefore a
pass is research evidence only, never a claim that product integrity/recovery is complete.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import struct
import tempfile
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_lazy_interval_reader as LAZY

SCHEMA = "cmpct-v030-r4-deflate-persisted-lazy-reader-v1"
PAGE = LAZY.PAGE
LIMIT = LAZY.LIMIT
BLOCK = 512
HEADER = struct.Struct("<4sII")
DIR = struct.Struct("<QIBBH")  # absolute frame offset, frame length, kind, reserved, logical id
MAGIC = b"SAM1"
KIND_ANCHOR = 1
KIND_BLOCK = 2


def _uvar_read(raw: bytes, off: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if off >= len(raw) or shift > 63:
            raise ValueError("invalid uvarint")
        b = raw[off]; off += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, off
        shift += 7


def _unpack_nibbles(raw: bytes, count: int) -> list[int]:
    out: list[int] = []
    for b in raw:
        out.append(b & 15)
        if len(out) < count:
            out.append((b >> 4) & 15)
    if len(out) != count:
        raise ValueError("nibble count mismatch")
    return out


def _metadata_raw(parsed: dict) -> tuple[list[bytes], list[bytes]]:
    tokens = parsed["tokens"]
    blocks = parsed["blocks"]
    first_token_bit: list[int | None] = [None] * len(blocks)
    for _start, _length, _distance, bit0, _bit1, bid in tokens:
        if first_token_bit[bid] is None:
            first_token_bit[bid] = bit0

    block_raw: list[bytes] = []
    for b in blocks:
        fb = first_token_bit[b["id"]]
        if fb is None:
            raise RuntimeError("empty DEFLATE block unsupported")
        raw = bytearray(b"BST1")
        raw += DEP.uvarint(b["id"]); raw.append(b["type"])
        raw += DEP.uvarint(b["out_start"])
        raw += DEP.uvarint(b["out_end"] - b["out_start"])
        raw += DEP.uvarint(fb)
        if b["type"] == 2:
            llp = DEP.pack_nibbles(b["ll_lengths"]); ddp = DEP.pack_nibbles(b["dd_lengths"])
            raw += DEP.uvarint(len(b["ll_lengths"])) + DEP.uvarint(len(llp)) + llp
            raw += DEP.uvarint(len(b["dd_lengths"])) + DEP.uvarint(len(ddp)) + ddp
        block_raw.append(bytes(raw))

    pages = math.ceil(parsed["output_bytes"] / PAGE)
    anchors: list[bytes] = []
    ti = 0
    for page in range(pages):
        pos = page * PAGE
        while ti + 1 < len(tokens) and tokens[ti][0] + tokens[ti][1] <= pos:
            ti += 1
        start, length, _distance, bit0, _bit1, bid = tokens[ti]
        if not (start <= pos < start + length):
            raise RuntimeError("failed to locate page token anchor")
        anchors.append(b"ANC1" + DEP.uvarint(page) + DEP.uvarint(start) + DEP.uvarint(bit0) + DEP.uvarint(bid))
    return anchors, block_raw


def _write_metadata(path: Path, parsed: dict) -> dict:
    anchors, blocks = _metadata_raw(parsed)
    rows: list[tuple[int, int, bytes]] = []
    for i, raw in enumerate(anchors): rows.append((KIND_ANCHOR, i, raw))
    for i, raw in enumerate(blocks): rows.append((KIND_BLOCK, i, raw))
    header_bytes = HEADER.size
    directory_bytes = DIR.size * len(rows)
    cursor = header_bytes + directory_bytes
    directory = bytearray(); frames = bytearray()
    frame_sizes: list[int] = []
    for kind, ident, raw in rows:
        enc = zlib.compress(raw, 9)
        frame = hashlib.sha256(enc).digest() + enc
        directory += DIR.pack(cursor, len(frame), kind, 0, ident)
        frames += frame
        frame_sizes.append(len(frame))
        cursor += len(frame)
    payload = HEADER.pack(MAGIC, len(anchors), len(blocks)) + directory + frames
    path.write_bytes(payload)
    return {
        "stored_bytes": len(payload), "header_bytes": header_bytes, "directory_bytes": directory_bytes,
        "frame_payload_bytes": sum(frame_sizes), "anchors": len(anchors), "blocks": len(blocks),
    }


class PreadFile:
    def __init__(self, path: Path, block: int = BLOCK):
        self.path = path; self.fd = os.open(path, os.O_RDONLY); self.size = path.stat().st_size; self.block = block
        self.cache: dict[int, bytes] = {}; self.fetched: set[int] = set(); self.calls = 0
    def close(self): os.close(self.fd)
    def __len__(self): return self.size
    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.indices(self.size)
            if step != 1: return bytes(self[i] for i in range(start, stop, step))
            return bytes(self[i] for i in range(start, stop))
        i = int(key)
        if i < 0: i += self.size
        if not 0 <= i < self.size: raise IndexError(i)
        base = (i // self.block) * self.block
        data = self.cache.get(base)
        if data is None:
            data = os.pread(self.fd, min(self.block, self.size - base), base)
            if not data: raise EOFError("short payload pread")
            self.cache[base] = data; self.fetched.add(base); self.calls += 1
        return data[i - base]
    def bytes_fetched(self) -> int:
        return sum(min(self.block, self.size - base) for base in self.fetched)


class MetaStore:
    def __init__(self, path: Path):
        self.path = path; self.fd = os.open(path, os.O_RDONLY); self.size = path.stat().st_size
        h = os.pread(self.fd, HEADER.size, 0)
        if len(h) != HEADER.size: raise ValueError("short metadata header")
        magic, self.na, self.nb = HEADER.unpack(h)
        if magic != MAGIC: raise ValueError("metadata magic mismatch")
        self.header_bytes = HEADER.size; self.bytes = HEADER.size; self.calls = 1
        self.cache: dict[tuple[int,int], dict] = {}
    def close(self): os.close(self.fd)
    def _slot(self, kind: int, ident: int) -> int:
        if kind == KIND_ANCHOR:
            if not 0 <= ident < self.na: raise IndexError(ident)
            return ident
        if kind == KIND_BLOCK:
            if not 0 <= ident < self.nb: raise IndexError(ident)
            return self.na + ident
        raise ValueError("bad metadata kind")
    def load(self, kind: int, ident: int) -> dict:
        key=(kind,ident)
        if key in self.cache: return self.cache[key]
        off = HEADER.size + self._slot(kind, ident) * DIR.size
        draw = os.pread(self.fd, DIR.size, off); self.calls += 1; self.bytes += len(draw)
        if len(draw) != DIR.size: raise ValueError("short metadata directory read")
        frame_off, frame_len, actual_kind, _reserved, actual_id = DIR.unpack(draw)
        if actual_kind != kind or actual_id != ident: raise ValueError("metadata directory identity mismatch")
        if frame_len < 33 or frame_off < HEADER.size + (self.na+self.nb)*DIR.size or frame_off + frame_len > self.size:
            raise ValueError("metadata frame bounds invalid")
        frame = os.pread(self.fd, frame_len, frame_off); self.calls += 1; self.bytes += len(frame)
        if len(frame) != frame_len: raise ValueError("short metadata frame read")
        digest, enc = frame[:32], frame[32:]
        if hashlib.sha256(enc).digest() != digest: raise ValueError("metadata frame authentication failed")
        try: raw = zlib.decompress(enc)
        except zlib.error as exc: raise ValueError("metadata frame decompression failed") from exc
        row = self._parse(kind, ident, raw, frame_len + DIR.size)
        self.cache[key]=row
        return row
    def _parse(self, kind: int, ident: int, raw: bytes, charged: int) -> dict:
        if kind == KIND_ANCHOR:
            if not raw.startswith(b"ANC1"): raise ValueError("anchor magic mismatch")
            off=4; page,off=_uvar_read(raw,off); start,off=_uvar_read(raw,off); bit,off=_uvar_read(raw,off); bid,off=_uvar_read(raw,off)
            if off != len(raw) or page != ident: raise ValueError("anchor parse mismatch")
            return {"page":page,"token_start":start,"bit_start":bit,"block_id":bid,"frame_bytes":charged}
        if not raw.startswith(b"BST1"): raise ValueError("block magic mismatch")
        off=4; bid,off=_uvar_read(raw,off)
        if off >= len(raw): raise ValueError("short block state")
        typ=raw[off]; off+=1; out_start,off=_uvar_read(raw,off); span,off=_uvar_read(raw,off); fb,off=_uvar_read(raw,off)
        ll: list[int]=[]; dd: list[int]=[]
        if typ == 2:
            nll,off=_uvar_read(raw,off); bll,off=_uvar_read(raw,off); llraw=raw[off:off+bll]; off+=bll
            ndd,off=_uvar_read(raw,off); bdd,off=_uvar_read(raw,off); ddraw=raw[off:off+bdd]; off+=bdd
            ll=_unpack_nibbles(llraw,nll); dd=_unpack_nibbles(ddraw,ndd)
        if off != len(raw) or bid != ident or typ not in (0,1,2): raise ValueError("block parse mismatch")
        return {"id":bid,"type":typ,"out_start":out_start,"out_end":out_start+span,"first_token_bit":fb,"ll_lengths":ll,"dd_lengths":dd,"frame_bytes":charged}


class MetaSeq:
    def __init__(self, store: MetaStore, kind: int): self.store=store; self.kind=kind
    def __len__(self): return self.store.na if self.kind == KIND_ANCHOR else self.store.nb
    def __getitem__(self, ident: int): return self.store.load(self.kind, ident)


def _run_one(payload_path: Path, meta_path: Path, expected: bytes, start: int) -> dict:
    payload=PreadFile(payload_path); meta=MetaStore(meta_path)
    try:
        reader=LAZY.LazyIntervalReader(payload, MetaSeq(meta,KIND_ANCHOR), MetaSeq(meta,KIND_BLOCK), len(expected))
        end=min(start+PAGE,len(expected)); t0=time.perf_counter(); got=reader.read(start,end); wall=time.perf_counter()-t0
        pbytes=payload.bytes_fetched(); mbytes=meta.bytes; combined=pbytes+mbytes
        return {"start":start,"end":end,"exact":got==expected[start:end],"payload_pread_bytes":pbytes,"metadata_pread_bytes":mbytes,
                "physical_bytes":combined,"physical_amplification":combined/max(1,end-start),"payload_pread_calls":payload.calls,"metadata_pread_calls":meta.calls,
                "metadata_frames":len(meta.cache),"symbols_parsed":reader.symbols_parsed,"recursive_calls":reader.recursive_calls,
                "max_recursion_depth":reader.max_depth,"cache_bytes_peak":reader.max_cache_bytes,"wall_s":wall}
    finally:
        payload.close(); meta.close()


def _run_set(payload_path: Path, meta_path: Path, expected: bytes, starts: list[int]) -> dict:
    rows=[_run_one(payload_path,meta_path,expected,s) for s in starts]
    fail=sum((not r["exact"]) or r["physical_bytes"]>LIMIT or r["max_recursion_depth"]>LAZY.MAX_RECURSION for r in rows)
    return {"requests":len(rows),"failures":fail,"all_exact_and_bounded":fail==0,
            "worst_physical":max(rows,key=lambda r:r["physical_bytes"]),"worst_wall":max(rows,key=lambda r:r["wall_s"]),
            "max_payload_pread_calls":max(r["payload_pread_calls"] for r in rows),"max_metadata_pread_calls":max(r["metadata_pread_calls"] for r in rows),
            "total_wall_s":sum(r["wall_s"] for r in rows)}


def _corruption_probe(meta_path: Path, expected: bytes, payload_path: Path) -> dict:
    corrupt=meta_path.with_name("metadata-corrupt.bin"); data=bytearray(meta_path.read_bytes())
    magic,na,nb=HEADER.unpack_from(data,0); assert magic==MAGIC and na>0
    frame_off,frame_len,kind,_r,ident=DIR.unpack_from(data,HEADER.size)
    flip=frame_off+32+max(0,(frame_len-32)//2); data[flip]^=1; corrupt.write_bytes(data)
    refused=False; message=""
    try: _run_one(payload_path,corrupt,expected,0)
    except Exception as exc: refused=True; message=f"{type(exc).__name__}: {exc}"
    return {"touched_anchor_frame_corrupted":True,"fail_closed":refused,"message":message,"flipped_offset":flip,"kind":kind,"id":ident}


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_persist_lazy_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_persist_lazy_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"04_analytics_and_database"
    rel=DUAL._npz_relation(source)["accepted"]; npz=source.joinpath(*Path(rel["npz_path"]).parts)
    info,comp,expected,method=CONE._raw_zip_member(npz,rel["member"])
    if method!=zipfile.ZIP_DEFLATED: raise RuntimeError("expected DEFLATE")
    parsed=DEP.parse_tokens(comp); inflated=zlib.decompress(comp,-15)
    if inflated!=expected or parsed["output_bytes"]!=len(expected): raise RuntimeError("builder parse mismatch")
    payload_path=work/"owner.deflate"; payload_path.write_bytes(comp); meta_path=work/"sparse.meta"; meta_stats=_write_metadata(meta_path,parsed)
    candidate=LAZY.DUAL_OWNER_BYTES+meta_stats["stored_bytes"]; margin=DUAL.ACCEPTED_V029_ANALYTICS-candidate
    rss0=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fixed=_run_set(payload_path,meta_path,expected,LAZY.TOKEN.starts(len(expected)))
    unaligned=_run_set(payload_path,meta_path,expected,LAZY._unaligned_starts(len(expected)))
    corruption=_corruption_probe(meta_path,expected,payload_path)
    rss1=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    supported=margin>0 and fixed["all_exact_and_bounded"] and unaligned["all_exact_and_bounded"] and corruption["fail_closed"]
    return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"member":{"compressed_bytes":len(comp),"compressed_sha256":hashlib.sha256(comp).hexdigest(),"raw_bytes":len(expected),"raw_sha256":hashlib.sha256(expected).hexdigest(),"crc32":info.CRC},
            "physical_metadata":{**meta_stats,"dual_owner_plus_metadata_bytes":candidate,"accepted_v029_analytics_bytes":DUAL.ACCEPTED_V029_ANALYTICS,"margin_to_v029_bytes":margin},
            "payload_pread_block_bytes":BLOCK,"fixed_requests":fixed,"unaligned_controls":unaligned,"metadata_corruption":corruption,
            "host_process":{"ru_maxrss_before_kib":rss0,"ru_maxrss_after_kib":rss1,"delta_ru_maxrss_kib":max(0,rss1-rss0)},
            "hypothesis":{"persisted_lazy_reader_preserves_exact_bounded_locality":supported},
            "contract":{"diagnostic_only":True,"release_credit":False,"same_lazy_algorithm":True,"same_page_bytes":PAGE,"same_limit_bytes":LIMIT,"payload_pread_block_bytes_frozen":BLOCK,"no_threshold_sweep":True,"no_product_format_change":True,"metadata_frames_authenticated":True,"payload_subrange_authentication_complete":False,"recovery_complete":False},
            "next_if_supported":"add archive-rooted authenticated payload chunks plus corruption/recovery probes and held-out NPZ/NPY relations before any integration claim",
            "next_if_falsified":"preserve negative and attribute physical overhead to metadata directory, frame fanout, or payload block rounding without raising the 8x limit"}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-persist-lazy-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-persist-lazy.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"member":d["member"],"physical_metadata":d["physical_metadata"],"fixed_requests":d["fixed_requests"],"unaligned_controls":d["unaligned_controls"],"metadata_corruption":d["metadata_corruption"],"host_process":d["host_process"],"hypothesis":d["hypothesis"]},indent=2))

if __name__=="__main__": main()
