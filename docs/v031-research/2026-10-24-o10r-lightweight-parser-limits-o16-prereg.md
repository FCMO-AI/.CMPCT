# O16 — lightweight signed-generation parser-limit import seam (prospective preregistration)

Date: 2026-10-24 UTC. Status: **PREDICTION FROZEN BEFORE PRODUCT IMPLEMENTATION**.
Owner: Phased3 isolated child of PR #365; other branches remain untouched.

## Problem, exact baseline, strongest control

Released CMPCT v0.30.0 is immutable; candidate O10R PR #365 HEAD `54c998200b1908b696ade049fe94df71a736c284`, Reader blob `2402721258531a56cfa2a53dcbd81874fd6c1f76`, is the owned correct resource-ceiling implementation. O13 PR #371 observed on 80 fresh-process authentic r24 archives a repeatable +2.796ms checkpoint import+constructor at 512 operations and +1.728ms at 4096 relative to the O9 Reader. Journal timings were essentially neutral; CPU/RSS claims are bounded to the observed Ubuntu/CPython 3.11 scope. Whole-process checkpoint +5.801ms / +6.70% (512) and +3.052ms / +3.18% (4096) were separately observed and are *not* official performance-gate verdicts.

Static source observation: O10R `CMPCT._decode_generation_payload` and `_index_from_footer` import `ParserLimits` and `ResourceLimitError` from `cmpct.validation` **before** discovering whether the signed generation is a checkpoint. `validation` is the much broader strict parser/index proof module; only journal replay actually needs `_apply_delta`. This is a suspected D1/D2 dependency/import-ownership cost, not yet a measured causal result.

Independent negative: PR #371 exact-head official parity Actions 40118727310 produced FAIL with four reported regressions, including media/cli/create +5.35%/+6.883ms, nested/cli/create +5.47%/+3.552ms and sparse/cli/extract +6.92%/+3.814ms. The parity failure is a real gate observation and is not waived by changing import architecture. It need not be causally attributed to the proposed change because O13 changed no product source relative to #365.

## Hypothesis and mechanism

Move **only** the public error-class and `ParserLimits` declarations, including identical configured environment semantics, into a small dependency-light `cmpct.resource_limits` module. Re-export **the same actual Python classes** from `cmpct.validation`; import them in the Reader from `cmpct.resource_limits`; leave strict journal `_apply_delta` in `cmpct.validation` with deferred import.

Expected: checkpoint-only ordinary Reader open no longer causes `cmpct.validation` to be imported during generation admission, preserving every compressed/decoded generation and depth ceiling. Fresh-process checkpoint import+constructor should save some (possibly most) of O13's +1.7–2.8ms checkpoint-specific increment versus O9, without sacrificing O9's 4096 journal speedup. This prediction could be false if other Reader paths already import validation or if Python startup noise dominates.

## Simpler controls and alternatives

- Cheapest falsifier: in a clean Python subprocess, construct an authentic signed checkpoint archive and check whether `cmpct.validation` appears in `sys.modules`; compare before/after source under exactly the same dependency environment. Verify journal still loads shared validator when signed deltas exist.
- Stronger economy check: repeated source-exact warm CPU and fresh interpreter checkpoint/journal ABBA with identical archive content, same runtime, same process boundaries, all original measurements preserved. Do not infer a product win from import isolation alone.
- Keeping eager validator import is simpler if measured savings cannot justify a new module. Copying ParserLimits independently is forbidden because it creates drift. Broad validator import rewriting is unjustified.
- Hot-path micro timing cannot substitute for exact-head product/security, three-host package conformance or full parity.

## Hard invariants and disproof

1. `validation.ParserLimits is resource_limits.ParserLimits`, likewise `ValidationError` and `ResourceLimitError`; same public classes, defaults, eight env overrides, errors and inheritance. No change to `preflight_archive`.
2. Genuine signed over-limit generation and depth must fail in ordinary Reader on Ubuntu, Windows and macOS exactly as O10R; unrestricted valid archives must still decode identically.
3. O9 signed journal replay, symlink prewrite safety, MessagePack duplicate-key rejection, Writer/recovery/hardlinks and strict preflight must all survive.
4. Reader-only authenticated checkpoint admission must avoid `cmpct.validation` eager import when otherwise unused; if not, reject the causal explanation.
5. If median fresh-process checkpoint startup gain is <=1ms, or recurring CPU/RSS/packaging debt erases it, prefer the existing simpler owner; do not promote complexity on speculative microbenefit.
6. Never change format revision 24, benchmark corpus/gates, validator semantics or v0.30 records. Treat any performance FAIL as a FAIL pending causal replication. No merge or release without exact-head gates.

## Decision unlocked

If lightweight shared policy removes a material checkpoint cold-start cost while keeping O10R safety and exact journal economics, preserve it as a productization candidate. Otherwise retire the import-split frame as a low-yield family and prefer shipping the known safe O10R with documented small checkpoint cost.

## Evidence classification

O13 = prior source-bound product-startup research; O16 before-hosting mechanism = architectural hypothesis; source identity, CI and adversarial full-product tests required for product credit. No discovery-policy edit is proposed.
