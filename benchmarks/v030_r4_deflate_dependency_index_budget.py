from __future__ import annotations

"""Charge the missing dependency-index information behind the Analytics token-anchor oracle.

Mission lock
============
The token-anchor physical oracle showed that the exact sparse LZ77 dependency closure can fit the
4 KiB selective-read 8x payload/range envelope, but it computed that closure from a fully parsed
in-memory parent graph. That graph was not charged to the archive. Before implementing a reader,
this experiment asks whether enough *persisted* token/dependency information can plausibly fit the
1,681,984-byte auxiliary budget that remains before the dense dual owner loses to accepted v0.29.

This is deliberately a lower-bound/economics experiment, not release credit. It serializes every
DEFLATE token's output length, copy distance, compressed bit start/span and block transition using
unsigned varints; exact dynamic-Huffman code lengths and per-4KiB page token anchors are included.
A 32-byte digest is charged. We report both the raw sidecar and a whole-sidecar zlib-9 compressed
size. The compressed form is an optimistic information floor because whole-sidecar compression is
not itself random-accessible.

Falsifier
=========
If even the optimistic compressed sidecar plus the dense owner exceeds accepted v0.29 Analytics,
reject the current token-graph productization path: the oracle's missing dependency information is
not economically free. If it fits, the path merely survives this lower bound; the next experiment
must page/frame/authenticate the sidecar and charge sidecar I/O plus actual selective reconstruction.
No threshold, page-size, corpus or codec sweep is allowed.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE

SCHEMA = "cmpct-v030-r4-deflate-dependency-index-budget-v1"
PAGE = 4096
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
AUTH_BYTES = 32


def uvarint(v: int) -> bytes:
    if v < 0:
        raise ValueError("negative uvarint")
    out = bytearray()
    while v >= 0x80:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    out.append(v)
    return bytes(out)


def pack_nibbles(values: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(values), 2):
        a = values[i]
        b = values[i + 1] if i + 1 < len(values) else 0
        if not (0 <= a <= 15 and 0 <= b <= 15):
            raise ValueError("invalid DEFLATE code length")
        out.append(a | (b << 4))
    return bytes(out)


def dynamic_with_lengths(br: CONE.BitReader):
    hlit = br.read(5) + 257
    hdist = br.read(5) + 1
    hclen = br.read(4) + 4
    code_lengths = [0] * 19
    for i in range(hclen):
        code_lengths[CONE.CL_ORDER[i]] = br.read(3)
    code_table = CONE._table(code_lengths)
    values: list[int] = []
    need = hlit + hdist
    while len(values) < need:
        sym = CONE._decode(br, code_table)
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
    return CONE._table(ll), CONE._table(dd), ll, dd


def parse_tokens(raw: bytes) -> dict:
    br = CONE.BitReader(raw)
    tokens: list[tuple[int, int, int, int, int, int]] = []
    blocks: list[dict] = []
    out_pos = 0
    bid = 0
    while True:
        header_bit = br.bit
        final = br.read(1)
        btype = br.read(2)
        out0 = out_pos
        ll_lengths: list[int] = []
        dd_lengths: list[int] = []
        if btype == 0:
            br.align()
            n = br.read(16)
            nn = br.read(16)
            if (n ^ 0xFFFF) != nn:
                raise ValueError("stored LEN/NLEN mismatch")
            for _ in range(n):
                s = br.bit
                br.read(8)
                e = br.bit
                tokens.append((out_pos, 1, 0, s, e, bid))
                out_pos += 1
        elif btype in (1, 2):
            if btype == 1:
                ll, dd = CONE.FIXED
            else:
                ll, dd, ll_lengths, dd_lengths = dynamic_with_lengths(br)
            while True:
                s = br.bit
                sym = CONE._decode(br, ll)
                if sym < 256:
                    e = br.bit
                    tokens.append((out_pos, 1, 0, s, e, bid))
                    out_pos += 1
                elif sym == 256:
                    break
                elif 257 <= sym <= 285:
                    li = sym - 257
                    length = CONE.LEN_BASE[li] + br.read(CONE.LEN_EXTRA[li])
                    ds = CONE._decode(br, dd)
                    if ds >= len(CONE.DIST_BASE):
                        raise ValueError("invalid distance symbol")
                    distance = CONE.DIST_BASE[ds] + br.read(CONE.DIST_EXTRA[ds])
                    if distance > out_pos:
                        raise ValueError("distance beyond output")
                    e = br.bit
                    tokens.append((out_pos, length, distance, s, e, bid))
                    out_pos += length
                else:
                    raise ValueError("reserved literal/length symbol")
        else:
            raise ValueError("reserved block type")
        blocks.append({
            "id": bid,
            "type": btype,
            "header_bit": header_bit,
            "end_bit": br.bit,
            "out_start": out0,
            "out_end": out_pos,
            "ll_lengths": ll_lengths,
            "dd_lengths": dd_lengths,
        })
        bid += 1
        if final:
            break
    return {"tokens": tokens, "blocks": blocks, "output_bytes": out_pos, "consumed_bits": br.bit}


def serialize_index(parsed: dict) -> tuple[bytes, dict]:
    out = bytearray(b"DIDX1")
    tokens = parsed["tokens"]
    blocks = parsed["blocks"]
    out += uvarint(parsed["output_bytes"])
    out += uvarint(parsed["consumed_bits"])
    out += uvarint(len(tokens))
    out += uvarint(len(blocks))

    block_bytes = 0
    for b in blocks:
        before = len(out)
        out.append(b["type"])
        out += uvarint(b["header_bit"])
        out += uvarint(b["end_bit"] - b["header_bit"])
        out += uvarint(b["out_start"])
        out += uvarint(b["out_end"] - b["out_start"])
        if b["type"] == 2:
            llp = pack_nibbles(b["ll_lengths"])
            ddp = pack_nibbles(b["dd_lengths"])
            out += uvarint(len(b["ll_lengths"])) + uvarint(len(llp)) + llp
            out += uvarint(len(b["dd_lengths"])) + uvarint(len(ddp)) + ddp
        block_bytes += len(out) - before

    token_bytes = 0
    prev_out = 0
    prev_bit = 0
    prev_bid = 0
    page_anchors: list[tuple[int, int, int]] = []
    next_page = 0
    for ordinal, (start, length, distance, bit0, bit1, bid) in enumerate(tokens):
        while next_page * PAGE < start + length:
            pos = next_page * PAGE
            if pos >= parsed["output_bytes"]:
                break
            if pos >= start:
                page_anchors.append((next_page, ordinal, bit0))
                next_page += 1
            else:
                break
        before = len(out)
        out += uvarint(start - prev_out)
        out += uvarint(length)
        out += uvarint(distance)
        out += uvarint(bit0 - prev_bit)
        out += uvarint(bit1 - bit0)
        out += uvarint(bid - prev_bid)
        prev_out = start + length
        prev_bit = bit0
        prev_bid = bid
        token_bytes += len(out) - before

    anchor_bytes = 0
    out += b"PG"
    out += uvarint(len(page_anchors))
    p0 = o0 = b0 = 0
    for page, ordinal, bit in page_anchors:
        before = len(out)
        out += uvarint(page - p0) + uvarint(ordinal - o0) + uvarint(bit - b0)
        p0, o0, b0 = page, ordinal, bit
        anchor_bytes += len(out) - before

    digest = hashlib.sha256(out).digest()
    out += digest
    return bytes(out), {
        "block_descriptor_bytes": block_bytes,
        "token_descriptor_bytes": token_bytes,
        "page_anchor_descriptor_bytes": anchor_bytes,
        "page_anchors": len(page_anchors),
        "auth_digest_bytes": len(digest),
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_depidx_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_depidx_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    rel = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(rel["npz_path"]).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, rel["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError("expected DEFLATE")
    parsed = parse_tokens(comp)
    actual = zlib.decompress(comp, -15)
    if actual != expected or parsed["output_bytes"] != len(actual):
        raise RuntimeError("token parser mismatch")
    sidecar, parts = serialize_index(parsed)
    compressed = zlib.compress(sidecar, 9)
    budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    raw_total = DUAL_OWNER_BYTES + len(sidecar)
    compressed_total = DUAL_OWNER_BYTES + len(compressed)
    survives = compressed_total <= ACCEPTED_V029_ANALYTICS
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "member": {
            "compressed_bytes": len(comp),
            "raw_bytes": len(actual),
            "compressed_sha256": hashlib.sha256(comp).hexdigest(),
            "raw_sha256": hashlib.sha256(actual).hexdigest(),
            "crc32": info.CRC,
        },
        "index": {
            "tokens": len(parsed["tokens"]),
            "blocks": len(parsed["blocks"]),
            **parts,
            "raw_sidecar_bytes": len(sidecar),
            "raw_sidecar_sha256": hashlib.sha256(sidecar).hexdigest(),
            "whole_sidecar_zlib9_bytes": len(compressed),
            "whole_sidecar_zlib9_sha256": hashlib.sha256(compressed).hexdigest(),
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_analytics_bytes": ACCEPTED_V029_ANALYTICS,
            "auxiliary_budget_bytes": budget,
            "raw_owner_plus_sidecar_bytes": raw_total,
            "raw_over_v029_bytes": raw_total - ACCEPTED_V029_ANALYTICS,
            "optimistic_compressed_owner_plus_sidecar_bytes": compressed_total,
            "optimistic_compressed_margin_to_v029_bytes": ACCEPTED_V029_ANALYTICS - compressed_total,
        },
        "hypothesis": {
            "persisted_dependency_information_survives_global_information_budget_lower_bound": survives,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "lower_bound_only": True,
            "no_threshold_sweep": True,
            "no_page_size_sweep": True,
            "no_codec_sweep": True,
            "auth_digest_charged": AUTH_BYTES,
            "important_limitation": "whole-sidecar zlib-9 is an optimistic information floor and is not random-access framing; selective sidecar I/O, hostile bounds, recovery framing and actual reconstruction CPU remain unproven",
        },
        "next_if_supported": "frame the dependency sidecar into independently authenticated page-addressable chunks and measure sidecar+payload pread amplification with exact reconstruction",
        "next_if_falsified": "preserve the negative and abandon the current token-graph reader path unless a different general dependency representation beats this information floor",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-depidx-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-depidx.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"member": d["member"], "index": d["index"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
