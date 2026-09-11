# CMPCT1 ONE Genesis candidate freeze handoff — 2026-09-10

Status: **PRE_GATE_FREEZE_CANDIDATE_NOT_CERTIFIED**
Experimental version: `ONE-G0.2`
Primary branch: `research/cmpct1`
Frozen candidate source proposed for first post-boundary certification: `38f17f4a45686a59a853bf62f0c840e228879e17`
Current branch may move for tests/docs/CI hardening; do **not** silently substitute branch HEAD for the frozen candidate.

## Mission lock

This handoff freezes the best exact-source candidate surface that has both semantic/selective adapter evidence and fresh-process resource evidence before the 2026-09-11 America/Mexico_City Genesis activation boundary.

It does **not** certify the candidate, execute Genesis inputs, compare contenders, score rows, or select a winner. The production candidate boundary remains fail-closed until the date boundary has opened and certification checks bind the exact tested Git objects.

Frozen comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Why `38f17f4...` is the freeze candidate

A transfer-only fresh-process run immediately before this source exposed a real production-seam defect: the workload measurement executor invokes `benchmarks/one/one_genesis_cmpct1_product_worker.py` by absolute script path, while the worker originally depended on module-style `sys.path`. The subprocess therefore failed to import `experiments.one` despite the module-invocation unit tests being green.

`38f17f4a45686a59a853bf62f0c840e228879e17` repairs that seam by binding imports to the worker's own sealed checkout root. It does not alter the ONE creator representation, reader semantics, corpus, scoring law, or comparator settings.

A later commit, `84f2e27e8440913d8e7352e52d155715da7350d9`, adds an explicit regression test for the exact absolute-script invocation. That test-only commit hardens future branch behavior but does not replace the exact-source candidate that already received the two hosted transfer authorities below.

## Exact-source hosted adapter evidence

Workflow: `CMPCT1 ONE-G0.2 Genesis candidate adapter probe`
Run: `34536981098`
Source: `38f17f4a45686a59a853bf62f0c840e228879e17`
Conclusion: **SUCCESS**

The lane verifies the transfer-only adapter boundary, deterministic wire, exact whole reconstruction, authenticated selective reconstruction, generic reader ontology, complete stored-byte accounting, and the embargo flags that prevent Genesis workload import/execution/scoring/winner selection.

## Exact-source hosted resource evidence

Workflow: `CMPCT1 ONE G0.2 candidate resource transfer`
Run: `34536981202`
Job: `103070778446`
Source: `38f17f4a45686a59a853bf62f0c840e228879e17`
Conclusion: **SUCCESS**
Artifact: `10175780293`
Artifact ZIP digest: `sha256:f046e4ef5e0a34cd19b4de1037faaad721aec4ded2166bbd8457b7774ccc8a29`
Candidate wire SHA-256: `146dc494c868d5eafba60b6d88b39cd84c07188e669867c349bcb043a2b4112b`
Decision: `ADVANCE_RESOURCE_OBSERVABILITY_ONLY`

The transfer fixture contains 314,988 logical regular-file bytes and produced a 258,980-byte authenticated ONE archive. It is intentionally not Genesis data and earns no competitive score.

Five fresh-process samples established deterministic wire and exact full-tree + authenticated selective semantics:

| phase | median CPU | median wall | median peak RSS |
| --- | ---: | ---: | ---: |
| creation | 0.030312561 s | 0.030311017 s | 23,687,168 B |
| whole read | 0.028005863 s | 0.028004804 s | 23,932,928 B |
| selective access | 0.029871894 s | 0.138923932 s | 23,724,032 B |

The selective wall samples were noisy (`0.087447730–0.224070687 s`) while CPU stayed near 0.03 s; do not turn the tiny transfer fixture's hosted wall time into a product throughput claim.

Creation accounting on the transfer tree:

- logical file bytes: 314,988 B
- source-read bytes: 314,988 B
- discovery exact-proof bytes: 65,536 B
- discovery sample bytes: 112 B
- Surprise bytes: 258,546 B
- complete wire bytes: 258,980 B
- raw auth-index bytes: 4,924 B
- authenticated manifest bytes: 9,094 B
- control/integrity bytes: 434 B
- authentication source reread: 0 B
- regular files: 7; directories: 1; symlinks: 1

For the selected `structured/events.jsonl` member:

- requested: 28,221 B
- source read: 28,221 B
- cone: 28,221 B
- proof payload: 28,221 B
- auth index: 420 B
- fallback: false
- one plan command

## Current negative evidence that remains active

The second-stage relation falsifier is **not** promoted. Exact-source hosted evidence at `ca61df66c9c59a9258cdac5e8bb0676cc351a0e7` produced `HOLD_SECOND_STAGE_RELATION_KERNEL`: broad median CPU improved to ~0.592x, but hostile dual-collision survivors regressed to ~1.556x CPU / ~1.411x wall. A separate late-tail survivor supplement was near-neutral (~1.00045x CPU), localizing the red to fixed/control overhead when the baseline exact proof would fail early.

Existing native exact relation proof is already roughly 19.6–19.7x faster than the Python proof path. Therefore the pre-gate freeze does not absorb or promote the current Python second-stage filter. Any reopening must prove marginal value against the native proof/fused-observation frontier, not merely against the superseded Python proof cost.

## Certification transition after the date boundary

At or after the first permitted activation on **2026-09-11 America/Mexico_City**, do the following in order and fail closed on any mismatch:

1. Resolve the frozen candidate commit `38f17f4a45686a59a853bf62f0c840e228879e17` and compute exact Git identities for:
   - `experiments/one/general_law_archive.py`
   - `experiments/one/authenticated_archive_envelope.py`
   - `experiments/one`
2. Verify the exact-source adapter run `34536981098` and resource run `34536981202` remain successful and correspond to that source.
3. Verify no post-freeze evidence invalidates the creator/reader/runtime-tree semantics or resource boundary.
4. Update `benchmarks/one/genesis_one_candidate_boundary_v1.json` **only as a certification authority transition**, setting status to `CERTIFIED_FOR_GENESIS`, `production_eligible=true`, and binding `certified_candidate` to the exact creator/reader/runtime-tree Git objects of `38f17f4...`. Do not change creator/reader/runtime code in the certification commit.
5. Run the candidate-boundary validator and production-worker authorization tests on that exact certification state. If any identity, semantic, access, integrity, portability, or resource invariant fails, revert/hold certification rather than weakening the validator.
6. Freeze the resulting certification commit/source relationship and launch the real 15-workload Genesis executor using the frozen ONE candidate and the immutable v0.29/v0.30 comparator authorities.
7. Preserve raw measurements before scoring. Never substitute a post-hoc per-workload mechanism oracle for either ONE or v0.30.

## Hostile reviewer vetoes

Do not certify merely because branch CI is green. Certification is allowed only when the tested candidate identities match the production worker's sealed checkout expectations.

Do not chase a newer branch HEAD unless it has a materially stronger candidate and receives the same exact-source adapter/resource evidence before certification. Test/docs/CI-only hardening after the freeze does not automatically create a new compression candidate.

Do not run the 15 Genesis workloads before the Mexico City date boundary. Do not edit the workload matrix, comparator settings, semantic requirements, locality, integrity, recovery, safety, portability, or scoring to manufacture a pass.

## Next decisive action

The next decisive campaign action is no longer another pre-gate microbenchmark. It is the controlled post-boundary transition from this frozen, exact-source-tested candidate to a certified production measurement boundary, followed immediately by the full same-input 15-workload Genesis comparison.

If certification cannot be completed without altering the candidate surface, the correct result is **HOLD / gate infrastructure blocker**, not an improvised benchmark.