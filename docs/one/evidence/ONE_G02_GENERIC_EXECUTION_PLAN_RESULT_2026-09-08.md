# ONE-G0.2 Generic Execution Plan — exact result

Decision: **ADVANCE_GENERIC_EXECUTION_PLAN**

## Provenance

- branch: `research/cmpct1`
- exact result source: `60e7dc4dee0f6f8673b6d5c00991913d6ee2b2cc`
- Actions run: `34289515470`
- job: `102272699123`
- artifact: `10080796346`
- artifact digest: `sha256:554e5364d0a91302f484664394f93e7bf5ab5520e32767b030efd0b9a1104e6b`
- repetitions: 9 paired, alternating arm order
- exact matrix: 18/18 cells present
- semantic/work-accounting truth: green
- semantic + hostile decision tests: green

Earlier generic-plan sources `efe61e28b031c3353541956b3e9536e083349038` and `146ca033a8144a55e9f2dd1eb7fa3656825788cc` are promotion-inadmissible for the pre-result reasons recorded in the hostile-review receipt. This result is from the corrected non-degenerate / reference-reachability lineage.

## Frozen decision law

Advance required all six 1 MiB rows at <=1.05x reference wall **and** CPU, plus at least 8/18 rows at <=0.95x on both. Result: **9 material wins** and all six decisive rows bounded.

## Exact row summary

| size | family | wall ratio | CPU ratio | compile break-even replays (wall) |
|---:|---|---:|---:|---:|
| 64 KiB | terminal_mix | 0.7091x | 0.7088x | 3.33 |
| 64 KiB | repeat | 0.7075x | 0.7086x | 1.78 |
| 64 KiB | slice_concat | 0.6528x | 0.6535x | 1.92 |
| 64 KiB | xor2 | 0.9792x | 0.9793x | 0.31 |
| 64 KiB | add8_3 | 0.9946x | 0.9952x | 0.58 |
| 64 KiB | shared_basis | 0.7148x | 0.7144x | 2.88 |
| 256 KiB | terminal_mix | 0.8578x | 0.8584x | 1.56 |
| 256 KiB | repeat | 0.9123x | 0.9108x | 2.72 |
| 256 KiB | slice_concat | 0.8694x | 0.8693x | 2.45 |
| 256 KiB | xor2 | 1.0056x | 1.0054x | none |
| 256 KiB | add8_3 | 0.9984x | 0.9982x | 0.53 |
| 256 KiB | shared_basis | 0.8824x | 0.8819x | 3.29 |
| 1 MiB | terminal_mix | 0.9654x | 0.9653x | 2.42 |
| 1 MiB | repeat | 0.9708x | 0.9707x | 2.16 |
| 1 MiB | slice_concat | **0.9035x** | **0.9040x** | 0.68 |
| 1 MiB | xor2 | 1.0034x | 1.0035x | none |
| 1 MiB | add8_3 | 1.0012x | 1.0012x | none |
| 1 MiB | shared_basis | 0.9534x | 0.9531x | 1.81 |

## Causal interpretation

The same six-op ONE grammar benefits from separating one-time validation/range resolution from replay. The gain is large when Python graph/range control is a material share of the operation and naturally shrinks when byte processing dominates.

The 1 MiB arithmetic rows are the strongest discriminator: XOR and add8 remain essentially neutral after graph-control removal (~1.003x and ~1.001x), while their absolute reference medians are ~166 ms and ~478 ms. The prepared control plane therefore did what it was meant to do; the remaining owner on those rows is bulk byte arithmetic, not graph discovery.

This is evidence for a **general reader-internal prepared control plane**, not a terminal/run-specific fast path. No stored opcode, wire byte, Law semantics, integrity requirement or discovery behavior changed.

## Claim boundary / surviving objection

This is hosted-Python full-root evidence. It does not prove a canonical execution-plan format, product-native throughput, authenticated selective-range performance, peak-RSS improvement, or cold one-shot superiority. Compilation is separate and generally amortizes in roughly 0.3–3.3 beneficial replays; arithmetic rows with no replay win have no finite break-even.

The strongest surviving objection is that the current prepared executor still performs XOR/add8 byte arithmetic in Python. A new control structure cannot make unavoidable data-plane work fast. The next mechanism-level test should therefore keep this generic plan and replace only existing bulk arithmetic execution with a bounded native kernel, preserving exact six-op semantics and charging the language/native boundary honestly.

## Decision and next action

**Advance** the generic prepared execution-plan principle as ONE reader-internal research architecture. Next falsifier: native bulk execution for existing XOR/add8 plan operations, tested in the same broad matrix with no workload dispatcher. If native arithmetic wins strongly while non-arithmetic rows remain neutral, retain the split architecture: generic prepared control plane + bulk kernels. If boundary/marshalling cost erases the gain, preserve the negative and seek a more contiguous plan/data representation rather than adding special reader-visible mechanisms.