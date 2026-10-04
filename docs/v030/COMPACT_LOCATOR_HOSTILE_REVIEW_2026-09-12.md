# v0.30 compact monotone locator — hostile-review chain (2026-09-12)

Status: **Forge research evidence; no canonical r25 / release credit.**

This note preserves the negative chain after the Office 644-byte three-family locality result. It is
not a release note and does not alter the frozen ONE Genesis result or the v0.29 canonical baseline.

## Last adjudicated economic/locality authority before this hostile-review chain

Hosted run `34709794379` (`ebb1952c0cf05a3b5fe6ae45562b3cc433286701`) established the compact
monotone locator v2 diagnostic result on the same Office candidate and frozen source-sealed v0.29:

- compact locator raw: **321 B**;
- compressed locator body: **264 B**;
- authenticated locator frame: **312 B**;
- primary + tail + footer: **672 B**;
- candidate with locality metadata: **5,952,805 B**;
- frozen same-input v0.29: **5,954,026 B**;
- density margin: **1,221 B**;
- worst charged 4 KiB selective read: **32,746 B = 7.9946289x**;
- remaining locality slack: **22 B**;
- primary-locator corruption rejected with exact tail recovery under the same footer root;
- group-body corruption detected; corrupt footer root rejects both copies.

That result remains diagnostic. The footer root is not yet bound to a canonical archive trust anchor.

For comparison, the immediately preceding ordinary serialized directory cost 4,320 B, produced a
5,956,453 B candidate (2,427 B worse than v0.29), and retained only 10 B of locality slack. The compact
locator therefore recovered the crossing by removing redundant directory description, not by omitting
metadata.

## Hostile Review 1 — decompression allocation ordering

v1/v2 read the compressed locator with `zlib.decompress(body)` and checked the 1 MiB expanded-size
ceiling only *after* decompression. A small hostile body could therefore allocate far beyond the claimed
reader limit before rejection.

`v030_r4_office_compact_monotone_directory_v3.py` changes no persisted representation/economics. It uses
`decompressobj().decompress(..., MAX_RAW+1)` and fails closed on >1 MiB output, incomplete streams,
unconsumed compressed input or concatenated/trailing streams. Hosted exact-head run `34710381998` is the
receipt lane for this intermediate fix. **v2 must not be treated as the resource-bounded reader authority.**

## Hostile Review 2 — parsed object-graph amplification

Bounding the raw locator to 1 MiB was still insufficient because the inherited parser materialized a
Python dict of lists of `(key, offset)` tuples. A valid near-ceiling locator can therefore amplify one
bounded byte buffer into a much larger object graph.

`v030_r4_office_compact_monotone_directory_v4.py` preserves the exact LOC1 bytes but validates canonical
uvarints, family order, unique/monotone stream ids and full consumption in one pass, then exposes lazy
family iterators over the already bounded raw bytes. No retained per-record table is required. A
near-ceiling synthetic canonical locator (>100k records) is an explicit hostile control. Hosted exact-head
run `34710639121` is the intermediate receipt lane. **v3 must not be treated as parser-state authority.**

A separate fresh-process resource referee (`v030_r4_compact_locator_parser_resource_referee.py`) compares
legacy and streaming parsers on identical deterministic near-ceiling bytes. Timing is reported rather than
threshold-tuned; peak RSS is the causal test for the removed table.

## Hostile Review 3 — compressed length is not raw length

v3/v4 compared compressed `body_len` to the 1 MiB *raw* ceiling. DEFLATE can expand incompressible input
slightly, so this conflated two independent resource bounds and could reject a raw-valid frame.

For `n = 1,048,576`, zlib's `compressBound` formula
`n + (n>>12) + (n>>14) + (n>>25) + 13` is **1,048,909 B**. The reader therefore needs both:

- compressed-input ceiling: **1,048,909 B**;
- expanded/raw ceiling: **1,048,576 B**.

v5 implemented this split but used `os.urandom` to construct its incompressible hostile control. That makes
the *evidence input* probabilistic even though the mechanism is deterministic, so v5 is explicitly
non-authoritative. v6 replaces the control with fixed-seed deterministic bytes and keeps every product
parameter unchanged. Its corrected exact-head receipt lane is
`.github/workflows/v030-r4-office-compact-monotone-directory-v6b.yml`.

## Trust-anchor locality debt

The v2 cold-read authority has only **22 B** of slack. A standalone fully cold SHA-256 external trust
anchor is **32 B**, so charging it independently would produce **32,778 B**, ten bytes beyond the frozen
32,768 B / 8x limit.

This is a semantic fork, not permission to hide cost. Promotion must either:

1. reclaim at least 10 B of worst-case cold locality before charging a standalone root; or
2. bind the locator root into authenticated archive-open state and account acquisition/verification of
   that state explicitly under the product's access semantics.

`v030_r4_office_locator_trust_anchor_budget_referee.py` freezes this arithmetic negative. A trust root may
not become free merely because a diagnostic footer contains a hash of its own sibling frame.

## Promotion debt intentionally still open

Even if deterministic v6 passes, the Office locator remains Forge evidence rather than a canonical r25
reader. Open debt includes canonical archive-root binding, broader malformed-input/fuzz transfer,
fresh-process end-to-end reader CPU/RSS/throughput, physical payload `pread` semantics beyond the research
prerequisites, recovery integration, native-reader parity, platform portability and held-out workload
transfer. With only 22 B of measured locality slack, none of these costs may be silently added.
