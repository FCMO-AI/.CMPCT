from __future__ import annotations

"""Office page-seed cold-reader falsifier.

Mission lock
============
The fixed 4 KiB sparse-anchor cold reader transferred byte-exactly to all eight SFV4
Office streams but failed physical locality on 525/1800 probes, with a 71.43x worst
case. Exact dependency evidence says Office itself is near 2x logical closure, so the
new falsifiable hypothesis is that the excess comes from recursively reconstructing
whole dependency pages for small external LZ77 seeds.

Without changing the 4 KiB page/anchor spacing, DEFLATE bytes, request size, 8x law,
corpus, selector, or codec, persist one independently framed *external seed set* only
for pages whose token reconstruction needs bytes before that page's anchor token.
At read time those seed bytes replace recursive prior-page reads. The builder may use
the fully inflated stream solely to create and validate these persisted seed frames;
the reader may use only compressed payload, anchors/block state, and the page seed
frames. Charge every anchor/block/seed frame touched plus unique compressed payload.

Disprove if any output byte differs, any charged 4 KiB selective read exceeds 32,768
bytes, or the complete SFV4 candidate plus sparse-anchor/block metadata plus all seed
frames reaches/exceeds the frozen v0.29 Office floor. No parameter sweep is permitted.
Even a pass remains diagnostic: metadata is represented as parsed Python objects here,
not deserialized with os.pread from an authenticated archive, and corruption/resource,
fresh-process CPU/RSS, recovery, and native parity remain unpaid.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-page-seed-cold-reader-v1"
PAGE = 4096
LIMIT = 8 * PAGE
FRAME_TAX = COLD.FRAME_TAX
MAX_DECODE_SYMBOLS = 1_000_000


def _merge(rs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not rs:
        return []
    out = [list(sorted(rs)[0])]
    for a, b in sorted(rs)[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _build_seeds(parsed: dict, anchors: list[dict], raw: bytes) -> tuple[list[dict | None], int, int]:
    tokens = parsed["tokens"]
    seeds: list[dict | None] = []
    stored = 0
    logical = 0
    ti = 0
    for page, anchor in enumerate(anchors):
        page_end = min((page + 1) * PAGE, len(raw))
        out_start = anchor["token_start"]
        while ti < len(tokens) and tokens[ti][0] < out_start:
            ti += 1
        j = ti
        need: list[tuple[int, int]] = []
        while j < len(tokens) and tokens[j][0] < page_end:
            start, length, distance, _bit0, _bit1, _bid = tokens[j]
            if distance:
                seed_len = min(distance, length)
                src0 = start - distance
                src1 = src0 + seed_len
                if src0 < out_start:
                    need.append((src0, min(src1, out_start)))
            j += 1
        merged = _merge(need)
        if not merged:
            seeds.append(None)
            continue
        frame = bytearray(b"SED1")
        frame += DEP.uvarint(page) + DEP.uvarint(len(merged))
        prev = 0
        intervals = []
        for a, b in merged:
            data = raw[a:b]
            frame += DEP.uvarint(a - prev) + DEP.uvarint(b - a) + data
            intervals.append((a, b, data))
            logical += b - a
            prev = a
        enc = zlib.compress(bytes(frame), 9)
        cost = len(enc) + FRAME_TAX
        stored += cost
        seeds.append({
            "intervals": intervals,
            "frame_bytes": cost,
            "frame_sha256": hashlib.sha256(enc).hexdigest(),
            "logical_seed_bytes": sum(b - a for a, b in merged),
        })
    return seeds, stored, logical


class SeedReader(COLD.ColdReader):
    def __init__(self, comp: bytes, anchors: list[dict], blocks: list[dict], seeds: list[dict | None], output_bytes: int):
        super().__init__(comp, anchors, blocks, output_bytes)
        self.seeds = seeds
        self.seed_frames: set[int] = set()

    def metadata_bytes(self) -> int:
        base = super().metadata_bytes()
        return base + sum(self.seeds[p]["frame_bytes"] for p in self.seed_frames if self.seeds[p] is not None)

    def _seed_read(self, page: int, start: int, end: int) -> bytes:
        rec = self.seeds[page]
        if rec is None:
            raise RuntimeError("missing external seed frame")
        self.seed_frames.add(page)
        out = bytearray()
        pos = start
        for a, b, data in rec["intervals"]:
            if b <= pos:
                continue
            if a > pos:
                break
            take_end = min(end, b)
            if take_end > pos:
                out += data[pos - a:take_end - a]
                pos = take_end
            if pos >= end:
                return bytes(out)
        raise RuntimeError("persisted external seed does not cover requested interval")

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
            if self.symbols_decoded > MAX_DECODE_SYMBOLS:
                raise RuntimeError("decode symbol resource bound exceeded")
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
                        seed += self._seed_read(page, src0, prior_end)
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
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_pageseed_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_pageseed_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")
    derived = built["derived_inventory"]
    streams = built["all_streams"]
    hashes = sorted({rec["stream_hash"] for rec in derived.values()})

    sparse_metadata = 0
    seed_metadata = 0
    logical_seed_bytes = 0
    rows = []
    requests = exact_failures = locality_failures = 0
    worst = None
    max_symbols = 0
    t0 = time.perf_counter()
    for h in hashes:
        comp = streams[h]
        raw = zlib.decompress(comp, -15)
        parsed = DEP.parse_tokens(comp)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parser/output mismatch")
        anchors, blocks, sparse_stored = COLD._build_metadata(parsed)
        seeds, seed_stored, seed_logical = _build_seeds(parsed, anchors, raw)
        sparse_metadata += sparse_stored
        seed_metadata += seed_stored
        logical_seed_bytes += seed_logical
        row = {"stream_sha256": h, "raw_bytes": len(raw), "compressed_bytes": len(comp), "sparse_metadata_bytes": sparse_stored,
               "seed_metadata_bytes": seed_stored, "logical_seed_bytes": seed_logical, "seed_pages": sum(x is not None for x in seeds),
               "requests": 0, "locality_failures": 0, "exact_failures": 0, "worst_combined_bytes": 0}
        for start in TRANSFER._starts(len(raw)):
            end = min(start + PAGE, len(raw))
            r = SeedReader(comp, anchors, blocks, seeds, len(raw))
            q0 = time.perf_counter()
            got = r.read(start, end)
            qwall = time.perf_counter() - q0
            exact = got == raw[start:end]
            meta = r.metadata_bytes()
            payload = r.payload_bytes()
            combined = meta + payload
            requests += 1
            row["requests"] += 1
            max_symbols = max(max_symbols, r.symbols_decoded)
            if not exact:
                exact_failures += 1; row["exact_failures"] += 1
            if combined > LIMIT:
                locality_failures += 1; row["locality_failures"] += 1
            row["worst_combined_bytes"] = max(row["worst_combined_bytes"], combined)
            q = {"stream_sha256": h, "start": start, "end": end, "request_bytes": end-start,
                 "metadata_bytes_touched": meta, "payload_bytes_touched": payload, "combined_bytes_touched": combined,
                 "combined_amplification": combined/max(1,end-start), "symbols_decoded": r.symbols_decoded,
                 "seed_frames_touched": len(r.seed_frames), "wall_s": qwall, "exact": exact}
            if worst is None or combined > worst["combined_bytes_touched"]:
                worst = q
        rows.append(row)
    probe_wall = time.perf_counter() - t0
    sfv4_bytes = int(built["stored_bytes"])
    candidate = sfv4_bytes + sparse_metadata + seed_metadata
    margin = SFV4.ACCEPTED_V029_OFFICE - candidate
    supported = exact_failures == 0 and locality_failures == 0 and margin > 0
    return {
        "schema": SCHEMA, "source_commit": os.environ.get("EVIDENCE_HEAD"), "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source), "streams": rows,
        "summary": {"derived_file_count": len(derived), "unique_derived_stream_count": len(hashes), "requests": requests,
                    "request_bytes": PAGE, "limit_bytes": LIMIT, "exact_failures": exact_failures,
                    "locality_failures": locality_failures, "max_symbols_decoded_per_request": max_symbols,
                    "worst_combined": worst, "probe_wall_s": probe_wall},
        "economics": {"sfv4_bytes_before_locality_metadata": sfv4_bytes, "sparse_anchor_block_metadata_bytes": sparse_metadata,
                      "page_seed_metadata_bytes": seed_metadata, "logical_seed_bytes_before_framing": logical_seed_bytes,
                      "candidate_with_all_locality_metadata_bytes": candidate, "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
                      "margin_to_v029_bytes": margin},
        "hypothesis": {"page_seed_materialization_cuts_recursion_within_product_economics": supported},
        "contract": {"diagnostic_only": True, "release_credit": False, "runtime_recursive_prior_reads": False,
                     "runtime_parent_graph_used": False, "runtime_token_list_used": False, "runtime_decoded_owner_used": False,
                     "fixed_page_and_anchor_bytes": PAGE, "fixed_limit_bytes": LIMIT, "no_parameter_sweep": True,
                     "remaining_debt": "deserialize authenticated metadata from archive bytes; actual os.pread/seeks; corruption/resource/recovery; fresh-process CPU/RSS; native parity"},
        "next_if_supported": "replace parsed metadata/payload with authenticated serialized bytes and os.pread, then hostile corruption/resource and CPU/RSS gates",
        "next_if_falsified": "preserve the negative and separate seed-storage economics from token-location payload work before changing representation; do not tune 4KiB/8x",
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-pageseed-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-pageseed.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"summary":d["summary"],"economics":d["economics"],"hypothesis":d["hypothesis"]},indent=2))

if __name__ == "__main__": main()
