# ONE-G0.2 trusted prior-root reuse result — 2026-09-08

## Exact evidence authority

- source: `research/cmpct1 @ 790b8cf096514094e8e14976e72c3a3077ac0da2`
- Actions run: `34230528763`
- job: `102075215206`
- artifact: `one-g02-trusted-prior-root-reuse-790b8cf096514094e8e14976e72c3a3077ac0da2`
- artifact ID: `10057761062`
- artifact ZIP SHA-256: `f112f6d2c0ac7fcc99cceaa9e2ff077bbb99e98a889749ea5bd90d00c1d39d2b`
- tests: 12 passed
- decision: **`ADVANCE_TRUSTED_PRIOR_ROOT_REUSE`**

The exact-head checkout/binding, frozen decision-law tests, falsifier, semantic gates, and artifact retention all passed.

## 1 MiB result-bearing rows

| case | admitted | control wall ms | trusted wall ms | wall ratio | control CPU ms | trusted CPU ms | CPU ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| shift_plus1 | yes | 3.027 | 2.259 | 0.747 | 3.024 | 2.257 | 0.746 |
| shift_plus1_damage_quarter | yes | 13.723 | 12.899 | 0.940 | 13.702 | 12.896 | 0.941 |
| fragmented_every96 | yes | 67.186 | 66.432 | 0.989 | 67.179 | 66.402 | 0.988 |
| fragmented_every32 | no | 1.812 | 1.057 | 0.584 | 1.810 | 1.056 | 0.583 |
| independent_random | no | 1.768 | 1.013 | 0.573 | 1.766 | 1.011 | 0.573 |

All rows preserved exact Program/canonical semantics. Rejected rows retained zero Segment capacity under the already-promoted lazy scheduling policy.

## Interpretation

The previous generation's authenticated SHA-256 identity should be carried as trusted adjacent-version writer state rather than recomputed from the old generation on every update. The benefit is largest when the rest of writer work is cheap and naturally diluted when deeper segmentation/Program construction dominates.

This does **not** weaken authentication. The trusted digest is independently established before the timed adjacent-write path. Cold import, repair, external/untrusted bases, and any state whose provenance cannot be established must authenticate normally.

The result also narrows future fusion work: do not build a fused kernel merely to accelerate an old-root hash that should not occur on the hot persistent-update path. Only unavoidable current-generation authentication belongs in future whole-writer fusion analysis.

## Claim boundary

This result covers the persistent adjacent-version research writer. Establishment/persistence of prior authenticated state, filesystem traversal, authenticated placement, process startup, full product ingest, and decode timing remain outside scope. It changes creation cost, not stored ONE bytes or reader semantics, and earns no Genesis comparator point by itself.
