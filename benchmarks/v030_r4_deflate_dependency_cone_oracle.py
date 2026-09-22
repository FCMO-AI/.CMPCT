from __future__ import annotations

"""Lower-bound locality oracle for the Analytics exact-NPZ owner.

The dense dual owner beats ordinary v0.30, but its monolithic raw-DEFLATE NPY member exports
unacceptable selective reconstruction. A duplicate 16 KiB decoded view repairs locality but costs
3.61 MB, exceeding the 1.682 MB auxiliary budget required to remain below frozen v0.29 Analytics.

This diagnostic asks a narrower mechanism question before another format prototype: how far does the
*actual transitive DEFLATE back-reference dependency cone* extend for every 4 KiB output request?
It parses the exact frozen raw-DEFLATE member, verifies parser output length against zlib/zipfile,
and computes the earliest transitive output dependency for every decoded byte. The measured span is
a conservative contiguous restart-cone model, not a shipping reader and not release credit.

Pre-registered disproof: if the worst 4 KiB contiguous dependency cone exceeds 8x, reject another
contiguous restart/window design. A failure does NOT falsify a sparse token graph; it says only that
contiguous history ownership is structurally too broad. If <=8x, the next experiment must build and
charge a real authenticated physical index/restart representation; no threshold sweep is allowed.
"""

import argparse
import collections
import json
import os
from pathlib import Path
import shutil
import struct
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL

SCHEMA = "cmpct-v030-r4-deflate-dependency-cone-oracle-v1"
REQUEST = 4 * 1024
LIMIT_AMP = 8.0
INDEX_ENTRY_BYTES = 16
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
DUAL_OWNER_BYTES = 4_453_188

LEN_BASE = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
LEN_EXTRA = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0]
DIST_BASE = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
DIST_EXTRA = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13]
CL_ORDER = [16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]


class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.bit = 0

    def read(self, n: int) -> int:
        if n == 0:
            return 0
        if self.bit + n > len(self.data) * 8:
            raise ValueError("truncated deflate stream")
        v = 0
        for i in range(n):
            v |= ((self.data[self.bit >> 3] >> (self.bit & 7)) & 1) << i
            self.bit += 1
        return v

    def align(self) -> None:
        self.bit = (self.bit + 7) & ~7


def _rev(v: int, n: int) -> int:
    out = 0
    for _ in range(n):
        out = (out << 1) | (v & 1)
        v >>= 1
    return out


def _table(lengths: list[int]):
    if not lengths:
        raise ValueError("empty huffman alphabet")
    maxbits = max(lengths)
    count = [0] * (maxbits + 1)
    for n in lengths:
        if n:
            count[n] += 1
    code = 0
    next_code = [0] * (maxbits + 1)
    for bits in range(1, maxbits + 1):
        code = (code + count[bits - 1]) << 1
        next_code[bits] = code
    table = {}
    for sym, n in enumerate(lengths):
        if not n:
            continue
        c = next_code[n]
        next_code[n] += 1
        table[(_rev(c, n), n)] = sym
    return table, maxbits


def _decode(br: BitReader, ht) -> int:
    table, maxbits = ht
    code = 0
    for n in range(1, maxbits + 1):
        code |= br.read(1) << (n - 1)
        sym = table.get((code, n))
        if sym is not None:
            return sym
    raise ValueError("invalid huffman code")


def _fixed():
    ll = [0] * 288
    for i in range(0, 144):
        ll[i] = 8
    for i in range(144, 256):
        ll[i] = 9
    for i in range(256, 280):
        ll[i] = 7
    for i in range(280, 288):
        ll[i] = 8
    return _table(ll), _table([5] * 32)


FIXED = _fixed()


def _dynamic(br: BitReader):
    hlit = br.read(5) + 257
    hdist = br.read(5) + 1
    hclen = br.read(4) + 4
    code_lengths = [0] * 19
    for i in range(hclen):
        code_lengths[CL_ORDER[i]] = br.read(3)
    code_table = _table(code_lengths)
    values: list[int] = []
    need = hlit + hdist
    while len(values) < need:
        sym = _decode(br, code_table)
        if 0 <= sym <= 15:
            values.append(sym)
        elif sym == 16:
            if not values:
                raise ValueError("repeat with no previous code length")
            values.extend([values[-1]] * (br.read(2) + 3))
        elif sym == 17:
            values.extend([0] * (br.read(3) + 3))
        elif sym == 18:
            values.extend([0] * (br.read(7) + 11))
        else:
            raise ValueError("invalid code-length symbol")
        if len(values) > need:
            raise ValueError("code lengths overrun")
    ll = values[:hlit]
    dd = values[hlit:]
    if not any(dd):
        dd = [1]
    return _table(ll), _table(dd)


def parse_dependencies(raw_deflate: bytes) -> dict:
    br = BitReader(raw_deflate)
    earliest: list[int] = []
    symbol_starts: list[tuple[int, int, int]] = []
    blocks: list[dict] = []
    block_id = 0
    while True:
        block_header_bit = br.bit
        final = br.read(1)
        btype = br.read(2)
        out0 = len(earliest)
        if btype == 0:
            br.align()
            n = br.read(16)
            nn = br.read(16)
            if (n ^ 0xFFFF) != nn:
                raise ValueError("stored block LEN/NLEN mismatch")
            for _ in range(n):
                symbol_starts.append((len(earliest), br.bit, block_id))
                br.read(8)
                earliest.append(len(earliest))
        elif btype in (1, 2):
            ll, dd = FIXED if btype == 1 else _dynamic(br)
            while True:
                sym_bit = br.bit
                sym = _decode(br, ll)
                if sym < 256:
                    symbol_starts.append((len(earliest), sym_bit, block_id))
                    earliest.append(len(earliest))
                elif sym == 256:
                    break
                elif 257 <= sym <= 285:
                    li = sym - 257
                    if li >= len(LEN_BASE):
                        raise ValueError("invalid length symbol")
                    length = LEN_BASE[li] + br.read(LEN_EXTRA[li])
                    ds = _decode(br, dd)
                    if ds >= len(DIST_BASE):
                        raise ValueError("invalid distance symbol")
                    distance = DIST_BASE[ds] + br.read(DIST_EXTRA[ds])
                    if distance > len(earliest):
                        raise ValueError("distance beyond output")
                    symbol_starts.append((len(earliest), sym_bit, block_id))
                    for _ in range(length):
                        src = len(earliest) - distance
                        earliest.append(earliest[src])
                else:
                    raise ValueError("reserved literal/length symbol")
        else:
            raise ValueError("reserved DEFLATE block type")
        blocks.append({
            "id": block_id,
            "header_bit": block_header_bit,
            "end_bit": br.bit,
            "out_start": out0,
            "out_end": len(earliest),
            "type": btype,
        })
        block_id += 1
        if final:
            break
    return {
        "output_bytes": len(earliest),
        "consumed_bits": br.bit,
        "earliest": earliest,
        "symbols": symbol_starts,
        "blocks": blocks,
    }


def _raw_zip_member(npz: Path, member: str):
    raw = npz.read_bytes()
    with zipfile.ZipFile(npz, "r") as zf:
        info = zf.getinfo(member)
        expected = zf.read(member)
    off = info.header_offset
    if raw[off:off + 4] != b"PK\x03\x04":
        raise ValueError("bad local ZIP header")
    _sig, _ver, _flags, method, _mt, _md, _crc, _cs, _us, fn, ex = struct.unpack_from("<IHHHHHIIIHH", raw, off)
    data_off = off + 30 + fn + ex
    comp = raw[data_off:data_off + info.compress_size]
    return info, comp, expected, method


def _worst_contiguous_span(values: list[int], width: int) -> dict:
    q: collections.deque[int] = collections.deque()
    worst = {"amplification": 0.0, "start": 0, "end": 0, "earliest_dependency": 0, "span_bytes": 0}
    n = len(values)
    if not n:
        return worst
    if n < width:
        mn = min(values)
        return {"amplification": (n - mn) / max(1, n), "start": 0, "end": n, "earliest_dependency": mn, "span_bytes": n - mn}
    for i, value in enumerate(values):
        while q and values[q[-1]] >= value:
            q.pop()
        q.append(i)
        left = i - width + 1
        while q and q[0] < left:
            q.popleft()
        if i + 1 >= width:
            start = i + 1 - width
            mn = values[q[0]]
            span = (i + 1) - mn
            amp = span / width
            if amp > worst["amplification"]:
                worst = {"amplification": amp, "start": start, "end": i + 1, "earliest_dependency": mn, "span_bytes": span}
    return worst


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r4_deflate_cone_neutral")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_r4_deflate_cone_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"

    relation = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(relation["npz_path"]).parts)
    info, comp, expected, method = _raw_zip_member(npz, relation["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError(f"expected DEFLATE member, got method={method}")

    t0 = time.perf_counter()
    parsed = parse_dependencies(comp)
    parse_wall = time.perf_counter() - t0
    actual = zlib.decompress(comp, -15)
    if actual != expected:
        raise RuntimeError("raw DEFLATE decode mismatch")
    if parsed["output_bytes"] != len(actual):
        raise RuntimeError("parser output length mismatch")

    worst = _worst_contiguous_span(parsed["earliest"], REQUEST)
    optimistic_index = len(parsed["blocks"]) * INDEX_ENTRY_BYTES
    aux_budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    supported = worst["amplification"] <= LIMIT_AMP and optimistic_index <= aux_budget
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "relation": relation,
        "member": {
            "compressed_bytes": len(comp),
            "raw_bytes": len(actual),
            "crc32": info.CRC,
            "compress_type": info.compress_type,
        },
        "parser": {
            "blocks": len(parsed["blocks"]),
            "symbols": len(parsed["symbols"]),
            "consumed_bits": parsed["consumed_bits"],
            "stream_bits": len(comp) * 8,
            "parse_wall_s": parse_wall,
            "exact_raw_match": True,
        },
        "dependency_cone": {
            "request_bytes": REQUEST,
            "limit_amplification": LIMIT_AMP,
            "worst_contiguous_transitive_span": worst,
            "passes_contiguous_cone_floor": worst["amplification"] <= LIMIT_AMP,
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
            "max_auxiliary_bytes_to_beat_v029": aux_budget,
            "optimistic_block_index_bytes": optimistic_index,
            "optimistic_index_within_budget": optimistic_index <= aux_budget,
        },
        "hypothesis": {"supported_for_restart_index_design": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_duplicate_decoded_view": True,
            "no_threshold_sweep": True,
            "no_product_format_change": True,
            "important_limitation": "contiguous dependency span is a conservative restart-cone model; a sparse token graph could be cheaper, so failure rejects contiguous restart cones, not every possible indexed DEFLATE reader",
        },
        "next_if_supported": "build an authenticated physical restart/index prototype and charge exact index/state bytes plus pread I/O",
        "next_if_falsified": "preserve negative; do not add full-history checkpoints or duplicate decoded views; investigate sparse token ownership or a different owner boundary",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-cone-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-cone.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"member": d["member"], "parser": d["parser"], "dependency_cone": d["dependency_cone"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
