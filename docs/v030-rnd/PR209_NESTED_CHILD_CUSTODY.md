# PR #209 nested-child candidate custody — decision note

**State:** evidence-enablement / no product credit  
**Source boundary:** PR #209 exact head `893233de8a5820b5760b6f83e5805830f663b232`  
**Date:** 2026-09-27

## Question

Did PR #209's failed complete-product compression discriminator actually execute
`compact-r24-release-policy-v1` inside the shipping r24 child process that owned the measured fallback bytes?

## Source proof

PR #209 installs the candidate in the outer benchmark interpreter by rebinding
`sys.modules["experiments.entropygraph_v030_release_product"]` and the matching attribute on the
`experiments` package.

The shipping r24 owner is `R24PrebuildProcess`. Its `start()` method launches a new interpreter with
`python -m experiments.entropygraph_v030_r24_process_prebuild --worker ...`. The child environment receives
the repository `PYTHONPATH`, but no candidate-module identity. In that fresh interpreter, `_worker()` imports
`experiments.entropygraph_v030_release_product` canonically and invokes its
`_locality_bounded_r24_build()`.

Parent-process `sys.modules` rebinding is process-local state. With no argv/environment/module-identity carrier,
the nested child cannot inherit PR #209's outer alias.

## Contradictory evidence this resolves

PR #208 run `35997996511` measured the `disable_medium_binary_only` arm at the exact genuine-r24
Incremental Backups floor:

- genuine r24: 8,036,531 B;
- candidate arm: 8,036,531 B;
- delta: 0 B;
- conservative selected-VZIP decoded-context amplification: 0.44988960623446705x.

PR #209 run `36004181224` then failed the unchanged complete-product ablation at the same workload:

`canonical v0.30 product regressed genuine r24 bytes: neutral_hostile_v1/06_incremental_backups`

The ablation aborted before publishing its normal JSON receipt. Runtime was skipped. Selective-read evidence
completed independently.

The process-boundary source proof explains why the positive same-process policy result and the negative
complete-product result can coexist without scientifically disproving the candidate policy.

## Focused falsifier

`benchmarks/v030_pr209_nested_child_binding_falsifier.py` regenerates the accepted repaired Incremental
Backups substrate and compares three strong-verified artifacts:

1. genuine r24;
2. parent-interpreter compact-r24 candidate;
3. exact shipping nested `R24PrebuildProcess` child.

The prior product-disproof claim is falsified if the parent candidate reaches the genuine floor while the nested
shipping child remains larger.

## Decision rule

If the focused mismatch reproduces, authorize exactly one evidence-custody repair: carry explicit candidate
identity through the existing nested r24 process boundary and rerun the unchanged global compression parity.
Do **not** reopen Deflate cutoff, packing-threshold, comparator, workload, locality, or release-gate tuning.

If a correctly bound complete-product run is then red, retire the family. If it is green, proceed to the inherited
runtime/RSS/selective/native/recovery/platform gates without claiming release authority early.

Production remains v0.29.0 / canonical r24. v0.30 remains merge/tag/version/publish locked.
