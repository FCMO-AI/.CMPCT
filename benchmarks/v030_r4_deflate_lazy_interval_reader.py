from __future__ import annotations

"""Lazy interval sparse-anchor reader for the Analytics exact-NPZ owner.

Mission Lock / Referee
======================
The persisted 4 KiB-page cold reader is structurally falsified: the independent page-closure oracle
found 923/938 fixed requests above the 8x decoded-work ceiling, with a 930-page / 929.53x worst case.
The earlier byte/token oracle nevertheless found only ~1.01x exact decoded dependency closure and
~3.62x worst compressed payload. The discrepancy is causal: ``ColdReader.read`` turns a tiny history
request into complete source-page materialization.

Hypothesis: keep the SAME 4 KiB token anchors, block Huffman state, metadata framing, compressed owner,
8x byte envelope and fresh-reader request semantics, but parse irrelevant tokens lazily and materialize
only the exact LZ77 history intervals needed by output bytes. A copy token is periodic with its declared
distance, so a requested sub-slice can be reconstructed from at most the corresponding residues in the
pre-token distance window; the reader need not recursively instantiate intervening full pages.

Disproof
========
Reject this mechanism if any fixed or preregistered unaligned 4 KiB request is byte-inexact; if unique
logical dependency intervals, compressed payload + metadata I/O, or persisted side metadata exceed the
same economic/locality floor; if dependency recursion exceeds the unchanged 128 ceiling; or if reader
state grows without a request-bounded explanation. Do not change PAGE, LIMIT, anchor spacing, codec,
metadata grammar or thresholds after execution begins.

This is still research evidence, not release credit. Metadata records are builder-produced Python
objects carrying authenticated-frame byte charges; an eventual product reader must deserialize and
verify persisted frames from bounded physical reads, integrate archive-rooted authentication/recovery,
and prove native/portable parity.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_deflate_token_anchor_physical_oracle as TOKEN

SCHEMA = "cmpct-v030-r4-deflate-lazy-interval-reader-v1"
PAGE = COLD.PAGE
LIMIT = COLD.LIMIT
DUAL_OWNER_BYTES = COLD.DUAL_OWNER_BYTES
MAX_RECURSION = COLD.MAX_RECURSION
UNALIGNED_PROBES = 64


def _merge_len(ranges: list[tuple[int, int]]) -> int:
    if not ranges:
        return 0
    rs = sorted(ranges)
    out = [list(rs[0])]
    for a, b in rs[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return sum(b - a for a, b in out)


def _unaligned_starts(n: int) -> list[int]:
    if n <= PAGE:
        return [0]
    limit = n - PAGE
    vals = {1, max(0, PAGE - 1), max(0, PAGE + 1), max(0, limit - 1), limit}
    # Deterministic prime-stride probes, frozen before result-bearing execution.
    for i in range(UNALIGNED_PROBES):
        vals.add((137 + i * 104729) % (limit + 1))
    return sorted(v for v in vals if 0 <= v <= limit and v % PAGE != 0)


class LazyIntervalReader:
    def __init__(self, comp: bytes, anchors: list[dict], blocks: list[dict], output_bytes: int):
        self.comp = comp
        self.anchors = anchors
        self.blocks = blocks
        self.output_bytes = output_bytes
        self.interval_cache: dict[tuple[int, int], bytes] = {}
        self.payload_ranges: list[tuple[int, int]] = []
        self.logical_ranges: list[tuple[int, int]] = []
        self.anchor_frames: set[int] = set()
        self.block_frames: set[int] = set()
        self.recursive_calls = 0
        self.max_depth = 0
        self.symbols_parsed = 0
        self.cache_hits = 0
        self.max_cache_bytes = 0

    def _tables(self, bid: int):
        b = self.blocks[bid]
        self.block_frames.add(bid)
        if b["type"] == 1:
            return CONE.FIXED
        if b["type"] == 2:
            return CONE._table(b["ll_lengths"]), CONE._table(b["dd_lengths"])
        return None

    def metadata_bytes(self) -> int:
        return sum(self.anchors[p]["frame_bytes"] for p in self.anchor_frames) + sum(
            self.blocks[b]["frame_bytes"] for b in self.block_frames
        )

    def payload_bytes(self) -> int:
        return _merge_len(self.payload_ranges)

    def logical_dependency_bytes(self) -> int:
        return _merge_len(self.logical_ranges)

    def _remember_cache_peak(self) -> None:
        self.max_cache_bytes = max(self.max_cache_bytes, sum(len(v) for v in self.interval_cache.values()))

    def read(self, start: int, end: int, depth: int = 0) -> bytes:
        if not (0 <= start <= end <= self.output_bytes):
            raise RuntimeError("out-of-range recursive read")
        if start == end:
            return b""
        if depth > MAX_RECURSION:
            raise RuntimeError("recursive dependency depth exceeded")
        key = (start, end)
        cached = self.interval_cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.recursive_calls += 1
        self.max_depth = max(self.max_depth, depth)
        self.logical_ranges.append(key)
        out = bytearray()
        pos = start
        while pos < end:
            page_end = min(end, ((pos // PAGE) + 1) * PAGE)
            out += self._read_from_anchor(pos, page_end, depth)
            pos = page_end
        got = bytes(out)
        if len(got) != end - start:
            raise RuntimeError("short interval reconstruction")
        self.interval_cache[key] = got
        self._remember_cache_peak()
        return got

    def _copy_slice(self, token_start: int, length: int, distance: int, want0: int, want1: int, depth: int) -> bytes:
        if not (token_start <= want0 < want1 <= token_start + length):
            raise RuntimeError("invalid copy slice")
        n = want1 - want0
        phase = (want0 - token_start) % distance
        base0 = token_start - distance
        if n >= distance:
            seed = self.read(base0, token_start, depth + 1)
            if len(seed) != distance:
                raise RuntimeError("short copy seed")
            return bytes(seed[(phase + i) % distance] for i in range(n))
        first = min(n, distance - phase)
        a = self.read(base0 + phase, base0 + phase + first, depth + 1)
        if first == n:
            return a
        b = self.read(base0, base0 + (n - first), depth + 1)
        return a + b

    def _read_from_anchor(self, start: int, end: int, depth: int) -> bytes:
        page = start // PAGE
        anchor = self.anchors[page]
        self.anchor_frames.add(page)
        out_start = anchor["token_start"]
        out_pos = out_start
        bid = anchor["block_id"]
        br = CONE.BitReader(self.comp)
        br.bit = anchor["bit_start"]
        segment_start = br.bit
        tables = self._tables(bid)
        result = bytearray()
        result_pos = start

        def finish_segment() -> None:
            nonlocal segment_start
            a = segment_start // 8
            b = (br.bit + 7) // 8
            if b > a:
                self.payload_ranges.append((a, b))
            segment_start = br.bit

        while out_pos < end:
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
                self.symbols_parsed += 1
                token_end = token_start + 1
                if token_end > start and token_start < end:
                    if token_start != result_pos:
                        raise RuntimeError("stored-literal result discontinuity")
                    result.append(sym)
                    result_pos += 1
            else:
                ll, dd = tables
                sym = CONE._decode(br, ll)
                self.symbols_parsed += 1
                if sym < 256:
                    token_end = token_start + 1
                    if token_end > start and token_start < end:
                        if token_start != result_pos:
                            raise RuntimeError("literal result discontinuity")
                        result.append(sym)
                        result_pos += 1
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
                    if distance > token_start:
                        raise RuntimeError("distance beyond output")
                    token_end = token_start + length
                    want0 = max(start, token_start)
                    want1 = min(end, token_end)
                    if want0 < want1:
                        if want0 != result_pos:
                            raise RuntimeError("copy result discontinuity")
                        result += self._copy_slice(token_start, length, distance, want0, want1, depth)
                        result_pos = want1
                else:
                    raise RuntimeError("reserved literal/length symbol")
            out_pos = token_end
        finish_segment()
        if result_pos != end or len(result) != end - start:
            raise RuntimeError("interval reconstruction bounds mismatch")
        return bytes(result)


def _run_requests(comp: bytes, expected: bytes, anchors: list[dict], blocks: list[dict], starts: list[int]) -> dict:
    rows = []
    failures = 0
    exact_failures = 0
    max_cache = 0
    total_wall = 0.0
    for start in starts:
        end = min(start + PAGE, len(expected))
        reader = LazyIntervalReader(comp, anchors, blocks, len(expected))
        t0 = time.perf_counter()
        got = reader.read(start, end)
        wall = time.perf_counter() - t0
        total_wall += wall
        exact = got == expected[start:end]
        meta = reader.metadata_bytes()
        payload = reader.payload_bytes()
        logical = reader.logical_dependency_bytes()
        combined = meta + payload
        if not exact:
            exact_failures += 1
        if combined > LIMIT or logical > LIMIT or reader.max_depth > MAX_RECURSION:
            failures += 1
        max_cache = max(max_cache, reader.max_cache_bytes)
        rows.append({
            "start": start,
            "end": end,
            "exact": exact,
            "logical_dependency_bytes": logical,
            "logical_dependency_amplification": logical / max(1, end - start),
            "metadata_bytes_touched": meta,
            "payload_bytes_touched": payload,
            "combined_bytes_touched": combined,
            "combined_amplification": combined / max(1, end - start),
            "anchor_frames": len(reader.anchor_frames),
            "block_frames": len(reader.block_frames),
            "symbols_parsed": reader.symbols_parsed,
            "recursive_calls": reader.recursive_calls,
            "max_recursion_depth": reader.max_depth,
            "cache_hits": reader.cache_hits,
            "cache_bytes_peak": reader.max_cache_bytes,
            "wall_s": wall,
        })
    def worst(key: str):
        return max(rows, key=lambda r: r[key]) if rows else None
    return {
        "requests": len(rows),
        "exact_failures": exact_failures,
        "limit_failures": failures,
        "all_exact_and_bounded": exact_failures == 0 and failures == 0,
        "worst_logical_dependency": worst("logical_dependency_bytes"),
        "worst_combined_io": worst("combined_bytes_touched"),
        "worst_recursion": worst("max_recursion_depth"),
        "worst_symbols": worst("symbols_parsed"),
        "worst_wall": worst("wall_s"),
        "max_cache_bytes_peak": max_cache,
        "total_wall_s": total_wall,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_lazy_interval_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_lazy_interval_repair")
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
    anchors, blocks, metadata_stored = COLD._build_metadata(parsed)
    candidate_bytes = DUAL_OWNER_BYTES + metadata_stored
    density_margin = DUAL.ACCEPTED_V029_ANALYTICS - candidate_bytes

    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fixed = _run_requests(comp, expected, anchors, blocks, TOKEN.starts(len(expected)))
    unaligned = _run_requests(comp, expected, anchors, blocks, _unaligned_starts(len(expected)))
    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    passes = (
        density_margin > 0
        and fixed["all_exact_and_bounded"]
        and unaligned["all_exact_and_bounded"]
    )
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "member": {
            "compressed_bytes": len(comp),
            "compressed_sha256": hashlib.sha256(comp).hexdigest(),
            "raw_bytes": len(expected),
            "raw_sha256": hashlib.sha256(expected).hexdigest(),
            "crc32": info.CRC,
        },
        "metadata": {
            "page_bytes": PAGE,
            "anchors": len(anchors),
            "block_states": len(blocks),
            "stored_bytes_including_frame_auth_and_directory": metadata_stored,
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "dual_owner_plus_metadata_bytes": candidate_bytes,
            "accepted_v029_analytics_bytes": DUAL.ACCEPTED_V029_ANALYTICS,
            "margin_to_v029_bytes": density_margin,
        },
        "fixed_requests": fixed,
        "unaligned_controls": unaligned,
        "host_process": {
            "ru_maxrss_before_kib": rss0,
            "ru_maxrss_after_kib": rss1,
            "delta_ru_maxrss_kib": max(0, rss1 - rss0),
            "note": "process high-water delta only; per-request cache peak is the direct reader-state measure",
        },
        "hypothesis": {
            "lazy_interval_reader_preserves_8x_path_without_full_page_materialization": passes,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_owner_and_metadata_as_cold_reader": True,
            "same_page_bytes": PAGE,
            "same_io_limit_bytes": LIMIT,
            "same_recursion_limit": MAX_RECURSION,
            "no_threshold_sweep": True,
            "no_page_size_sweep": True,
            "no_codec_change": True,
            "no_product_format_change": True,
            "metadata_objects_not_yet_deserialized_from_physical_frames": True,
        },
        "next_if_supported": (
            "persist actual anchor/block frames and read them plus compressed ranges through bounded pread; verify frame hashes, corruption refusal, recovery and held-out NPY relations"
        ),
        "next_if_falsified": (
            "preserve the negative; use the failing logical/payload/recursion owner to choose sub-page anchors, bounded authenticated seed material, or retire sparse-DEFLATE locality for this owner"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-lazy-interval-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-lazy-interval.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({
        "member": d["member"],
        "metadata": d["metadata"],
        "fixed_requests": d["fixed_requests"],
        "unaligned_controls": d["unaligned_controls"],
        "host_process": d["host_process"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
