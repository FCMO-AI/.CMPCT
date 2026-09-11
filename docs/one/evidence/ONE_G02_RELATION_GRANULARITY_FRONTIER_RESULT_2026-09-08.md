# ONE-G0.2 relation granularity frontier — exact result

Date: 2026-09-08
Primary branch: `research/cmpct1`
Research version: ONE-G0.2

## Exact authority

- scientific source carried unchanged by PR head: `89cf68820881c2f500e86827c5e097cdc9e22168` (the only delta from primary source `5c34f643a4f4ffb918bced337a62bac7391d178d` is an evidence-trigger workflow comment);
- GitHub Actions run: `34300834716`;
- job: `102307184731`;
- artifact: `10084859606`;
- artifact digest: `sha256:93ccafae2e8dc7a666572afd24f15417e0bde8b7802c6fa4eaa20aa2f8aeebd3`;
- exact frozen 42-cell benchmark completed successfully.

## Verdict

`ADVANCE_RELATION_GRANULARITY_FRONTIER` — **representation-density scope only**.

The result proves that the non-redundant add8/XOR relation principle has an economical coarse-grain region inside the existing six-op ONE grammar without a new opcode or a widened resource limit. It emphatically does **not** prove that the current execution shape is fast enough.

## 1 MiB frontier

| relation block | nodes | candidate/literal wire | reference work/literal | materialized/literal | native prepared replay/literal wall |
|---:|---:|---:|---:|---:|---:|
| 64 B | 24,577 | inadmissible | — | — | — |
| 128 B | 12,289 | inadmissible | — | — | — |
| 256 B | 6,145 | inadmissible | — | — | — |
| 512 B | 3,073 | 0.531119x | 2.333333x | 2.500000x | 17.1–17.3x |
| 1,024 B | 1,537 | 0.515495x | 2.333333x | 2.500000x | 9.34–9.38x |
| 2,048 B | 769 | 0.507683x | 2.333333x | 2.500000x | 5.21–5.39x |
| 4,096 B | 385 | **0.503777x** | 2.333333x | 2.500000x | **3.26–3.30x** |

add8 and XOR have identical wire ratios because they use the same generic node geometry. Every admitted row reconstructed byte-exactly through the independent evaluator and preserved the root commitment. No aligned duplicate block contaminated the matrix.

The fine-grain failure is itself an important result: a 64-byte discovery descriptor is not a viable dense storage boundary under `max_nodes=4096`. ONE must separate **evidence granularity** from **Law emission granularity**.

## Causal interpretation

The wire result is strong: at 4 KiB relation spans ONE stores a unique parent once plus generic relation/control information and lands near half of literal wire. But the current generic graph executes each parent Surprise, relation Fill and derived add8/XOR node as materialized intermediates, then the root Concat copies the complete result again. Prepared native arithmetic cannot rescue that geometry: the arithmetic loop is no longer the owner; graph materialization and root assembly are.

Therefore this is not a speed/density system win and must not be reported as one. The reader-side result violates the campaign's efficiency objective badly enough that relation research cannot advance to canonical status on density alone.

## Next causal gate

Writer-side discovery should become **budget-aware and span-growing**: cheap fine/coarse probes may nominate a relation, but verified evidence should be coalesced to the largest Law span justified by the data before nodes are emitted. A dense 1 MiB relation corpus requires at least 512-byte pair spans under the present node envelope; 4 KiB gives the best measured wire geometry.

In parallel, reader work needs a representation-neutral Law-fusion test. The promising optimization is not a relation codec: compile root `concat` plus generic `add8/xor(parent, fill(constant))` cones into bounded direct root writes so parent bytes and derived bytes are produced into their final positions without materializing Fill/relation children and recopying them through Concat. The same graph, root, limits and generic operations must remain authoritative. If that cannot materially reduce the 2.33x work / 2.5x materialization penalty, this relation line remains density-only evidence.

No comparator authority, benchmark requirement, recovery/integrity rule, or frozen v0.30 state moves from this scoped advance.
