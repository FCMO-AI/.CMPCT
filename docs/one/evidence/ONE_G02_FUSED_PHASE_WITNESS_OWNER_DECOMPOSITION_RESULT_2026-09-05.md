# ONE-G0.2 — fused phase-witness native cost-owner decomposition result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **stable first owner = bottom-K maintenance**

## Exact evidence

- source: `fd51c1ce7695a0210cbb09f6f0f83b22e9a8e3b8`
- workflow: `33974005342`
- job: `101327399246`
- artifact: `9971763783`
- artifact digest: `sha256:2e8033b1b4caf18d0356aca6f8d9f03c36af824d70ae588a51a8902272fe1c87`
- pre-result ONE semantic/hostile tests: pass
- native witness/reference mismatches: 0

## Frozen decomposition

The rejected fused certificate was split without changing its semantics:

1. baseline observer;
2. baseline + rolling 8-byte raw word;
3. raw word + frozen phase schedule/hash;
4. full frozen bottom-4 maintenance.

Incremental elapsed was charged in ns per logical input byte.

## Result

The preregistered stable-owner law required one component to be the largest positive increment on at least four of the five large gate controls.

Owner counts:

- bottom-K maintenance: **4/5**;
- phase hash: **1/5**;
- raw-window maintenance: **0/5**.

Large-row increments:

| case | raw word | phase hash | bottom-K | largest |
|---|---:|---:|---:|---|
| random 1 MiB | 0.6169 ns/B | 0.5738 ns/B | **0.6338 ns/B** | bottom-K |
| compressed-like ~1 MiB | 0.6190 | 0.5703 | **0.6366** | bottom-K |
| repeated 1 MiB | 0.6197 | 0.5648 | **0.6385** | bottom-K |
| shifted/versioned 1 MiB | 0.6171 | 0.5804 | **0.6295** | bottom-K |
| zeros 1 MiB | 0.3104 | **0.7066** | 0.6274 | phase hash |

The alternating hostile row was close but raw-window-led (0.6244 vs bottom-K 0.6102 vs hash 0.5713). Tiny controls were bottom-K-led.

## Causal interpretation

The rejected path is not dominated by one absurdly expensive instruction. It is a three-part hot-loop bill, with bottom-K only narrowly but consistently first on ordinary large controls. This matters: repairing bottom-K alone cannot plausibly restore the original <=1.12x carrying-cost gate unless the repair also exposes fusion or elimination opportunities in the neighboring raw-word/hash work.

Still, the stable-owner rule is satisfied and gives a disciplined next Builder. The current heap-style online admission does common-path threshold work on every sampled phase even though actual witness admissions/replacements are sparse on mature large inputs. The next experiment should preserve exact bottom-4 tuples while changing the selection representation, not the certificate coverage.

## Hostile Reviewer

Do not overread the 4/5 count. Bottom-K is a **first owner**, not proof of sole dominance. Random/compressed/repeated/shifted increments differ by only about 0.01–0.07 ns/B between the three components. A local selection optimization that merely shifts code layout or branch pressure into hashing is not a meaningful win.

Any next Builder therefore needs an end-to-end full-fused A/B, exact witness equality, and a material total-loop improvement—not merely a faster isolated selector microbenchmark.

## Next decisive action

Test a branch-light exact sorted-4 representation for each phase: because positions arrive monotonically, equal-hash later positions are never better than already-held equal-hash witnesses. Maintain each phase's four witnesses sorted by `(hash, position)`, reject the common case with one comparison against the current worst, and perform bounded shifts only on a true admission. Preserve the five phases, hash, K=4, witness tuples, raw-word path, and all parent controls.

If that cannot materially reduce total fused elapsed, retire selection-local rehabilitation and move to cross-stage fusion/opportunity gating rather than trying another heap spelling.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows from this result.