# O196b — official ABBA source-path native admission preregistration

Date: 2026-10-26 UTC
Status: PRE-RESULT, follow-up to completed O196 clean-wheel negative.
Starting PR #516 exact `75cd1a7c7daaab6982a42043166481a24b3fe7df`; direct base #509 `62792a7fc61b033b306b4445c337ed123946514d`. This is an additive prediction, NOT a rewrite of O196 original prediction or wheel result.

## Why another experiment is decision-changing

Hosted O196 wheel-run `40346318252` directly proved absence of the optional C helper in a clean ordinary Linux wheel, with an independent positive control showing changed segmentation when C is explicitly injected. But the **canonical official ABBA** uses a different execution environment: candidate `pip install -e '.[audio,test]'` and sets `PYTHONPATH=<candidate src>` for B arms; base materializes historical Rust core in a separate worktree and uses `PYTHONPATH=<base src>` for A arms. Extrapolating wheel result to that workflow without checking both paths would be unjustified.

**Primary question:** when reproducing the official source-path imports on one Ubuntu runner with the canonical direct base and candidate, does either `codec._cdc` actually load `libcmpct_cdc.so`?

**Prospective prediction:** both source-path environments have `_cdc is None`, no adjacent `libcmpct_cdc.so`, identical source `codec.py` SHA and identical fixed-CHUNK segmentation for >2MiB deterministic input. If so, O185's changed C object was not exercised by those two arms under the evidenced harness setup, sharply narrowing causal attribution of the three contradictory performance runs to environment/noise/other effects; DO NOT declare the performance RED resolved.

**Strong simpler control:** wheel O196 negative + static `pyproject.toml`/loader path inspection predicts no C, but cannot prove editable/install-specific generated artifacts. One source-exact minimal import/run probe is cheaper and causally sharper than repeating a 7-repetition × 4 round corpus.

**Alternative:** editable installation or base native-materialization may generate the optional helper adjacent to `codec.py`; then preserve helper-positive admission and investigate which source/implementation ran. Inability to install Rust native format dependency is INFRA failure, not a no-helper finding.

## Procedure, acceptance and limits

1. Checkout candidate actual HEAD; `git worktree add --detach` the direct PR base SHA, prove exact source paths and C blob.
2. Reproduce benchmark candidate `pip install -e .`, and run original `tools/materialize_performance_base_native.py` on the detached base to supply its authentic Rust core; no modification of the benchmark tools or source.
3. In fresh processes under the **same interpreter** and controlled `PYTHONPATH=<base src>` then `PYTHONPATH=<candidate src>`, with work directory outside the source, attest `codec.__file__`, adjacent optional C object, `codec._cdc`, exact source hashes, and deterministic `cdc_chunks` outputs. Preserve both machine-readable JSON witnesses and environment provenance.
4. If both absent, assert fixed-fallback cuts, exact reassembly, and identical source/segmentation, producing `O196B_DECISION=ABBA_PATHS_BOTH_CDC_ABSENT`. If present, do not fail merely for surprising truth: output `PREDICTION_FALSIFIED` with per-arm identifiers. Fail for wrong module/path, malformed cut, missing evidence, or unequal source without explanation.
5. Do not weaken frozen r24 performance gates, rewrite the original RED or claim a new product improvement. This is attribution evidence only; it cannot establish which incidental host factor caused the RED.

**Disproof:** source SHA mismatch with direct-base/candidate tree, unexpected import path, nonexact split, missing result-bearing run/artifact, or any falsely asserted no-helper result. An observed nonempty `_cdc` disproves predicted absence and demands separate provenance before attributing speed.

**quality-ratchet:** distinguish actually executed engine from unexecuted source diff using exact source-path import, preserving all negative performance and cache evidence.
