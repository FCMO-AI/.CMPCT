from __future__ import annotations

"""Resource-plan correction for the lazy-tail Office referee.

The first lazy-tail draft correctly changed compressed-byte ownership, but its mixed-in seeded reader
would have fallen back to recursive prior-page reads because the inherited page decoder did not route
external history through ``SeedReader._seed_read``. That would change the frozen v7 physical plan before
the hypothesis was tested. This wrapper preserves the exact same lazy compressed-window mechanism while
restoring the already-frozen gated-seed semantics. No result from the first draft is accepted.
"""

import json
from pathlib import Path

from benchmarks import v030_r4_office_lazy_tail_window_referee as V1

SCHEMA = 'cmpct-v030-r4-office-lazy-tail-window-v2'


def _prior_recursive(self, page: int, src0: int, prior_end: int, depth: int) -> bytes:
    return self.read(src0, prior_end, depth + 1)


def _prior_seed(self, page: int, src0: int, prior_end: int, depth: int) -> bytes:
    return self._seed_read(page, src0, prior_end)


# Patch the single dependency hook without changing any range, metadata, threshold or decoder rule.
V1.LazyReader._prior = _prior_recursive

_orig_decode = V1.LazyReader._decode_page


def _decode_with_prior_hook(self, page: int, depth: int) -> bytes:
    # This is the v1 decoder with exactly one semantic correction: external history is obtained through
    # ``self._prior`` so ordinary readers recurse and seeded readers consume the frozen seed frame.
    cached = self.page_cache.get(page)
    if cached is not None:
        return cached
    anchor = self.anchors[page]
    self.anchor_frames.add(page)
    page_base = page * V1.PAGE
    page_end = min(page_base + V1.PAGE, self.output_bytes)
    out_start = anchor['token_start']
    out_pos = out_start
    local = bytearray()
    bid = anchor['block_id']
    win = self.comp.open_page(page)
    br = V1.LazyBulkBitReader(win, anchor['bit_start'])
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
            sym = V1.CONE._decode(br, ll)
            self.symbols_decoded += 1
            if sym < 256:
                token = bytes([sym])
            elif sym == 256:
                if out_pos != block['out_end']:
                    raise RuntimeError('early EOB relative to persisted block state')
                continue
            elif 257 <= sym <= 285:
                li = sym - 257
                length = V1.CONE.LEN_BASE[li] + br.read(V1.CONE.LEN_EXTRA[li])
                ds = V1.CONE._decode(br, dd)
                if ds >= len(V1.CONE.DIST_BASE):
                    raise RuntimeError('invalid distance symbol')
                distance = V1.CONE.DIST_BASE[ds] + br.read(V1.CONE.DIST_EXTRA[ds])
                if distance > out_pos:
                    raise RuntimeError('distance beyond output')
                seed_len = min(distance, length)
                src0 = out_pos - distance
                src1 = src0 + seed_len
                seed = bytearray()
                if src0 < out_start:
                    prior_end = min(src1, out_start)
                    seed += self._prior(page, src0, prior_end, depth)
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


V1.LazyReader._decode_page = _decode_with_prior_hook
V1.LazySeedReader._decode_page = _decode_with_prior_hook
V1.LazySeedReader._prior = _prior_seed
V1.SCHEMA = SCHEMA


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    d = V1.run(work, v029_checkout, worker)
    d['schema'] = SCHEMA
    d['contract']['seeded_external_history_uses_frozen_seed_frames'] = True
    d['contract']['v1_draft_receives_no_evidence_credit'] = True
    return d


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-r4-office-lazy-tail-work'))
    p.add_argument('--v029-checkout', type=Path, required=True)
    p.add_argument('--worker', type=Path, default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-r4-office-lazy-tail-window-v2.json'))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'lazy_tail': d['lazy_tail'], 'hypothesis': d['hypothesis'], 'profile': d['profile']}, sort_keys=True))


if __name__ == '__main__':
    main()
