# ONE-G0.2 — sparse relation gate evidence replay preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Why this replay exists

The original exact-source sparse relation-gate workflow (`c76590233f3880d6e91fbd76c04217c6cc78d3a9`, run `33965168847`, job `101303891835`) never reached its frozen benchmark. The run stopped in the pre-result ONE test step and preserved no benchmark artifact. Therefore there is **no scientific sparse-gate timing/classification result to inherit** from that activation.

The benchmark itself, `benchmarks/one/one_g02_shift_relation_sparse_gate_integration.py`, remains frozen in the repository and already contains its Mission Lock, controls, thresholds and decision law. This replay does not alter that benchmark, its kernel, or any threshold. It exists only to execute the previously preregistered experiment under the now-current project test environment and preserve a result-bearing artifact.

## Authority

All decision criteria are the unchanged criteria embedded in the frozen benchmark:

- identical enabled/disabled classification versus the ungated exact safe dispatcher at every size;
- identical best shift for every enabled relation;
- 100% productive-relation retention;
- at least one cheaply rejected pair at every size;
- gate compared bytes <=1% of logical relation bytes;
- each size gated/baseline <=1.03x;
- seven-size median gated/baseline <=0.95x.

Sizes remain 4, 8, 16, 32, 64, 128 and 256 KiB; pair identity remains supplied by the frozen adjacent-pair batch. Arbitrary pair discovery is still out of scope.

## Claim boundary

A pass would establish only that this **cheap exact-shift falsifier** is a viable writer-side turnstile once a candidate relation pair already exists. It would not prove arbitrary pair nomination, and it would not by itself solve the currently rejected unconditional rich-certificate carrying cost.

A fail must remain a fail. Do not retune the two-supporting-sample threshold or sample count after this replay.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.