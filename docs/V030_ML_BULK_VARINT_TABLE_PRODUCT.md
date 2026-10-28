# v0.30 ML DGO1 bulk one-byte length-table parsing — productization evidence

Status: **scoped product mechanism implemented; exact-parent extraction transfer earned; unchanged product gates still required before convergence**.

Current exact parent: `agent/v030-authoritative-integration@cab8e8dc21595b8bb342e0b39c18e06c91a16b7b`; production remains v0.29.0/r24 and v0.30 remains release-locked.

## Mechanism and ownership

The promoted single-buffer delimiter inverse already belongs to the exact parent and remains the global/default behavior. PR #152 does **not** delete or replace that earned owner. Instead:

1. `release_single_buffer_delimiter_inverse(..., bulk_one_byte_table=False)` preserves exact-parent default parsing;
2. `release_bulk_one_byte_table_delimiter_inverse` opts into the bulk one-byte-table parser explicitly;
3. `_G04Session` owns a delimiter-inverse callable per session and defaults to the promoted global inverse;
4. `_stream_g04` propagates that explicit capability;
5. only `extract_verified_into_staging()` injects the bulk callable for unpublished verified staging extraction.

There is no temporary process-global mutation. Ordinary readers, selective reads, `strong_verify`, and create-side verification continue to observe the exact-parent promoted inverse even while a verified-staging extraction is in flight.

For the bulk route, after decoding and bounding `count`, the parser inspects exactly the next `count` descriptor bytes. `bytes.isascii()` proves every byte has continuation bit clear (`<0x80`); only then are the lengths materialized directly. A short slice or any high-bit byte falls back to the unchanged generic `_get_varint` grammar. Logical-size, cumulative-length, cell-work, body-size, output-shape and trailing/body accounting remain mandatory.

## Evidence lineage

Research PR #151 run `35439489634`, artifact `10582959452`, first established 23.8592% median ML extraction headroom with exact output identity and explicit 130/257-byte multi-varint fallback.

The earlier product run `35442048869` measured 23.2963% median wall / 23.2994% CPU against its then-exact parent, but its implementation exposed the bulk parser globally. Unchanged r24/ZIP run `35442276749` preserved archive bytes but found create regressions on media (+15.64%, +4.52 ms) and nested (+24.53%, +3.96 ms). That red is preserved as the causal reason global ownership is non-promotable.

Exact-parent audit then corrected an initially over-broad repair idea: deleting the global release inverse would itself revert the previously promoted single-buffer optimization. The correct repair is **parent default globally + staging-only bulk capability**, as implemented here.

## Current strongest-control product evidence

Scoped exact-parent A/B run `35460272188`, candidate source `d9146e3c661f71f47c4f38b235c08d3003125a8c`, control `cab8e8dc21595b8bb342e0b39c18e06c91a16b7b`, durable record `benchmarks/history/v030_ml_bulk_varint_scope_parent_d9146e3c661f.json`:

- wall improvements: **23.4353%, 23.4914%, 23.6272%, 22.9071%**;
- median wall improvement: **23.4633%**;
- median CPU improvement: **23.4590%**;
- exact reconstructed tree SHA-256 in every arm;
- fresh-process median `ru_maxrss` ratio: **1.0x**;
- block-I/O deltas identical in every paired arm (`inblock=0`, `oublock=35512`).

Post-#155 authoritative runtime requires only **7.4722%** relative ML extraction improvement to bring ML to 1.10x and remove the current aggregate-median owner. The scoped product retains about 3.14x that hurdle in this exact-parent A/B. This is product evidence, not release credit: unchanged authoritative runtime after convergence owns the frozen release decision.

## Hostile / concurrency proof

Permanent tests now cover:

- one-byte bulk equivalence against both the promoted single-buffer default and the historical independent inverse;
- explicit multi-byte lengths 130 and 257 through exact generic fallback;
- malformed/truncated rejection through default, bulk and historical readers;
- staging-only capability injection without global mutation;
- an in-flight verified-staging extraction blocked in another thread while shared strict/create-side inverse ownership remains the promoted default before, during and after the call.

No selector, threshold, writer byte, format revision, benchmark identity, locality law or integrity check changes.

## Completion gates

- [x] bounded one-byte mechanism and exact generic fallback;
- [x] preserve exact-parent promoted single-buffer inverse as global/default owner;
- [x] scope only the bulk capability to verified staging;
- [x] one-byte, 130/257 multi-byte and malformed/truncated equivalence regressions;
- [x] concurrent strict/create-vs-fast-staging ownership proof;
- [x] exact-parent fresh-process extraction A/B retains material headroom with exact tree, RSS and block-I/O accounting;
- [ ] unchanged r24/ZIP gate green: zero byte regressions and no confirmed timing regression;
- [ ] exact-head normal CI green after the final scoped product/evidence tree;
- [ ] authoritative runtime gate after convergence decides the frozen extraction ceilings.

The mechanism must be retired or repaired rather than promoted if unchanged r24/ZIP or authoritative runtime remains red for a causally attributable product regression.