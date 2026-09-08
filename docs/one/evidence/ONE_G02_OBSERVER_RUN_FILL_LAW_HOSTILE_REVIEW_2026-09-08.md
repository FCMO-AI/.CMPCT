# ONE-G0.2 observer-run → generic fill-Law compiler hostile review — 2026-09-08

## Review scope

Pre-result hostile review of the implementation/falsifier frozen by `docs/one/prereg/ONE_G02_OBSERVER_RUN_FILL_LAW_PREREG_2026-09-08.md`.

No hosted performance result from this experiment is admissible unless it comes from a source at or after the fixes recorded here without moving the preregistered 32-byte qualification floor or economic gates.

## Material defects found before result consumption

### 1. Candidate would have been charged an extra full previous-root SHA

The first `program_from_observed_runs()` helper always hashed `source` internally. The benchmark writer already computes both previous/current SHA-256 identities before constructing either arm. Leaving the helper unchanged would therefore have charged the candidate a second full-source SHA while control paid one.

**Repair:** allow the already-computed previous/current digests to be passed into the compiler. No cryptographic work is removed from the writer; the duplicate candidate-only hash is removed.

### 2. Root equality originally compared graph-local Ref identities

The first semantic probe compared `control_program.roots == candidate_program.roots`. That is invalid for this experiment: the candidate must reconstruct the same named root bytes and SHA identities through a different Law graph, so its current root naturally points to a different node ID.

**Repair:** compare root names, declared lengths and exact SHA-256 identities, then independently decode/evaluate both Programs and require byte-identical previous/current outputs. Graph-local node references are intentionally allowed to differ.

### 3. Timing code claimed alternation but measured complete control and candidate loops separately

The initial harness comment promised paired alternating timing while `_time()` actually ran one full arm and then the other. Runner drift could therefore be mistaken for mechanism cost.

**Repair:** one paired loop now alternates `control→candidate` and `candidate→control` by repetition, preserving separate wall/CPU sample arrays.

### 4. Pre-timing semantic Programs/wires could perturb allocation state

The semantic authority probes retained both complete Programs and canonical wires while timing began. That could perturb allocator/cache state, especially on the 1 MiB rows where this experiment intentionally changes emitted byte volume.

**Repair:** extract only scalar authority, release heavy Program/wire/Observation objects, force collection, then enter the paired timing loop in the row-isolated child.

## Surviving claim limits

1. The candidate still pays the same native observation scan and eager `.materialize()` boundary as control. A green result therefore proves representation/compiler value despite that shared boundary; it does **not** prove direct packed/native opportunity consumption.
2. The candidate uses only existing `surprise`, `fill`, and `concat` relations. No reader-visible run opcode exists.
3. The 32-byte eligibility floor remains frozen. It may not be moved from result data.
4. A boundedness failure is INVALIDATE in this first experiment. Do not silently raise node/ref limits to rescue density.
5. The test covers intra-object maximal constant runs on the frozen synthetic observer families. It does not prove arbitrary Law discovery or full corpus generality.
6. Both roots remain in the pair wire. Report pair-container ratios honestly; do not quote the current-root-only reduction as though it were total archive reduction.
7. Authentication placement, recovery, filesystem fidelity, portability and the September 11 comparator gate remain outside scope.
8. A pass earns no v0.29/v0.30 authority by itself.

## Hostile expectation

The mechanism should win density strongly on `long_runs` and materially on the terminal constant region in `structured`; controls should remain literal/no-op because their qualifying run set is empty or economically ineligible. The more interesting disproof risk is creation economics: hundreds of fill nodes on `long_runs` could save substantial output bytes yet add Python Program-graph cost. The preregistered 1.10 run-rich time veto is intentionally left intact.

If the candidate fails that compute gate, preserve the density result but do not promote the Python construction shape. The causal next question would be native/bulk fill-Law emission from the same observer evidence, not threshold tuning.
