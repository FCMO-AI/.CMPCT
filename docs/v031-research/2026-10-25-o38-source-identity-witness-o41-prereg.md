# O41 — Independent exact-source witness for inherited O33 receipts (preregistered 2026-10-25 UTC)

**Evidence tier:** infrastructure / scientific-receipt integrity. **Status at freeze:** prediction only, no new O41 program, product code, hosted result, merger or release.

## Authority and collision boundary
Released CMPCT v0.30.0 / on-disk r24 is unchanged. This separate child branch starts from O38 product HEAD `dffc6da03b588e209843f2fc6e219e5bce3a7800`, PR #392. Do not change PR #392's Reader, PR #385's owner, PR #393's O39 replication, any frozen O33 instrument, research timings, official parity evaluator, or shared Discovery state. Current PR #392 conversation documents the source-label discrepancy; O41 owns only a fail-closed extra **witness**, not another speed experiment.

## Baseline defect and falsifiable hypothesis
Unmodified original O33 instrument blob `8aabcc100843475068031e39a8a4cfb74edfddac` writes historical constants `source_base=9c9cecc6...` (O28) and `source_candidate_product=0edb7bc6...` (O31) into `o33-raw.json`, regardless of the supplied `--base-source` and `--candidate-source`. O38 correctly reused that historical instrument against actual O31/O38 sources; its separate workflow source pins and child paths are meaningful, but the raw header fields are **not** proof of O38 identity. Raw records must remain immutable evidence, including their incorrect inherited-context labels.

**Hypothesis:** a small, independent, read-only postprocessor can bind each actual O33 child to checked out Git source HEAD, exact Reader blob and loaded native module path; validate the full 96-observation / six-SHA-committed-archive pairing; and emit one machine-readable receipt explicitly classifying inherited header labels as historical constants, without rerunning/tampering with timings or source.

## Alternatives / cost
Documentation annotation alone is cheap but not fail-closed and does not guard future reuse of this harness. Editing historical O33 labels or weakening its original source blob pin destroys provenance; forbidden. Reimplementing the timing instrument or repeating all performance trials is unnecessary if the old per-child evidence plus new source pins suffice. Selected a minimal independent witness and negative-tamper tests, with no new source/Reader implementation.

## Predictions and disproof
1. Original source checkout `O31_OWNER_SHA=0edb7bc6e832deb1b403fea50c36e655da9844fd`, base Reader blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`; candidate O38 Reader blob `4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867`, and evidence checkout HEAD explicitly recorded. Actual child `source`, `module`, `native_module` must point into the corresponding checked source directory, not a third tree.
2. All six genuine corpus files are SHA-256 authenticated against the raw manifest; 512/4096 × plain/fanout/chain, 96 alternating child observations and exact label/group order required. Any missing, duplicate, fabricated, reordered, relabelled or out-of-root child fails closed.
3. Original O33 `source_base`/`source_candidate_product` fields are retained verbatim and labelled *historical instrument constants, not measured source identities*. A tampered field is also rejected because O33's known instrument bytes are frozen.
4. Mutation controls on an otherwise valid raw fixture—swapped source path, swapped Reader module, altered archive SHA, malformed ABBA group—must be rejected. A witness that passes tampered evidence is a failed O41 result; do not downgrade controls.
5. The original O38 research CI may rerun on the new evidence-only HEAD to create a **new** checked-out source witness. That is **not** a new O38 product speed gain. Source product `src/` must have identical tracked tree to pinned O38; official parity and installed-wheel receipts from O38 cannot be newly credited to a documentation/tool child without executing them.
6. No numeric core version, format revision, benchmark corpus/comparator, safety evaluator, semantic contract, FCMO Hub or shared Discovery policy change.

## Deciding question
If this fail-closed witness survives the original source-bound scientific run and its hostile negative controls, O38's metadata-custody caveat can be marked resolved **for the new exact execution only**. If source/ABI/corpus identity cannot be proven, retain the ambiguity and stop. Highest-leverage subsequent step is integration/review with #385 owner and not another narrow hardlink micro-optimization.

## Timing and ownership
Other hourly activations may overlap. Before further writes re-read the candidate branch and PR #392/#393. This branch owns evidence-witness changes only; no force-overwrite of shared artifacts.
