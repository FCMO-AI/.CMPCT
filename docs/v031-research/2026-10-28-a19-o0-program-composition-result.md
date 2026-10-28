# A19-O0 — charged two-stage reversible-program result

Date: 2026-10-28 UTC. **Scope: research component/representation only. No CMPCT product, r24/r25 format, release, benchmark, comparator, evaluator, or discovery-policy change.**

## Frozen question and controls
Preregistration: `f48a8b9f2c1788ab83776df22916f75210159857` (committed **before** code). The 20-arm bounded grammar contains direct Zstd-19, all seven unary deinterleave/XOR-lag variants, and 12 `deinterleave→xor_prev` compositions. Every candidate pays for an actual Zstd-19 compressed payload plus an identical framed MessagePack description of logical size, SHA-256 and exact program. The binary `A19O` envelope is a **research fixture**, not a CMPCT format proposal.

Primary positive gate: a structured family with **both independent deterministic seeds** saving >=1% **and** >=128 complete bytes compared with best unary, and beating direct. Held-out, random and periodic controls cannot retroactively replace the primary question or alter its gate.

## Original source-exact hosted evidence
- Code/CI **HEAD**: `0d153b0a8ffe183e1346fe03b16a3ad285dd8a2a`, [run #40748875049](https://github.com/FCMO-AI/.CMPCT/actions/runs/40748875049), **SUCCESS**.
- Exact zipped artifact **ID 12843216143**, SHA-256 `109c8f2b6ef9e904a99c595df06fa02a89c10d88d427e7584440e4708c2fd28b`, with all **200** physical frames (10 fixtures × 20 arms) and full raw timing observations.
- Ubuntu 24.04, Python **3.11.17**, libzstd **1.5.5**, MessagePack **1.1.2**.
- Independent repository referee: physically checks every program frame, every source SHA and 150 raw timing observations; 7/7 falsified receipt attempts rejected; CI PASS indicates valid science, **not** a shippable product.
- **Second detached artifact audit** independently downloaded and confirmed artifact SHA, regenerated all ten byte-identical original SHAKE source identities, independently decoded all 200 physical frames and recomputed the strongest controls and frozen decision with no CMPCT/repository-referee imports. No mismatch.

| Fixture | Direct bytes | Best unary | Best 2-stage | Delta unary − composed | Primary result |
|---|---:|---:|---:|---:|---|
| progression seed0 | 18,758 | 16,385 | 16,216 | +169 / **1.031%** | PASS |
| progression seed1 | 18,588 | 16,457 | 16,260 | +197 / **1.197%** | PASS |
| quantized seed0 | 63,487 | **28,786** | 29,061 | −275 | FAIL |
| quantized seed1 | 63,468 | 29,495 | 28,699 | +796 | PASS |
| heldout seed0 | 64,612 | 53,319 | 48,619 | +4,700 | Exploratory only |
| heldout seed1 | 64,618 | 53,338 | 48,161 | +5,177 | Exploratory only |
| random seed0/1 | **65,630 / 65,633** | 65,641 / 65,644 | 65,656 / 65,659 | −15 / −15 | Direct wins |
| periodic seed0/1 | **133 / 133** | 147 / 147 | 170 / 170 | −23 / −23 | Direct wins |

Frozen hosted **decision = `A19_COMPOSITION_O0_HEADROOM`**, restricted to this libzstd 1.5.5 grammar/input/environment component. It is **not** a general archive-compression result.

## Independent contradictory codec-version observation
A fully separate Linux/Python3.13.5/local-libzstd **1.5.7** implementation measured the same ten input logical SHA-256 hashes and fully charged MessagePack envelopes. On progression seed1, unary = 16,395 B and composed = 16,261 B; **+134 B / 0.817%**, failing the frozen 1% condition. Quantized seed0 again fails (+275 B worse). Direct progression compressed output also changed markedly between 1.5.5 and 1.5.7; that difference is not an input-identity mistake.

The contradictory result must not be averaged away, called infrastructure failure, or hidden. The *same* encoded input and program portfolio can cross a narrow byte threshold as a compressor's actual implementation changes. The original prospective question did not freeze libzstd version; the strictly truthful claim is therefore **positive in observed hosted 1.5.5, not robustly positive across available versions**. A new predeclared environment/codec control is necessary before generalizing or proposing product admission.

## CPU / decoder work and strongest controls
Hosted **progression seed0** median five repeated in-process observations:

| Selected arm | Complete stored bytes | Create wall | Read/decode wall |
|---|---:|---:|---:|
| Direct Zstd-19 | 18,758 | **10.773 ms** | **0.151 ms** |
| Best unary | 16,385 | 35.357 ms | 5.324 ms |
| Best 2-stage | 16,216 | 36.459 ms | 5.445 ms |

Exhaustive 20-arm oracle search itself costs **596.42 ms wall / 596.38 ms CPU** for this 65KiB input. Progression seed1: **602.87 ms wall / 602.79 ms CPU** search. Python reversible XOR requires a full scan, allocations and separate temporary output; decoder work/cold memory and generic selector/search economics are not solved. These data falsify **immediate product viability** despite the positive 169/197 B hosted research result.

The two favorable heldout results were independently challenged with a **different simpler full-byte control**: fixed midpoint segmented representation, first segment best unary, second direct Zstd-19, both real compressed payloads and lengths plus MessagePack/sha charged. The local 1.5.7 bounded-segmentation oracle gives **47,348 B versus whole-file best-composed 48,619 B** (seed0), **47,372 B versus 48,159 B** (seed1). This gifts the ideal split position, so it has **oracle-only** scope, but demonstrates that mixed-regime composition win can simply be a consequence of missing region ownership/admission rather than evidence of a fundamentally stronger program algebra.

## Negative/adversarial scope and decision
- Frames with malformed magic, short/truncated metadata and mutated compressed payload are rejected by the hosted component; independent inverse and SHA check all legitimate frames.
- No arbitrary archive structural/corruption, sources mutated concurrently, stream/seek, recovery, CDC, ZIP parity, portability, transaction or real disk I/O claims.
- No installed CMPCT Reader/Builder, candidate complete archive size, byte parity on released corpus, cold-start/RSS, full-system create/extract timing, or official release benchmark measured.
- Strong alternatives include direct Zstd-19, best unary on exact bytes, version-changed compressor and explicitly charged segmented unary/direct control. None can be omitted from a future promotion argument.

**Decision:** retain **narrow research-only A19 descriptive headroom**, reject **immediate shipping/portable-generic proposition**, and **retire local threshold/lag/channel gardening**. If this information-model family is reopened, require a newly falsifiable discovery/representation boundary with inexpensive prospective admission and real controls; otherwise return to higher-leverage unmerged correctness and resource safety owners. No normative policy/Discovery STATE change justified by this single contradictory codec result.

## Concurrent work / transfer
A19 scope is isolated to PR #696. J24C native Reader and mutable-reference debt live on #662/#676/#692; Phased1 owns A16 co-owner representations; Phased2 owns signed metadata and quota controls #690/#693/#694. No overlapping shared product writes, no format modification, no merge or release.

**Counterfactual discriminator:** a best-unary-vs-composed control on two independent sources *and two explicitly pinned Zstd library versions* plus a charged split portfolio would have avoided concluding from one codec-specific byte win that a general A19 product route exists. This is a transferable prospective methodology observation, **not evidence sufficient to revise the discovery policy.**
