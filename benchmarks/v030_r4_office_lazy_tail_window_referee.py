from __future__ import annotations

"""Transfer a lazy-tail bounded compressed window to the frozen Office v7 candidate.

Mission lock
============
The full bounded-window transfer preserved exact reconstruction but failed the frozen 8x law by only
39 B: worst charged read 32,807 B versus 32,768 B. Its page window eagerly reserved the RFC-1951
48-bit token guard at every straddling boundary, producing 49,710 B aggregate physical over-read.
The earlier fixed PREAD8 control remained under 8x with much less over-read, proving that Office v7
itself is not the failure.

This referee keeps the frozen v7 archive economics (5,952,805 B), 644 B metadata grouping, 360 B
locator/root charge, seed selector, 4 KiB request and 8x law. A page preads only through the next
persisted token start. If decoding a boundary-straddling token actually needs more compressed bytes,
the bit reader extends that same contiguous page window *only through the byte currently required*.
No threshold/refill sweep and no archive-sized compressed buffer are allowed. Bulk <=24-bit field
extraction is reused from the independently adjudicated exact-identity referee.

Disproof
========
Any byte mismatch, uncovered consumed compressed byte, live page window >32,768 B, or fixed/page-pair
charged read >32,768 B falsifies the mechanism. The 8x ceiling, metadata groups and representation
bytes do not move. Aggregate physical over-read must also be lower than the failed eager-window
49,710 B receipt; otherwise the proposed cause was not removed.
"""

import argparse, hashlib, json, os, time, zlib
from pathlib import Path

from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sparse_superframe_economic_referee as SUPER
from benchmarks import v030_r4_office_group_charge_locality_referee as GROUP
from benchmarks import v030_r4_office_payload_pread8_referee as PREAD8
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA = 'cmpct-v030-r4-office-lazy-tail-window-v1'
PAGE = 4096
LIMIT = 8 * PAGE
FAILED_EAGER_OVERFETCH = 49_710
FAILED_EAGER_WORST = 32_807
MAX_FIELD_BITS = 24


class _LazyPageWindow:
    def __init__(self, owner, page: int, lo: int, hi: int):
        self.owner = owner
        self.page = page
        self.lo = lo
        self.data = bytearray()
        self._extend(hi)

    @property
    def hi(self) -> int:
        return self.lo + len(self.data)

    def _extend(self, hi: int) -> None:
        hi = min(self.owner.size, hi)
        if hi <= self.hi:
            return
        start = self.hi
        got = os.pread(self.owner.fd, hi - start, start)
        if len(got) != hi - start:
            raise RuntimeError('short lazy-tail pread')
        self.data += got
        self.owner.ranges.append((start, hi))
        self.owner.calls += 1
        self.owner.max_live_window_bytes = max(self.owner.max_live_window_bytes, len(self.data))

    def ensure(self, abs_hi: int) -> None:
        if abs_hi > self.owner.size:
            raise ValueError('lazy-tail window beyond compressed stream')
        self._extend(abs_hi)


class LazyTailSource:
    def __init__(self, fd: int, size: int, anchors: list[dict]):
        self.fd = fd
        self.size = size
        self.anchors = anchors
        self.pages = set()
        self.ranges = []
        self.calls = 0
        self.max_live_window_bytes = 0

    def open_page(self, page: int) -> _LazyPageWindow:
        if page in self.pages:
            raise RuntimeError('page window requested twice after decoded-page cache')
        a = self.anchors[page]
        start_bit = int(a['bit_start'])
        if page + 1 >= len(self.anchors):
            end_bit = self.size * 8
        else:
            n = self.anchors[page + 1]
            boundary = (page + 1) * PAGE
            if int(n['token_start']) > boundary:
                raise RuntimeError('next anchor starts after page boundary')
            # Stop at the next persisted token start. If that token straddles the logical page
            # boundary the bit reader extends on demand, instead of reserving MAX_TOKEN_BITS eagerly.
            end_bit = int(n['bit_start'])
        lo = start_bit // 8
        hi = (end_bit + 7) // 8
        self.pages.add(page)
        return _LazyPageWindow(self, page, lo, hi)

    def physical_ranges(self):
        return SRC.G._merge(self.ranges) if hasattr(SRC, 'G') else _merge(self.ranges)


def _merge(rs):
    if not rs:
        return []
    out = [list(x) for x in sorted(rs)]
    merged = [out[0]]
    for a, b in out[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


class LazyBulkBitReader:
    def __init__(self, window: _LazyPageWindow, bit: int):
        self.window = window
        self.bit = bit

    def read(self, n: int) -> int:
        if n == 0:
            return 0
        if n < 0 or n > MAX_FIELD_BITS:
            raise ValueError('unexpected DEFLATE field width')
        byte_abs = self.bit >> 3
        shift = self.bit & 7
        need = (shift + n + 7) >> 3
        self.window.ensure(byte_abs + need)
        idx = byte_abs - self.window.lo
        if idx < 0 or idx + need > len(self.window.data):
            raise ValueError('lazy-tail compressed window exhausted')
        word = self.window.data[idx]
        if need > 1:
            word |= self.window.data[idx + 1] << 8
        if need > 2:
            word |= self.window.data[idx + 2] << 16
        if need > 3:
            word |= self.window.data[idx + 3] << 24
        value = (word >> shift) & ((1 << n) - 1)
        self.bit += n
        return value

    def align(self):
        self.bit = (self.bit + 7) & ~7


class LazyReader(COLD.ColdReader):
    def _decode_page(self, page: int, depth: int) -> bytes:
        cached = self.page_cache.get(page)
        if cached is not None:
            return cached
        anchor = self.anchors[page]
        self.anchor_frames.add(page)
        page_base = page * PAGE
        page_end = min(page_base + PAGE, self.output_bytes)
        out_start = anchor['token_start']
        out_pos = out_start
        local = bytearray()
        bid = anchor['block_id']
        win = self.comp.open_page(page)
        br = LazyBulkBitReader(win, anchor['bit_start'])
        segment_start = br.bit
        tables = self._tables(bid)

        def finish_segment():
            nonlocal segment_start
            a = segment_start // 8
            b = (br.bit + 7) // 8
            if b > a:
                self.payload_ranges.append((a, b))
            segment_start = br.bit

        while out_pos < page_end:
            block = self.blocks[bid]
            if out_pos >= block['out_end']:
                finish_segment()
                bid += 1
                if bid >= len(self.blocks):
                    raise RuntimeError('ran beyond final DEFLATE block')
                block = self.blocks[bid]
                br.bit = block['first_token_bit']
                segment_start = br.bit
                tables = self._tables(bid)
            token_start = out_pos
            if block['type'] == 0:
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
                    if out_pos != block['out_end']:
                        raise RuntimeError('early EOB relative to persisted block state')
                    continue
                elif 257 <= sym <= 285:
                    li = sym - 257
                    length = CONE.LEN_BASE[li] + br.read(CONE.LEN_EXTRA[li])
                    ds = CONE._decode(br, dd)
                    if ds >= len(CONE.DIST_BASE):
                        raise RuntimeError('invalid distance symbol')
                    distance = CONE.DIST_BASE[ds] + br.read(CONE.DIST_EXTRA[ds])
                    if distance > out_pos:
                        raise RuntimeError('distance beyond output')
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
                            raise RuntimeError('local LZ77 history unavailable')
                        seed += local[lo:hi]
                    if len(seed) != seed_len or not seed:
                        raise RuntimeError('failed to reconstruct LZ77 seed')
                    token = bytes((seed * ((length + len(seed) - 1) // len(seed)))[:length])
                else:
                    raise RuntimeError('reserved literal/length symbol')
            local += token
            out_pos = token_start + len(token)
        finish_segment()
        begin = page_base - out_start
        if begin < 0 or page_end - out_start > len(local):
            raise RuntimeError('page reconstruction bounds mismatch')
        page_bytes = bytes(local[begin:page_end - out_start])
        if len(page_bytes) != page_end - page_base:
            raise RuntimeError('short page reconstruction')
        self.page_cache[page] = page_bytes
        return page_bytes


class LazySeedReader(SEED.SeedReader, LazyReader):
    # Reuse SeedReader._seed_read while taking the page decoder above.
    _decode_page = LazyReader._decode_page


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    t0 = time.perf_counter()
    base = PREAD8.run(work, v029_checkout, worker)
    if base['frozen_v7']['candidate_bytes'] != 5_952_805 or base['frozen_v7']['grouped_metadata_bytes'] != 48_787:
        raise RuntimeError('frozen v7 economics drift')
    manifest = json.loads((work / 'current' / 'manifest.json').read_text())
    pool = (work / 'current' / 'streams.bin').read_bytes()
    hashes = sorted({r['stream_hash'] for r in manifest['derived'].values()})
    fixed = pair = exact_fail = locality_fail = pair_fail = cover_fail = 0
    worst = worst_pair = None
    max_window = physical_total = logical_total = calls_total = 0

    for si, h in enumerate(hashes):
        s = manifest['stream_index'][h]
        comp = pool[s['o']:s['o'] + s['n']]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        anchors, blocks, _ = COLD._build_metadata(parsed)
        seeds, _all, _logical = SEED._build_seeds(parsed, anchors, raw)
        brecs, arecs = SUPER._encoded_records(parsed)
        bmap, bcost, _ = PREAD8._pack644([(int(r['key']), r['encoded']) for r in brecs], f's{si}:b')
        amap, acost, _ = PREAD8._pack644([(int(r['key']), r['encoded']) for r in arecs], f's{si}:a')
        pages = len(anchors)
        unsafe = set()
        selected = set()
        for p in range(pages):
            a = p * PAGE
            b = min(len(raw), min(pages, p + 2) * PAGE)
            r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            if r.read(a, b) != raw[a:b]:
                raise RuntimeError('classifier exactness drift')
            if r.metadata_bytes() + r.payload_bytes() > LIMIT:
                unsafe.add(p)
                selected.add(p)
                if p + 1 < pages:
                    selected.add(p + 1)
        gated = [None] * pages
        seed_records = []
        for p in sorted(selected):
            if seeds[p] is None:
                continue
            enc = GROUP._seed_enc(p, anchors[p], parsed, raw)
            if enc is None or hashlib.sha256(enc).hexdigest() != seeds[p]['frame_sha256']:
                raise RuntimeError('seed parity drift')
            gated[p] = seeds[p]
            seed_records.append((p, enc))
        smap, scost, _ = PREAD8._pack644(seed_records, f's{si}:s')
        costs = {**bcost, **acost, **scost}
        path = work / f'lazy-window-stream-{si}.deflate'
        path.write_bytes(comp)
        fd = os.open(path, os.O_RDONLY)
        try:
            def probe(a, b, seed_mode):
                src = LazyTailSource(fd, len(comp), anchors)
                cls = LazySeedReader if seed_mode else LazyReader
                r = cls(src, anchors, blocks, gated, len(raw)) if seed_mode else cls(src, anchors, blocks, len(raw))
                got = r.read(a, b)
                physical = SRC._bytes(_merge(src.ranges))
                meta = GROUP._charge_groups(r, amap, bmap, smap, costs)
                combined = physical + meta + PREAD8.LOCATOR_ROOT_CHARGE
                covered = SRC._covers(src.ranges, r.payload_ranges)
                return got, r, src, physical, meta, combined, covered

            for p in range(pages):
                a = p * PAGE
                b = min(len(raw), min(pages, p + 2) * PAGE)
                got, r, src, physical, meta, combined, covered = probe(a, b, p in unsafe)
                pair += 1
                logical_total += r.payload_bytes()
                physical_total += physical
                calls_total += src.calls
                max_window = max(max_window, src.max_live_window_bytes)
                if got != raw[a:b] or combined > LIMIT or not covered:
                    pair_fail += 1
                q = {'stream_sha256': h, 'pair_start_page': p, 'logical_payload_bytes': r.payload_bytes(), 'physical_payload_bytes': physical, 'metadata_bytes': meta, 'combined_bytes': combined, 'slack_bytes': LIMIT - combined, 'calls': src.calls, 'max_live_window_bytes': src.max_live_window_bytes, 'covered': covered}
                if worst_pair is None or combined > worst_pair['combined_bytes']:
                    worst_pair = q

            for start in TRANSFER._starts(len(raw)):
                end = min(start + PAGE, len(raw))
                p0 = start // PAGE
                p1 = (end - 1) // PAGE
                seed_mode = (p0 in unsafe) if p1 != p0 else (p0 in unsafe or (p0 > 0 and (p0 - 1) in unsafe))
                got, r, src, physical, meta, combined, covered = probe(start, end, seed_mode)
                fixed += 1
                logical_total += r.payload_bytes()
                physical_total += physical
                calls_total += src.calls
                max_window = max(max_window, src.max_live_window_bytes)
                if got != raw[start:end]:
                    exact_fail += 1
                if combined > LIMIT:
                    locality_fail += 1
                if not covered:
                    cover_fail += 1
                q = {'stream_sha256': h, 'start': start, 'end': end, 'logical_payload_bytes': r.payload_bytes(), 'physical_payload_bytes': physical, 'metadata_bytes': meta, 'combined_bytes': combined, 'slack_bytes': LIMIT - combined, 'calls': src.calls, 'max_live_window_bytes': src.max_live_window_bytes, 'covered': covered}
                if worst is None or combined > worst['combined_bytes']:
                    worst = q
        finally:
            os.close(fd)

    overfetch = physical_total - logical_total
    supported = exact_fail == 0 and locality_fail == 0 and pair_fail == 0 and cover_fail == 0 and max_window <= LIMIT and overfetch < FAILED_EAGER_OVERFETCH
    return {
        'schema': SCHEMA,
        'source_commit': os.environ.get('EVIDENCE_HEAD'),
        'frozen_v7': base['frozen_v7'],
        'pread8_control': {
            'hypothesis_supported': base['hypothesis']['eight_byte_exact_start_pread_refill_preserves_office_8x'],
            'total_logical_payload_bytes': base['physical_refill']['total_logical_payload_bytes'],
            'total_physical_payload_bytes': base['physical_refill']['total_pread_payload_bytes'],
            'total_pread_calls': base['physical_refill']['total_pread_calls'],
        },
        'failed_eager_window_reference': {'aggregate_overfetch_bytes': FAILED_EAGER_OVERFETCH, 'worst_combined_bytes': FAILED_EAGER_WORST},
        'lazy_tail': {
            'fixed_requests': fixed, 'pair_requests': pair, 'exact_failures': exact_fail,
            'locality_failures': locality_fail, 'pair_failures': pair_fail, 'coverage_failures': cover_fail,
            'total_logical_payload_bytes': logical_total, 'total_physical_payload_bytes': physical_total,
            'physical_minus_logical_bytes': overfetch, 'total_pread_calls': calls_total,
            'max_live_window_bytes': max_window, 'worst_fixed_probe': worst, 'worst_page_pair': worst_pair,
        },
        'hypothesis': {'lazy_tail_removes_eager_guard_overfetch_and_restores_office_8x': supported},
        'contract': {
            'diagnostic_only': True, 'release_credit': False, 'candidate_bytes_unchanged': True,
            'same_644b_metadata_groups': True, 'same_locator_root_charge': True, 'same_8x_limit': True,
            'same_seed_selector': True, 'actual_os_pread_drives_bit_decoder': True,
            'no_archive_sized_compressed_buffer': True, 'no_refill_or_threshold_sweep': True,
            'max_field_bits': MAX_FIELD_BITS,
            'remaining_debt': 'if supported: fresh-process throughput/CPU/RSS, serialized auth/root/recovery and native parity; if false: preserve exact excess and redesign compressed-range ownership without moving 8x',
        },
        'profile': {'wall_s_including_pread8_control': time.perf_counter() - t0},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-r4-office-lazy-tail-work'))
    p.add_argument('--v029-checkout', type=Path, required=True)
    p.add_argument('--worker', type=Path, default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-r4-office-lazy-tail-window.json'))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'lazy_tail': d['lazy_tail'], 'hypothesis': d['hypothesis'], 'profile': d['profile']}, sort_keys=True))


if __name__ == '__main__':
    main()
