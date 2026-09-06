# ONE-G0.2 — frontier reconciliation: relation discovery / safe dispatch

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: durable handoff reconciliation; immutable result receipts remain authority

## Why this note exists

`docs/one/CURRENT_STATE.md` is mutable handoff state and currently lags two terminal result families from 2026-09-05. This note prevents subsequent work from reopening already-falsified research or overlooking a later structural advance while the mutable state file is being reconciled.

No experimental result is created by this note. The receipts cited below are the evidence authorities.

## Correction 1 — unconditional local Gear certificate is retired

The structural local Gear certificate result correctly established that a 136-byte complementary witness class could repair real relation-nomination blind spots. The later native carrying-cost experiment answered the open economic question and **retired unconditional every-byte maintenance**.

Authority: `docs/one/evidence/ONE_G02_LOCAL_GEAR_CERTIFICATE_NATIVE_COST_RESULT_2026-09-05.md`.

Exact terminal facts:

- source `f211fbd8388c5b6f637f3b0c9363eb2ccc2360cc`;
- workflow `33971465170`;
- job `101320616350`;
- artifact `9971046571`;
- native witness mismatches versus Python reference: 0;
- median certificate/promoted-baseline ratio across the five large gate controls: **2.2941x**;
- rolling content-local state alone costs roughly +26% to +34% on large controls;
- full every-window bottom-8 certificate typically costs roughly +129% to +134%;
- the main owner is continuous per-window admission work, not rare heap replacement.

Scoped decision: **retire unconditional local Gear certificate maintenance**. Do not reopen by tuning window size, witness count, or timing thresholds. Complementary content-local evidence may be reconsidered only in a sparse, cold, opportunity-gated or otherwise causally different carrying-cost shape.

Therefore any statement that native carrying cost of this exact 136-byte always-hot certificate is still an open question is superseded.

## Correction 2 — overlap-safe generic relation dispatch transferred across 4–256 KiB

The generalized bounded-shift relation primitive later recovered its apparent genericity tax through a correctness-preserving dynamic disjointness proof plus a no-alias fast path, with alias-conservative fallback for overlap.

Authority: `docs/one/evidence/ONE_G02_RELATION_SAFE_DISPATCH_TRANSFER_2026-09-05.md`.

Exact terminal facts:

- source `25e9cc075a22998879a7d4c302248b5834d908f9`;
- workflow `33963218627`;
- job `101298639286`;
- artifact `9968618836`;
- 76 ONE tests passed;
- 35/35 transfer rows passed across 4, 8, 16, 32, 64, 128 and 256 KiB;
- every result struct exact;
- every disjoint transfer row selected the proven-disjoint fast path;
- dispatch/direct range: **0.762662x–0.950811x**;
- dispatch/compact-half range: **0.786643x–0.948439x**.

Scoped decision: **advance safe-dispatch structural transfer**. This is isolated writer-primitive evidence, not integrated discovery or product-speed authority.

The causal interpretation is important: within the tested envelope, the earlier speed penalty of the generalized relation primitive is not evidence that ONE's generic relation model is inherently slower. Compiler alias conservatism was a material exported implementation cost that can be removed safely when non-overlap is proven.

## Current live question

The next result-bearing question is now frozen in:

`docs/one/evidence/ONE_G02_INTEGRATED_DISCOVERY_SAFE_RELATION_DISPATCH_PREREG_2026-09-06.md`.

The experiment asks whether the safe-dispatch win survives when writer-side nomination/opportunity gating, negative-control work, dynamic disjointness proof, exact relation proof and overlap fallback are all charged over the same boundary.

### Hostile-review correction before implementation

The existing shared-observer nomination validation is Python/reference code, while the relation proof/dispatch result is native. Timing a Python nominator plus a native proof and calling the result an integrated-native writer measurement would be methodologically weak: Python interpreter/allocation cost could either drown the native mechanism-level gain or distort its relative ownership.

Therefore **do not consume result authority from a mixed Python-nomination/native-proof timing harness**.

Before the preregistered timing gate is run, build a native nomination bridge that faithfully exposes the same source-identity evidence already produced by the promoted ONE observer, or otherwise instrument the native observer to emit the required cross-object nomination events. Validate that native nomination trace independently against the existing Python/reference nomination semantics before combining it with the safe relation dispatch.

The current native minimizer trace exposes selected anchor positions, which is useful but does not by itself prove the full cross-object exact-reuse nomination semantics. Any bridge must preserve exact witness/equality checks rather than treating a minimizer collision as relation authority.

### Bridge implementation state

`benchmarks/one/one_g02_native_nomination_trace_bridge.py` now implements the first semantic bridge without duplicating the native minimizer. It consumes the promoted native selector's emitted anchor positions, reconstructs the Gear signal independently, and replays the existing nomination policy against fresh validation seeds. Its CI lane is `.github/workflows/one-g02-native-nomination-trace-bridge.yml`.

This bridge is deliberately **not** writer-speed evidence: local auditions and nomination event consumption still execute in the Python oracle. Its only admissible result is semantic equivalence (anchor trace, implied Gear signals, and cross-object nomination counts) or rejection. Native timing integration remains blocked until that equivalence passes and nomination event emission is moved into/instrumented from the native observer.

## Immediate work order

1. preserve the retired always-hot certificate negative;
2. preserve the 4–256 KiB safe-dispatch transfer result;
3. independently validate the native nomination trace bridge against reference semantics;
4. instrument/fuse native nomination events only after semantic equivalence is established;
5. only then run the frozen integrated discovery + safe-dispatch A/B;
6. if the integrated gain is diluted, decompose nomination/admission rather than returning to isolated relation micro-tuning.

No reader-visible ONE opcode, stored-byte change, comparator claim, v0.30 development or September-11 Genesis authority is created by this reconciliation.