# J24G60 — standard Writer single-delta chain cold-open cost (prospective preregistration)

Date: 2026-10-30 UTC
Status: PREREGISTERED BEFORE CODE / RESULTS / CI. This document is not a release receipt.
Source owner: #795 (exact parent commit `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`).
Adjacent scientific result: #798 (J24G59), source-exact three-host court #40991811610: public Writer emits exactly one op per committed delta; #797's >=16-op fast path is not entered by ordinary public mutations.
Scope: independently measure **cross-generation chain replay**, not repeat #798's op-width test or #797's synthetic 4096-op speed claim. Product and release law remain unchanged.

## Primary falsifiable question
For a real r24 Builder archive modified by 63 **ordinary public** Writer renames, is fresh-process `CMPCT(...)` open materially slower or more memory-intensive than a logically identical archive with a final **explicit synthetic full checkpoint**? Which fraction scales with file count N vs chain depth d? Can a cheap checkpoint explain enough of the observed gap that cross-generation reuse/indexing is worth implementing?

## Design, predicted result, and strong controls
- Construct deterministic, generically named r24 source trees of N=512 and N=2048 regular files, then perform 63 valid unique-root renames through `transactions.append_rename`. Capture snapshots at depths 1,16,32,63; preserve the exact source archive bytes and recorded footer linkage.
- For each snapshot, create a **separate experiment-only** full checkpoint with identical effective index (`_append_generation(checkpoint_index=...)`), leaving the actual Writer archive untouched. Compare `Reader.index` and file-read content with both snapshots to authenticate same semantics. Charge the complete extra archive bytes and distinguish any candidate checkpoint from a normal 64th public mutation.
- Time fresh-process **Reader open only** with `perf_counter_ns` and `process_time_ns`, multiple alternating A/B/B/A and B/A/A/B blocks; retain individual raw samples and startup-outside-timed boundaries. Process VmHWM on Linux, measured separately if possible; other hosts may report null rather than false equivalence. Also measure `preflight_archive` on a limited paired subset when feasible.
- Parse all relevant footer chains using independent standard MessagePack/Zstandard bytes+SHA, not only Reader `delta_depth`; cross-check exact Git source blobs and installed module files.
- Contrast 1-op chain vs explicit checkpoint at **identical logical tree**. A checkpoint's extra bytes and another write are real costs; this experiment will not claim that the standard public Writer currently produces a depth-63 same-state checkpoint. The hypothetical checkpoint is a *charged oracle*, not a shipping improvement.
- Strong simpler alternative: the 64th **existing** public Writer mutation checkpoints automatically. Its fact and bytes can explain part of the observed gap without implementing new index machinery. A no-journal original Builder archive establishes a fixed source/open cost floor.
- Plausible alternative: Python import, filesystem page cache, footer scanning, index decompression, reader validation or native library load dominates and the old replay may not matter. Capture wall+CPU, historical footer widths/record sizes and process scope; never assert cold-device I/O from fresh-process timing.
- Expected direction if expensive chain replay dominates: ratio chain/checkpoint rises with N*d; preflight may differ because its bounded validation has separate costs. **Decision-changing materiality**: >=10% AND >=3 ms in matched medians at N=2048,d=63 with correct archive semantics and no integrity red. This is a research allocation threshold, NOT a change to official release gate. If below that, prefer simpler existing checkpoint behavior; no optimization implementation.
- Kill/narrow conditions: any actual Writer delta with unexpected width/commit, non-identical indexes or member bytes, mismatched source SHA, hostile logical admission, or absent matched samples makes performance claims inconclusive; no partial green accepted as product evidence.

## Concurrency and evidence ladder
#795 owns signed-op grammar and Reader/preflight shared replay, #797 owns a private wide-generation index, #798 owns public Writer reachability, #574 owns Discovery state. J24G60 changes only new research documents, an isolated scientific harness and isolated workflow on its own exact parent. No shared source changes, no copied release scores, no merged product claims.
Use the cheap physical A/B first. Only if material, consider an additional owner-aligned cross-generation optimization with complete RSS/temp/storage/recovery/hostile tests.

## Frozen conditions
Do not change v0.30.0, format r24, existing decoder, writer, benchmarks, release evaluator/thresholds, legacy conformance tests, or `docs/discovery/STATE.json`. An ordinary Writer archive must remain a valid baseline. Record all negative evidence, including any CI/instrument failures. Public-safe corpus only. No inferred performance win until hosted source-exact evidence exists.
