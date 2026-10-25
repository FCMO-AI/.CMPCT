# O105 — A03 secondary residual factorization: decisive negative

Date: 2026-10-25. **Science/O0 only — no CMPCT archive product, release, format, version or promotion change.** This result is an interpretation of the immutable original GitHub Actions receipt, not replacement benchmark data.

## Source and prediction custody
- Canonical reference `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; v0.30.0/r24 remains shipping.
- Original prospective prediction was committed at `3527d8d0129fa50a4897155e2593413f60454274` before creating the oracle source, workflow or running any experiments.
- The committed source is `research/v031_o105_a03_residual_factor_oracle.py`, Git blob `afa477c7a9a99c24f9c747352eb4208857ce17a0`. Actual hosted source SHA-256: `962fd8768283559196a19246f6564c0303e7567bf16fcecc762d4e28485e1c98`.
- Hosted exact-head source `e27e030a0c28302fd2455be7d75aeffd3c5e0869`, [Actions run 40222399530](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222399530), Ubuntu 24.04, Python 3.11, libzstd level 9. Job `121256593464`: **SUCCESS**, all source/prereg ancestry and topology checks succeeded, all real encode/decode and independent JSON audit steps succeeded.
- Original uploaded [artifact 12610290749](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222399530/artifacts/12610290749) SHA256 **`7a331097afe413f2b72f9b80447a83a53d90f43a06671361113e479d3632429b`**. It contains raw JSON, repeated individual measurements, actual source identity and independent audit. Preserve that source; do not replace it with rounded values here.
- Separate local lower-rung CPython 3.13.5 source experiment used a nearly identical script (different output-file path and folder creation) and raw JSON SHA256 `49576b864669faa324a086b6f4a97a5053616645a3dff08f32ed1c5277f323c9`. The source version is not identical; the hosted exact-head result supersedes it for this source claim.

## Experimental question and six competing representations
A: individual complete-target Zstd; B: solid complete-target Zstd; C: one shared base + individually encoded XOR residuals; D: one shared base + concatenated groups of eight residuals; E: one shared base + **position-major transposed** groups of eight residuals; F: one shared base + one actual residual root per eight + individually compressed XOR-of-residual deltas. Inputs were four independently seeded 32-file trees of 4096-byte records: correlated sparse-random edits, held-out structured/field-edit records, independent sparse edits, unrelated random targets. Five **rotated-order repetitions** per arm, all target SHA-256 exact reconstruction required. Charged bytes = compressed payload of every owner + 64-byte root + 24-byte member references × 32 + 32 bytes per physical owner. This is a **research accounting model**, not actual CMPCT on-disk serialized bytes. Four selected member positions and physical/decoded work accounted.

## Hosted decision table (whole charged bytes)

| Case | Stronger simple B solid | C independent residual | D group residual | E positional residual | F residual-of-residual | E over B |
|---|---:|---:|---:|---:|---:|---:|
| Correlated sparse random | **5,772** | 13,117 | 6,773 | 6,922 | 8,726 | **+19.92%** |
| Held-out structured edits | **1,982** | 5,850 | 2,312 | 2,431 | 4,063 | **+22.65%** |
| Independent sparse edits | **9,860** | 11,453 | 9,893 | 11,468 | 15,373 | **+16.31%** |
| Unrelated random | **131,948** | 137,386 | 136,210 | 136,210 | 137,386 | **+3.23%** |

Positive H1 requires **E or F** to beat the strongest of A/B/C/D by >=10% on the correlated sparse-random family, and <=8x independent residual C selected work. **H1 FALSIFIED on stored bytes**, prior to any higher-rung product prototype. Held-out H2 is also **FALSIFIED** (the best factor lost to B). All 120 actual hosted arm/repetition observations, fingerprint and reconstruction checks passed. E's selected decoded logical bytes are 36,864 B for a 4,096-byte member, identical to D's owner work; D beats E's charged bytes in three regimes and ties in flat negative. Thus positional transposition has no observed advantage over grouped residuals under tested conditions. B solid requires 131,072 B decoded on one selected 4KiB member, so this byte win is **not** a product-locality win; B is a necessary full-storage control.

F is a conditional **research-only** byte/locality tradeoff against **C**, not stronger B/D: in the shared family F stores 8,726 vs C 13,117 B, but selected logical decoder work is 12,288 vs C 8,192 B (1.5x) and dependency depth 2 instead of 1. F loses substantially to B and D in full stored bytes and needs real integration, cold whole-owner SHA, indexing, RSS, I/O and generic admission to earn any product claim. Other families show direct F regressions. No universal gain.

## Host measured costs (not official performance)
The result-bearing job logs show median create wall in shared case: B 0.274 ms, C 4.253 ms, D 3.726 ms, E 8.286 ms, F 6.885 ms. Thus any tempting locality choice also exports creator work. These are tiny warm-process experimental timings, not official r24/ZIP same-runner ABBA and not cold/full-stack measurements; cross-runner performance claims are forbidden. An independent reader cannot infer true RSS, durable open cost, full tempfile I/O or native portability from these numbers. All local and hosted scientific negatives remain evidence.

## Decision and counterfactual
**NARROW / RETIRE** this fixed size-eight positional transposition family as a general stored-byte improvement under tested fixed-size correlated residual regimes. Do not tune group size, shift seeds or change comparator after seeing losses. A simple whole-target solid control and plain residual concatenation would have rejected it at the cheap O0 rung before any archive-format implementation; this is a useful prospective discriminator for future A03 work. A conditional F research Pareto point remains only when bounded random access is a product objective and generic admission can be proved; do not promote as a free byte win.

## Coordination, status and next work
The GitHub audit found `agent/phased1-a03-residual-factor-o0` as a branch pointing to the **unchanged canonical HEAD `4545d7d5...`** (no implementation claims or own commits as of this result). PR #458 is an independently scoped documented O0 experiment and does not modify other A03 product branches. PR #452 targets dictionary-framed original PACK bytes; PR #453 VZIP memory; PRs #455/#456 namespace custody; PR #440 discovery state reconciliation. No owner changes, no collision/duplicate product implementation, no `docs/discovery/STATE.json` mutation. We do not rewrite its stale state while another owner reconciles it.

**Next highest-leverage mission action:** stop E threshold gardening, preserve negative and return to product convergence/evidence that could be promoted (O93/O99 safety integration and #318 performance gate admission). Do not merge PR #458 or release; the oracle is evidence, not code to ship.
