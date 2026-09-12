from __future__ import annotations

"""Cold sparse-anchor selective reader prototype for the Analytics exact-NPZ owner.

Mission lock
============
The earlier token-anchor oracle met the 8x payload envelope but gifted a fully parsed per-byte LZ77
parent graph. Persisting every token dependency is expensive: globally-compressed metadata barely fits
and page-framed metadata loses the density floor. This experiment tests a different general mechanism:
persist only one token anchor per decoded 4 KiB page plus independently authenticated DEFLATE-block
Huffman state, then rediscover copy dependencies by locally parsing the original compressed stream at
read time.

Builder/runtime separation is explicit. The builder may parse the stream once to choose page anchors
and serialize block state. The cold reader receives only: compressed DEFLATE bytes, serialized anchor
records, serialized block-state records, and requested [start,end) output ranges. It does NOT receive
or consult the token list, per-byte parent graph, decoded owner, zlib output, or a prebuilt object tree.
Copy tokens recursively request only earlier output; overlapping copies use the already-decoded local
history or a bounded seed interval.

For each fixed 4 KiB request from the prior locality oracle, run a fresh logical reader cache and charge
unique compressed-payload byte ranges plus every anchor/block metadata frame touched. Each metadata
frame is independently zlib-9 compressed and charged 32 digest bytes + 16 directory bytes. Validate
returned bytes exactly against the independently inflated member only after the read completes.

Falsifiers
==========
Reject this prototype if any request is byte-inexact, recursion/work is unbounded, stored metadata makes
the 4,453,188-byte dual owner exceed accepted v0.29 Analytics, or worst cold metadata+payload I/O exceeds
32,768 bytes (8x a 4 KiB request). No anchor-spacing, page-size, codec, threshold, or corpus sweep is
allowed. A pass is still research evidence, not release credit: arbitrary unaligned reads, archive-rooted
authentication, corruption/recovery, hostile metadata bounds, reader CPU/RSS and native parity remain.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_token_anchor_physical_oracle as TOKEN

SCHEMA = "cmpct-v030-r4-deflate-sparse-anchor-cold-reader-v1"
PAGE = 4096
LIMIT = 8 * PAGE
DUAL_OWNER_BYTES = 4_453_188
FRAME_TAX = 48  # 32-byte digest + conservative 16-byte directory record.
MAX_RECURSION = 128


def _svar(v: int) -> bytes:
    return DEP.uvarint((v << 1) ^ (v >> 63))


def _frame(raw: bytes) -> tuple[bytes, int]:
    enc = zlib.compress(raw, 9)
    return enc, len(enc) + FRAME_TAX


def _build_metadata(parsed: dict) -> tuple[list[dict], list[dict], int]:
    tokens = parsed["tokens"]
    blocks = parsed["blocks"]
    first_token_bit: list[int | None] = [None] * len(blocks)
    for start, length, distance, bit0, bit1, bid in tokens:
        if first_token_bit[bid] is None:
            first_token_bit[bid] = bit0

    block_meta: list[dict] = []
    stored = 0
    for b in blocks:
        fb = first_token_bit[b["id"]]
        if fb is None:
            raise RuntimeError("empty DEFLATE block unsupported by prototype")
        raw = bytearray(b"BST1")
        raw += DEP.uvarint(b["id"])
        raw.append(b["type"])
        raw += DEP.uvarint(b["out_start"])
        raw += DEP.uvarint(b["out_end"] - b["out_start"])
        raw += DEP.uvarint(fb)
        if b["type"] == 2:
            llp = DEP.pack_nibbles(b["ll_lengths"])
            ddp = DEP.pack_nibbles(b["dd_lengths"])
            raw += DEP.uvarint(len(b["ll_lengths"])) + DEP.uvarint(len(llp)) + llp
            raw += DEP.uvarint(len(b["dd_lengths"])) + DEP.uvarint(len(ddp)) + ddp
        enc, cost = _frame(bytes(raw))
        stored += cost
        block_meta.append({
            "id": b["id"], "type": b["type"], "out_start": b["out_start"], "out_end": b["out_end"],
            "first_token_bit": fb, "ll_lengths": b["ll_lengths"], "dd_lengths": b["dd_lengths"],
            "frame_bytes": cost, "frame_sha256": hashlib.sha256(enc).hexdigest(),
        })

    pages = math.ceil(parsed["output_bytes"] / PAGE)
    anchors: list[dict] = []
    ti = 0
    for page in range(pages):
        pos = page * PAGE
        while ti + 1 < len(tokens) and tokens[ti][0] + tokens[ti][1] <= pos:
            ti += 1
        start, length, _distance, bit0, _bit1, bid = tokens[ti]
        if not (start <= pos < start + length):
            raise RuntimeError("failed to locate page token anchor")
        raw = b"ANC1" + DEP.uvarint(page) + DEP.uvarint(start) + DEP.uvarint(bit0) + DEP.uvarint(bid)
        enc, cost = _frame(raw)
        stored += cost
        anchors.append({
            "page": page, "token_start": start, "bit_start": bit0, "block_id": bid,
            "frame_bytes": cost, "frame_sha256": hashlib.sha256(enc).hexdigest(),
        })
    return anchors, block_meta, stored


class ColdReader:
    def __init__(self, comp: bytes, anchors: list[dict], blocks: list[dict], output_bytes: int):
        self.comp = comp
        self.anchors = anchors
        self.blocks = blocks
        self.output_bytes = output_bytes
        self.page_cache: dict[int, bytes] = {}
        self.payload_ranges: list[tuple[int, int]] = []
        self.anchor_frames: set[int] = set()
        self.block_frames: set[int] = set()
        self.recursive_calls = 0
        self.max_depth = 0
        self.symbols_decoded = 0

    def _tables(self, bid: int):
        b = self.blocks[bid]
        self.block_frames.add(bid)
        if b["type"] == 1:
            return CONE.FIXED
        if b["type"] == 2:
            return CONE._table(b["ll_lengths"]), CONE._table(b["dd_lengths"])
        return None

    def _merge_payload(self) -> int:
        if not self.payload_ranges:
            return 0
        rs = sorted(self.payload_ranges)
        merged = [list(rs[0])]
        for a, b in rs[1:]:
            if a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        return sum(b - a for a, b in merged)

    def metadata_bytes(self) -> int:
        return sum(self.anchors[p]["frame_bytes"] for p in self.anchor_frames) + sum(
            self.blocks[b]["frame_bytes"] for b in self.block_frames
        )

    def payload_bytes(self) -> int:
        return self._merge_payload()

    def read(self, start: int, end: int, depth: int = 0) -> bytes:
        if not (0 <= start <= end <= self.output_bytes):
            raise RuntimeError("out-of-range recursive read")
        if start == end:
            return b""
        if depth > MAX_RECURSION:
            raise RuntimeError("recursive dependency depth exceeded")
        self.recursive_calls += 1
        self.max_depth = max(self.max_depth, depth)
        out = bytearray()
        pos = start
        while pos < end:
            page = pos // PAGE
            data = self._decode_page(page, depth)
            base = page * PAGE
            take = min(end, base + len(data)) - pos
            off = pos - base
            out += data[off:off + take]
            pos += take
        return bytes(out)

    def _decode_page(self, page: int, depth: int) -> bytes:
        cached = self.page_cache.get(page)
        if cached is not None:
            return cached
        anchor = self.anchors[page]
        self.anchor_frames.add(page)
        page_base = page * PAGE
        page_end = min(page_base + PAGE, self.output_bytes)
        out_start = anchor["token_start"]
        out_pos = out_start
        local = bytearray()
        bid = anchor["block_id"]
        br = CONE.BitReader(self.comp)
        br.bit = anchor["bit_start"]
        segment_start = br.bit
        tables = self._tables(bid)

        def finish_segment() -> None:
            nonlocal segment_start
            a = segment_start // 8
            b = (br.bit + 7) // 8
            if b > a:
                self.payload_ranges.append((a, b))
            segment_start = br.bit

        while out_pos < page_end:
            block = self.blocks[bid]
            if out_pos >= block["out_end"]:
                finish_segment()
                bid += 1
                if bid >= len(self.blocks):
                    raise RuntimeError("ran beyond final DEFLATE block")
                block = self.blocks[bid]
                br.bit = block["first_token_bit"]
                segment_start = br.bit
                tables = self._tables(bid)

            token_start = out_pos
            if block["type"] == 0:
                sym = br.read(8)
                self.symbols_decoded += 1
                token = bytes([sym])
            else:
                ll, dd = tables
                sym = CONE._decode(br, ll)
                self.symbols_decoded += 1
                if sym < 256:
                    token = bytes([sym])
                elif sym == 256:
                    if out_pos != block["out_end"]:
                        raise RuntimeError("early EOB relative to persisted block state")
                    continue
                elif 257 <= sym <= 285:
                    li = sym - 257
                    length = CONE.LEN_BASE[li] + br.read(CONE.LEN_EXTRA[li])
                    ds = CONE._decode(br, dd)
                    if ds >= len(CONE.DIST_BASE):
                        raise RuntimeError("invalid distance symbol")
                    distance = CONE.DIST_BASE[ds] + br.read(CONE.DIST_EXTRA[ds])
                    if distance > out_pos:
                        raise RuntimeError("distance beyond output")
                    seed_len = min(distance, length)
                    src0 = out_pos - distance
                    src1 = src0 + seed_len
                    seed = bytearray()
                    if src0 < out_start:
                        prior_end = min(src1, out_start)
                        seed += self.read(src0, prior_end, depth + 1)
                        src0 = prior_end
                    if src0 < src1:
                        lo = src0 - out_start
                        hi = src1 - out_start
                        if lo < 0 or hi > len(local):
                            raise RuntimeError("local LZ77 history unavailable")
                        seed += local[lo:hi]
                    if len(seed) != seed_len or not seed:
                        raise RuntimeError("failed to reconstruct LZ77 seed")
                    token = bytes((seed * ((length + len(seed) - 1) // len(seed)))[:length])
                else:
                    raise RuntimeError("reserved literal/length symbol")
            local += token
            out_pos = token_start + len(token)
        finish_segment()
        begin = page_base - out_start
        if begin < 0 or page_end - out_start > len(local):
            raise RuntimeError("page reconstruction bounds mismatch")
        page_bytes = bytes(local[begin:page_end - out_start])
        if len(page_bytes) != page_end - page_base:
            raise RuntimeError("short page reconstruction")
        self.page_cache[page] = page_bytes
        return page_bytes


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_sparsecold_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_sparsecold_repair")
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
    parsed = DEP.parse_tokens(comp)
    inflated = zlib.decompress(comp, -15)
    if inflated != expected or parsed["output_bytes"] != len(expected):
        raise RuntimeError("builder parse mismatch")
    anchors, blocks, metadata_stored = _build_metadata(parsed)
    candidate = DUAL_OWNER_BYTES + metadata_stored
    density_margin = DUAL.ACCEPTED_V029_ANALYTICS - candidate

    reqs = TOKEN.starts(len(expected))
    rows = []
    worst = None
    failures = 0
    exact_failures = 0
    total_combined = total_payload = total_meta = total_symbols = total_calls = 0
    max_depth = 0
    for start in reqs:
        end = min(start + PAGE, len(expected))
        r = ColdReader(comp, anchors, blocks, len(expected))
        got = r.read(start, end)
        exact = got == expected[start:end]
        meta = r.metadata_bytes()
        payload = r.payload_bytes()
        combined = meta + payload
        if not exact:
            exact_failures += 1
        if combined > LIMIT:
            failures += 1
        row = {
            "start": start, "end": end, "exact": exact,
            "metadata_bytes_touched": meta, "payload_bytes_touched": payload,
            "combined_bytes_touched": combined,
            "combined_amplification": combined / max(1, end - start),
            "anchor_frames": len(r.anchor_frames), "block_frames": len(r.block_frames),
            "symbols_decoded": r.symbols_decoded, "recursive_calls": r.recursive_calls,
            "max_recursion_depth": r.max_depth,
        }
        rows.append(row)
        total_combined += combined
        total_payload += payload
        total_meta += meta
        total_symbols += r.symbols_decoded
        total_calls += r.recursive_calls
        max_depth = max(max_depth, r.max_depth)
        if worst is None or combined > worst["combined_bytes_touched"]:
            worst = row
    assert worst is not None
    passes = exact_failures == 0 and failures == 0 and density_margin >= 0
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "member": {
            "compressed_bytes": len(comp), "raw_bytes": len(expected),
            "compressed_sha256": hashlib.sha256(comp).hexdigest(),
            "raw_sha256": hashlib.sha256(expected).hexdigest(), "crc32": info.CRC,
        },
        "metadata": {
            "page_bytes": PAGE, "anchors": len(anchors), "block_states": len(blocks),
            "stored_bytes_including_frame_auth_and_directory": metadata_stored,
            "dual_owner_plus_metadata_bytes": candidate,
            "margin_to_v029_bytes": density_margin,
        },
        "selective_reader": {
            "requests": len(reqs), "request_bytes": PAGE, "limit_bytes": LIMIT,
            "exact_failures": exact_failures, "locality_failures": failures,
            "mean_metadata_bytes": total_meta / len(reqs),
            "mean_payload_bytes": total_payload / len(reqs),
            "mean_combined_bytes": total_combined / len(reqs),
            "mean_combined_amplification": total_combined / len(reqs) / PAGE,
            "mean_symbols_decoded": total_symbols / len(reqs),
            "mean_recursive_calls": total_calls / len(reqs),
            "max_recursion_depth": max_depth,
            "worst_combined": worst,
        },
        "hypothesis": {
            "cold_sparse_anchor_reader_exact_and_within_density_and_8x_io": passes,
        },
        "contract": {
            "diagnostic_only": True, "release_credit": False,
            "runtime_parent_graph_used": False, "runtime_token_list_used": False,
            "runtime_decoded_owner_used": False, "builder_may_choose_anchors_from_full_parse": True,
            "metadata_frame_auth_bytes": 32, "metadata_directory_bytes": 16,
            "no_anchor_spacing_sweep": True, "no_page_size_sweep": True,
            "no_codec_sweep": True, "no_threshold_sweep": True,
            "remaining_debt": "unaligned/adversarial requests, archive-rooted auth proof, corruption/recovery, hostile metadata bounds, measured reader CPU/RSS and native/shared-reader parity",
        },
        "next_if_supported": "remove benchmark-only metadata objects by deserializing frames from bytes, add unaligned+corruption hostile suite, and measure fresh-process selective-read CPU/RSS",
        "next_if_falsified": "preserve the negative and inspect whether excess comes from metadata I/O, payload rediscovery, or recursive work before changing representation; do not tune anchor spacing",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-sparsecold-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-sparsecold.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"metadata": d["metadata"], "selective_reader": d["selective_reader"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
