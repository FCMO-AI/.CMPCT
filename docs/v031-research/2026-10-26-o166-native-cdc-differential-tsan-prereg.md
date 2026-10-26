# O166 — hosted differential native CDC race court (preregistration)

Date: 2026-10-26
Status: PREDICTION FROZEN BEFORE EXPERIMENT CODE
Repo: FCMO-AI/.CMPCT
Parent: O163 PR #501 @ `d3ec6481fa43e4e49ba3ad42e2395082d03c0ccd`
Comparison base: `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`
Native owner control: PR #228; installed candidate native C blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364`

## Decision question

Can independent hosted concurrent cold-start execution distinguish the inherited unsynchronized mutable CDC gear-table initialization from the source-exact immutable O163 implementation, while proving deterministic algorithmic outputs under identical fixture seeds?

This does not duplicate an implementation. The owner #228 reported a local ThreadSanitizer control; O163 separately has 791 green general tests and 0-byte ABBA size regression. This experiment tests their intersection at the native concurrency boundary, using Git-source-exact original and integrated C files without modifying them.

## Predicted discriminators

1. In an Ubuntu hosted compiler/runtime with functioning ThreadSanitizer, initial simultaneous calls to the original base trigger a reported race inside lazy gear initialization, while the immutable candidate produces no TSan race. A green wrapper court is scientifically valid only if the raw baseline race, candidate clean execution, and matching outputs are all witnessed.
2. Identical deterministic inputs and parameters produce identical per-thread and aggregate cut results across base and candidate in ordinary unsanitized execution, with no missing/duplicate cut offsets or divergent counts.
3. The workflow verifies exact Git HEAD, original commit, pristine original and candidate native source blobs and source/protocol identities. It must record actual compiler/runtime details, stderr and exit codes, not infer source safety from arithmetic equivalence alone.

## Strongest simpler control and alternative explanation

The original owner already derived source-level equivalence (256 SplitMix64 constants), and the O163 r24/ZIP parity had zero stored-byte delta on 16 cells. Those controls are **not** a hosted concurrent first-use sanitizer experiment. If TSan reports a runtime mapping failure, loader fault, unsupported instrumentation or missing compiler, the result is INFRASTRUCTURE-INCONCLUSIVE, not a candidate pass or baseline product failure. An ordinary threaded run can check algorithmic parity but cannot prove race freedom.

## Kill / narrow / decision

- Candidate TSan data race or result difference: **reject** the native convergence hypothesis pending causal diagnosis.
- Baseline race and candidate clean with matching deterministic outputs: **confirm narrow hosted native race repair** for the tested compiler/platform/fixture.
- Both clean or sanitizer unavailable: **no race-elimination credit**; retain only parity evidence, report limitation.
- Never change existing tests, compiler semantics, benchmark thresholds, TSan diagnostics or source C to rescue a predicted green.
- No numerical product release, cross-platform ABI, r24 archive-size, CPU/RSS or general multi-file-system conclusions follow from this test.
- Scientific evidence is subordinate to main/branch truth, release gates and the owners' source identity.

## Concurrency / ownership / resource

This is a new, narrow, independent **replication** on existing O163 branch. Do not edit #228, #266, #476 or discovery STATE. No source benchmark changes. Small synthetic payloads only; sanitizer compute and extra CI footprint explicitly count as evidence-enablement cost. Candidate workflow must not silently trigger historical negative races as global CI regressions: classify original baseline race as expected scientific negative only when independently observed.
