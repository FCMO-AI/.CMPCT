# R41 — Global Dictionary-Effort Concept Compression Superseding Preregistration

Status: **FROZEN BEFORE ANY R41 RESULT-BEARING EXECUTION**

Supersedes, before execution, `docs/v030-rnd/R41_GLOBAL_DICTIONARY_EFFORT_CONCEPT_COMPRESSION_PREREG.md`.

The original R41 freeze is preserved unchanged as proposal history. No R41 result-bearing execution occurred under it. This superseding freeze makes exactly two measurement-law clarifications required to keep the experiment causal. Every other corpus, arm, mechanism, identity, correctness, locality, runtime, RSS, carrying-cost, anti-sunk-cost and terminal-decision rule from the original R41 freeze remains unchanged and is incorporated here by reference.

## Amendment 1 — do not contaminate timed arms with a second dictionary compression

The original freeze requested the number/raw bytes of individual candidates whose level-9 dictionary output differs from level 12. Computing that exactly inside either timed arm would require performing the *other* dictionary compression too, adding work that the actual candidate or control would not perform and corrupting the frozen runtime comparison.

Therefore R41 freezes the causal measurement as follows:

- record the already-existing dictionary-eligible candidate count and raw bytes for each workload/arm;
- record whether `global-dict9` changes the **complete deterministic archive bytes** relative to `dict12-control`, and the exact complete-byte delta;
- do **not** dual-compress eligible candidates inside a timed arm merely for diagnostic accounting;
- do **not** infer candidate-level output-difference counts from complete-archive deltas;
- if candidate-level differential attribution is later needed, it requires a separate untimed diagnostic and cannot retroactively change R41's terminal decision.

This amendment removes a measurement side effect; it does not relax any byte or performance gate.

## Amendment 2 — explicit runtime evidence required for promotion

The original freeze required global runtime/effort evidence to be directionally compatible with one writer policy. To make that clause mechanically falsifiable before execution, promotion now requires:

> at least one workload where dictionary eligibility is non-zero must show a **material build-wall improvement of `global-dict9` versus `dict12-control`**, using the same symmetric materiality boundary as the release timing law: improvement greater than **3 ms absolute AND 5% relative**.

No aggregate average may satisfy this condition on behalf of an activating workload. Non-activating workload timing differences are runner noise and carry no causal credit.

This is an additional hurdle, not a relaxation.

## Complete frozen R41 authority after supersession

Read this file together with the original R41 preregistration. The effective frozen experiment is:

- exact accepted repair-v6 15-workload matrix;
- accepted v0.29 aggregate identity **137,499,525 B**;
- inherited v0.30 absolute saving hurdle **687,783 B**, unchanged;
- 3 arms: `release-all-exact`, `dict12-control`, `global-dict9`;
- 5 fresh processes per arm/workload;
- only intervention: every candidate already eligible for archive-dictionary compression uses effort 9 instead of 12 in `global-dict9`;
- no new family predicate, subset, threshold, workload/path/name/hash dispatch, dictionary-training change, codec, grammar, retention, parser, locality, recovery, reader or platform behavior;
- strong verification, deterministic bytes, accepted tree identity and `<=8x` applicable locality are mandatory;
- zero material runtime regressions versus release and zero >10% RSS regressions versus release for promotion;
- zero lost strict byte wins versus release and zero activating workload turned into a byte loss versus release for promotion;
- Incremental Backups protected gain must survive as defined by the original freeze;
- dictionary eligibility must extend beyond the single R40 backup workload;
- at least one activating workload must satisfy the explicit material runtime improvement versus dict12 defined above;
- permanent policy state must be zero or negative relative to today's full-build level-12 / transaction level-9 split;
- exact terminal decision grammar remains `PROMOTE_GLOBAL_DICT9_PRODUCT_PREREQUISITE`, `RETAIN_SPLIT_POLICY_R40_BOUNDARY`, `REHABILITATE_GLOBAL_DICT9`, `RETIRE_DICTIONARY_EFFORT_UNIFICATION`, or `SUBSTRATE_OR_CORRECTNESS_FAILURE`.

Once any R41 result-bearing execution begins, this superseding freeze and the original freeze it incorporates are immutable. Any later scientific change requires R42 or another explicitly superseding experiment while preserving R41 evidence.
