# ONE-G0.2 selective-safe discovery gate repair — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: preregistered before repair execution

## Mission Lock / Referee

The hosted Genesis candidate-adapter probe exposed a real product-boundary incompatibility before the frozen 15-workload gate: the general Law archive may nominate a new `xor`/`add8` Law whose predictor root is itself a Law. Whole reconstruction remains valid, but the authenticated native range planner intentionally supports only terminal constant Laws backed by a Surprise operand plus a Fill operand. The probe therefore failed on a nested relation chain with `OneError: native Law terminal requires one Surprise and one Fill operand`.

Preserve this as a negative result. Do not weaken the probe by accepting fallback and do not touch the Genesis workloads. The repair question is whether encoder-side opportunity gating can avoid emitting a topology that the currently promoted selective reader cannot execute cone-proportionally, while still exercising ordinary exact reuse, ADD8, XOR, Fill and Surprise through the same ONE grammar.

## Falsifiable hypothesis

If automatic relation nomination is restricted to predictors whose stored root is a direct `surprise` terminal, then the general archive will remain byte-exact and deterministic, will preserve productive one-hop ADD8/XOR Laws, and every emitted Law-bearing file in the transfer probe will remain executable by authenticated native selective reads without fallback. A nested relation opportunity after a Law root must be deliberately rejected to Surprise rather than emitted as a reader-inaccessible Law.

This is an encoder discovery/pruning policy only. It adds no reader-visible operation, changes no ONE wire format, and performs no reader discovery.

## Transfer fixture

Use deterministic non-Genesis data with independent relation islands so both Law classes are still tested without post-result removal:

1. random/hash-stream base A;
2. ADD8(base A, constant);
3. unrelated random/hash-stream base B (forces Surprise);
4. XOR(base B, constant);
5. exact copy of the XOR output (exercises reuse of an existing Law root without nesting a new Law);
6. Fill;
7. noise, tiny nested file, and empty file.

Additionally include a dedicated unit falsifier where `A -> ADD8(A) -> XOR(previous)` would previously create a nested Law. The third root must now be Surprise and must remain whole/selective exact.

## Disproof tests

HOLD or RETIRE this repair if any of the following occurs:

1. whole reconstruction differs from source;
2. authenticated selective reconstruction differs or falls back for any non-empty transfer file;
3. deterministic wire identity changes between identical repeated builds;
4. a relation rooted in another Law is still automatically nominated by this general-archive discovery path;
5. direct one-hop ADD8 or XOR from a Surprise predictor is no longer discovered on its dedicated relation island;
6. exact reuse, Fill, or Surprise coverage disappears from the transfer probe;
7. an operation outside the canonical ONE grammar appears;
8. Genesis workload machinery is imported/generated/executed;
9. the repair changes format, integrity, recovery, or reader ontology instead of encoder opportunity policy.

## Evidence and decision

Retain the original hosted failure as the negative authority. Re-run the same candidate-adapter lane after the repair and require its existing no-fallback selective assertion to pass. Record root-class counts and the explicit nested-relation rejection test.

- `ADVANCE_SELECTIVE_SAFE_DISCOVERY_GATE` only if all disproof tests pass and the hosted candidate-adapter probe becomes green exact-source.
- `HOLD_SELECTIVE_SAFE_DISCOVERY_GATE` if semantics are correct but the no-fallback transfer boundary remains incomplete.
- `RETIRE_SELECTIVE_SAFE_DISCOVERY_GATE` if the pruning causes semantic, ontology, or direct one-hop relation regressions.

This result cannot be used as Genesis scoring and cannot justify changing the frozen 15-workload corpus or comparators.