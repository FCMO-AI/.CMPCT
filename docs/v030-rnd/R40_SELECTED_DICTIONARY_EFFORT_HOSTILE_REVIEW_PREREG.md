# R40 — Selected-Dictionary Effort Hostile Review Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: `docs/v030-rnd/R39_SELECTED_DICTIONARY_EFFORT_REHABILITATION_RESULT.md`.

## Question

R39 established a narrow Builder win: for the exact content-derived 180-candidate small-text family isolated by R38, dictionary level 9 retained 78.15%–80.27% of the protected level-12 byte saving while eliminating the material runtime regression on both frozen backup views.

R40 asks the adversarial product question that R39 deliberately did not answer:

> Does that intervention remain worth carrying when the same content-derived rule is exposed to the complete accepted 15-workload repair-v6 public matrix, including non-applicable data, false-positive admissions, byte erosion, runtime/RSS/locality effects, and permanent implementation/native/platform burden?

R40 is **Hostile Reviewer evidence**, not product or release authority. A positive result may authorize only the next Forge prerequisite/productization review. It may not directly edit canonical product policy, merge, tag, version-bump, publish, or unlock v0.30.

## Frozen worldview under attack

The Builder worldview is that the R38 family is a real semantic class rather than a backup-specific accident, and that lowering only its selected dictionary effort is a low-carrying-cost way to preserve most of the byte gain while paying down runtime debt.

The hostile alternative is that the apparent win is structurally narrow: the family may occur only in one nested backup regime, generic nomination may activate on unrelated data, byte erosion may spread beyond the protected pair, runtime gains may disappear outside the original target, or the rule may add permanent portfolio/native/platform complexity whose global cost exceeds its retained saving.

R40 must be able to reject the Builder worldview.

## Immutable source identity

Use the exact accepted public 15-workload matrix consumed by `benchmarks/mosaic_v029_generalization_bench.py`:

- historical v0.28 identities for rows not superseded by repair-v6;
- accepted repair-v6 identities for the five repaired neutral/hostile rows;
- repair-v6 record: `benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json`;
- accepted repaired v0.29 aggregate identity: **137,499,525 B**;
- immutable inherited v0.30 absolute saving hurdle: **687,783 B**.

The August 17 public record remains historical evidence and may not be rewritten. R40 may not alter generator identity, corpus membership, metadata normalization, the 15-row matrix, or the inherited v0.30 hurdle after any result-bearing execution.

## Frozen mechanism

The candidate family predicate is exactly the R39 predicate:

1. candidate has at least one exact Deflate stream;
2. candidate raw hash is not retained as canonical Deflate after the existing locality/retention law;
3. candidate raw hash is not retained as a secondary Deflate stream;
4. raw length is strictly `< 65,536` bytes;
5. at least one existing hint is in the canonical text-extension set;
6. the build has a dictionary;
7. admission is independent of workload name, path, corpus identity, filename stem, candidate hash allowlist, post-hoc winner identity, or benchmark row.

The only intervention is dictionary compression effort **12 -> 9** for candidates satisfying that predicate. R32 output-dead ordinary-Zstd elision for the exact-deflate-backed regenerable class remains present exactly as in R39. No other encoder, representation, retention, parser, locality, framing, recovery, or reader change is allowed inside this freeze.

## Frozen arms

For each workload, measure:

1. `release-all-exact` — the same exact-Deflate-retaining control used by R39;
2. `dict12-control` — the R39 selected representation with dictionary level 12;
3. `family-dict9` — identical to `dict12-control` except the frozen family uses dictionary level 9.

Every arm must consume the same generated source tree for that workload. Every output must be deterministic across repetitions.

## Frozen execution protocol

For all 15 public workloads:

- generate the accepted source tree once per workload under the current accepted repair-v6 substrate;
- prove the observed tree hash and inherited baseline bytes match the accepted identity before interpreting any arm;
- run **5 fresh processes per arm per workload**;
- record complete archive bytes and SHA-256;
- strong-verify every archive and require exact source-tree identity;
- record build wall time and process peak RSS;
- record total candidate count examined by the family predicate, specialized candidate count, and specialized raw bytes;
- preserve the existing exact Deflate retention accounting;
- derive operation-based selected-member locality using the current canonical measurement path wherever a selected virtual member exists;
- require the established `<=8x` selected-member decoded-context ceiling; absence of a virtual member is not a locality failure and must be recorded explicitly rather than invented as `1x`;
- preserve exact release/product grammar and all existing resource/correctness bounds.

Timing medians are computed per workload/arm across the five fresh processes. The unchanged material-runtime rule is:

`candidate - baseline > 3 ms` **and** `(candidate / baseline - 1) > 5%`.

RSS regression is material when median peak RSS exceeds the corresponding baseline by more than **10%**.

## Frozen accounting

For every workload, R40 must publish at least:

- accepted source tree hash / observed source tree hash / identity match;
- `release-all-exact`, `dict12-control`, and `family-dict9` complete bytes;
- byte delta of `dict12-control` vs release;
- byte delta of `family-dict9` vs release;
- byte erosion of `family-dict9` vs `dict12-control`;
- fraction of positive `dict12-control` saving retained by `family-dict9` when such saving exists;
- five fresh build-wall samples and medians;
- material-runtime flags vs release and vs dict12;
- five peak-RSS samples and median/material flags;
- total candidate auditions, family-predicate examinations, specialized candidate count, specialized raw bytes;
- exact Deflate retained/regenerated counts and bytes;
- strong verification / deterministic archive identity;
- locality availability, measured maximum amplification when applicable, and `<=8x` status.

Aggregate evidence must additionally report:

- number of workloads where the family activates;
- number of workloads where dict9 changes complete archive bytes relative to dict12;
- number of workloads where dict9 improves, ties, or worsens runtime relative to dict12 under the materiality law;
- number of workloads with any material runtime/RSS regression vs release;
- aggregate specialized raw bytes divided by aggregate logical input bytes as an Addressable Opportunity Mass proxy;
- aggregate retained positive byte saving and aggregate byte erosion vs dict12;
- false-positive admission count: family activations on workloads where dict9 does not retain a strict byte win vs release;
- global nomination density: specialized candidates / family-predicate examinations;
- implementation carrying-cost facts listed below.

Aggregate byte totals may illuminate carrying cost but may **never hide a losing required row**.

## Frozen implementation carrying-cost review

The result must explicitly price these facts rather than calling the mechanism “free”:

1. **Reader grammar:** the intervention changes encoder effort only; it adds no new on-disk codec, grammar, parser state, recovery state, or reader representation. If execution reveals otherwise, fail closed as substrate drift.
2. **Python encoder surface:** count net new permanent decision branches/constants required to express the content-derived policy in the canonical writer.
3. **Native boundary:** `docs/NATIVE_CORE.md` is authoritative. The shared native r24/r25 layer is primarily a reader/dispatcher boundary; R40 must state whether this encoder-only policy requires any native parser/reader/C-ABI change. Any required native behavior beyond accepting existing Zstd-dictionary metadata is carrying cost and blocks a “low-cost” conclusion until independently gated.
4. **Platform shells:** Android/platform consumers may not grow an independent parser or selector copy. Any platform-specific reimplementation required by the policy is disqualifying until concept-compressed into the shared boundary.
5. **Test/fuzz/recovery surface:** because no new grammar is intended, the mechanism must not claim new reader states. Any observed need for representation-specific parser/fuzz/recovery branches is charged as permanent complexity.
6. **Portfolio entropy:** determine whether the rule replaces/subsumes an existing effort choice or adds a second long-lived special case. A narrow additional exception with negligible AOM may be rejected even if locally positive.

## Frozen terminal decision grammar

Exactly one terminal decision must be emitted:

### `PROMOTE_DICT9_NEXT_PRODUCT_PREREQUISITE`

Allowed only if all of the following hold:

- all 15 accepted source identities match;
- all outputs are deterministic and strongly verify;
- no workload loses its strict complete-byte win vs `release-all-exact` because of dict9 where `dict12-control` had a strict win;
- the original Full Incremental Backups and isolated-family behavior remain directionally consistent with R39; for the full public Incremental Backups row, dict9 retains a strict byte win vs release and has no material runtime regression vs release;
- **zero** material runtime regressions vs release caused by `family-dict9` across the 15 workloads;
- **zero** >10% RSS regressions vs release across the 15 workloads;
- every applicable locality measurement remains `<=8x`;
- false-positive admissions do not create a byte loss vs release on any workload;
- the family has non-zero Addressable Opportunity Mass beyond a single post-hoc candidate identity, or the evidence shows the policy truly subsumes an existing canonical effort choice with negligible permanent carrying cost;
- native/platform/reader grammar carrying cost remains zero or demonstrably subsumed by existing generic Zstd-dictionary handling.

This decision authorizes only the next explicit product prerequisite. It does not authorize immediate productization or release credit.

### `REHABILITATE_GLOBAL_CARRYING_COST`

Emit when correctness/locality hold and the protected byte/runtime effect survives, but global nomination, false positives, RSS/runtime elsewhere, AOM, native/platform burden, or portfolio entropy makes the present rule too expensive to promote. The next work must attack the exported debt without tuning away the protected gain.

### `ITERATE_SAME_FAMILY`

Emit only when the global evidence identifies a specific lower-sufficient R0–R4 refinement inside the same causal family. A new result-bearing experiment requires a superseding freeze; R40 itself may not be edited.

### `RETIRE_DICT9_PRODUCT_FAMILY`

Emit when the global evidence shows the intervention is not product-worthy: it loses a required byte win, creates an unpayable global runtime/RSS/locality regression, has effectively negligible AOM with permanent special-case cost, or requires disproportionate new parser/native/platform state. Preserve R39 as scoped positive evidence and R40 as scoped product-negative evidence.

### `RETURN_TO_FOUNDRY`

Emit only if hostile review shows that closing the remaining product gap requires changing the information ontology rather than an R0–R4 implementation/product intervention. R40 may not disguise R5 work as local tuning.

### `SUBSTRATE_OR_CORRECTNESS_FAILURE`

Emit for accepted-identity drift, nondeterministic output, failed strong verification, broken exact-tree reconstruction, locality >8x, malformed evidence, or a change to the frozen mechanism/controls. No performance interpretation is permitted after this decision.

## Anti-sunk-cost / reopening law

R39’s success does not entitle the family to productization. A hostile-review rejection is a valid Forge result and must be preserved.

If R40 retires or rehabilitates the family, do not rerun lower dictionary levels, new extension subsets, workload-specific allowlists, or threshold sweeps merely because level 9 was close. Reopening requires new causal evidence that addresses the recorded failure mode and a new superseding preregistration.

## Strongest preregistered self-critique

The expected danger is that R39’s two protected views are not independent opportunity: one is a nested projection of the other. A 25 KiB local saving can be scientifically real while still being too small to justify a permanent general-purpose policy branch. R40 is intentionally designed so that “works on backups” is insufficient. The mechanism must either show transferable product economics with near-zero reader/platform burden or be rejected/rehabilitated despite the attractive local win.
