# A15-O0 — universal typed reconstruction miniature: exact hosted result and cost boundaries

**Date:** 2026-10-28 UTC. **Classification:** bounded Foundry oracle / science only. **Decision:** FEASIBLE_RESEARCH_SEED on the preregistered five synthetic families, **NOT** demonstrated universal-reader simplification or release/product progress.

## Source, prospective control, experiment custody
- Immutable published reference: main 80c358f8824ec1b20d349c92ed94c898090969b0; shipping v0.30.0, format r24.
- Frozen prediction **before code**: commit 6eaf4c66a422c3136dc8b732a697ceb6f9669ff7, docs/v031-research/2026-10-28-a15-o0-typed-reconstruction-prereg.md.
- Source-exact result-bearing experimental HEAD: 7814a61f57cd4eaa4f6d6f45da94e8ec91e81579. GitHub Actions [scientific court 40694211153](https://github.com/FCMO-AI/.CMPCT/actions/runs/40694211153), 2026-10-28T13:12:10Z **SUCCESS**.
- Raw GitHub artifact ID **12818417105**, artifact ZIP SHA-256 **5d77ae0b969d31c9071e79ec73e3df566aaccf9689638a7e6335c3f1c8b4d456**. Original ZIP verified independently outside the hosted court: 47 entries, ZIP CRC all good, source/content artifact and raw timing-medial fields checked, zero discrepancies.
- Installed dependencies: Ubuntu-24.04 scientific host, system libzstd and standalone Zstd CLI. No CMPCT Builder/Reader imported; no real .cmpct archive built. The hosted result is not multi-host.
- Independent referee program uses a separately coded frame parser, subprocess Zstd decompression and reverse transforms, without importing the producer/decoder. It replays all 205 source members, exact digests, encoded lengths, and all CPU/wall medians. It rejects **10/10** deliberately forged receipts. The oracle rejects **60/60** malformed envelopes (12 per five one-member cases).

## Headroom, equality and negative families
Every family has independent 1-, 8- and 32-member cohorts, 15 cases total. Every member reconstructed byte-exact and verified by SHA-256. Each arm uses **the same** selected depth<=2 operation, same uncompressed bytes, same Zstd-19 frame and same per-member seek boundary. The bespoke control uses direct specialized plan dispatch. Shared catalogs are charged once per cohort in both arms. The typed IR pays a one-byte type tag per instruction.

**Held-out 32-member cohorts, measured on actual hosted artifact:**

| Source family | Direct member-seek Zstd-19 control (B) | Best bespoke (B) | Typed IR (B) | IR overhead vs bespoke | IR/bespoke decode wall | IR/bespoke decode CPU |
|---|---:|---:|---:|---:|---:|---:|
| 16-bit lane | 90,531 | 67,810 | 67,813 | +3 B | 0.9991x | 0.9990x |
| 32-bit lane | 94,993 | 19,578 | 19,580 | +2 B | 0.9972x | 0.9971x |
| smooth difference | 50,471 | 31,070 | 31,073 | +3 B | 1.0008x | 1.0003x |
| zero/literal burst | 48,182 | 48,162 | 48,163 | +1 B | 0.9935x | 0.9933x |
| high entropy | 132,748 | 132,748 | 132,748 | 0 B | 1.0461x | 1.0450x |

The direct controls were calculated independently after hosted execution using exact member source bytes and system libzstd level 19, the same 9 B envelope head, 3 B direct program catalog and 42 B/member descriptor size. This is a **post-result stronger control**, not a frozen proposed oracle arm. Direct member frames preserve the same member-level access boundary; a solid single Zstd frame is not misrepresented as same-semantics random access.

The preregistered A15-O0 storage and median decode thresholds pass in **5/5** held-out families. That establishes only that this restricted typed instruction encoding can represent these operations with low descriptor and dispatch cost. It **does not establish** that typed IR reduces source complexity, improves archive compression beyond the already chosen transforms, or replaces current CMPCT reader grammars.

Two especially important negatives:
1. **High-entropy inputs:** the fallback wins unchanged; typed IR contributes **zero** storage saving and has a 4.61% observed wall slowdown. Its encoding is not a compression innovation.
2. **Zero/literal family:** 30/32 held-out members choose direct; only two choose the zero operator. The candidate's almost-zero size improvement versus direct indicates no broadly useful gain from this operator within the tested mixture.

On numeric and smooth-difference families, gains versus direct arise from shared reversible transforms, **not from the typed IR**; those classes already have prior A05/Geometry research. No unique information relationship was invented by this O0 result.

## Economics and proof limitations
- Observations: 15 cases × two arms × 7 raw medians, measured in one hosted process. Decode CPU/wall observations are not independent fresh-process timings, and sample order is not a source-locked ABBA trial.
- Member-level seekability is encoded by independent member frames; cold-open/index search overhead, physical read amplification, full Reader peak RSS and temp I/O were **not** measured. Each requested member still requires its own full encoded frame decode.
- Source/build search, Zstd frame creation, program nomination cost, complete filesystem fidelity, cross-file graphs, nested ZIP, updates, recovery, transaction boundaries, integrity across external references and selective cryptographic proof are untested.
- The decoder shares primitive inverse implementations with the bespoke arm. A thin interpreter dispatch layer cannot honestly claim reduced *maintenance surface*. The strongest alternative, a simple shared enum/switch, remains available.
- Existing actual Reader kinds S_BLOB, S_CHUNKS, S_VZIP, S_SPARSE, S_PACK and S_CDC require richer physical ownership, dependency and proof than this research grammar models. The word "universal" is prospective abstraction, not measured coverage.
- The fixed program catalog overhead was analytically expected to remain small for a tiny instruction set; this should have been recognized before an expensive compiler. Only a later realistic mixed-representation and independent port can decide whether there is any worthwhile product leverage.

## Counterfactual and decision
A cheaper prospective cost bound for a shared tag (at most number of selected opcode bytes, paid once per deduplicated program) plus an enum-dispatch microcheck could have predicted the byte and CPU feasibility result without generating 205 synthetic members. However it would not have proven exact inverse semantics, hostile handling or independent decode. This is a transferable *research question-selection observation*, not yet sufficient durable repeated evidence to change Discovery Engine policy.

**Decision:** preserve source-exact O0 as a positive **synthetic mechanism feasibility result** and explicitly narrow A15's next scientific question: can one instruction grammar capture at least two genuinely dissimilar currently shipped representation kinds with a demonstrable reduction in independent decoder/proof code, while preserving real file/range semantics, immutable ownership, full stored bytes, throughput, RSS and portability? Unless that stronger oracle exhibits tangible simplification/headroom over a simple safe enum switch, A15 does not merit productization. Do not reopen A05/O120 composition merely because encoded bytes were smaller than direct.

## Coordination, immutability and release law
- Scope: only research/a15_o0_*, its dedicated workflow and A15 prereg/result docs. No edits to src/, native/, frozen gates, benchmark history, format, version, released main or other owners' branches.
- No collision with #469 A05, #475 A07, #653 VZIP, #662/#676 ABI3 S_CHUNKS, and #574 Discovery STATE. Docs/discovery/STATE.json is a staleable cache and remains owned by #574.
- No product merge or release. Future CI after this documentation commit must be reported under its own exact HEAD; the scientific SUCCESS refers to 7814a61f source and original artifact.
- Existing issue/checker failures, if any, are not reason to change evaluators. No discovery policy change earned from a single bounded experiment.


## Additional independent physical-payload custody discriminator
After fetching the unmodified original hosted artifact ZIP, a detached standard-library script parsed both complete archived research formats directly (fixed header, program catalogs, member descriptors, Zstd frame spans) without importing either decoder. It independently compared **all 205/205 member compressed frame bytes**, member descriptors (including SHA-256), and the complete catalog operations. Result: **every member's actual compressed payload and full member descriptor is byte-identical between bespoke and typed IR**. Every difference in the complete artifact size equals **exactly one type-tag byte per opcode in the unique shared program catalog**, with a maximum of three bytes per 32-member cohort; no other bytes change. The original artifact ZIP passed its own CRC check. Detached audit receipt SHA-256: 1faeab0c78211202a64d0d50cd5d7664dbd04d27d4519b03352e1d032173434e.

This **sharpens the causal conclusion**: A15-O0 establishes the serialization/dispatch tax of a tiny typed grammar, not a better compression representation. The decoder unification thesis remains **unproven** against current CMPCT storage kinds, and a simple bespoke switch can still win product economics. This follow-up is independent post-result audit evidence, not a preregistered additional promotion gate.
