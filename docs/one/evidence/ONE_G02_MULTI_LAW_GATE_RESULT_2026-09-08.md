# ONE-G0.2 multi-Law opportunity gate and native carrying-cost result

## Decisions

- **Nomination substrate:** `ADVANCE_MULTI_LAW_GATE`
- **Full native carrying cost:** `HOLD_NATIVE_MULTI_LAW_CARRY`

**Exact source:** `86ce1618ef2433f26c568ebc951d11d5b954e4ac`  
**Workflow run:** `34302722535`  
**Job:** `102312897508`  
**Artifact:** `10085573390`  
**Artifact digest:** `sha256:1729578b8bf6380228c3be3035faa198809abdd7df6d161eff7db2e5f75c07f3`

## Structural gate

The corrected 24-cell nomination matrix passed again at this exact source: zero required-family false negatives, zero unexpected nominations on random/compressed-like/false-pattern controls, exactly one charged source scan, and bounded retained feature payload. This confirms the fused run/reuse/add8/xor signals are a credible nomination substrate. The Python loop timing is not carrying-cost authority.

## Native carrying-cost gate

The native candidate preserved semantic equality with the Python oracle on every row and kept run/reuse behavior identical to the native baseline. It also maintained high absolute throughput: all 1 MiB rows exceeded the frozen 150 MiB/s floor.

But the extra per-byte add8/XOR histograms were too expensive relative to the already-required run/reuse observer:

- median wall ratio: **1.34484x** vs frozen <=1.25x;
- median CPU ratio: **1.34364x** vs frozen <=1.25x;
- worst wall ratio: **1.67854x** (`mixed_structured`, 1 MiB);
- worst CPU ratio: **1.67845x**;
- 1 MiB `add8_ramp`: about **1.47368x** wall;
- 1 MiB `xor_chain`: about **1.48286x** wall;
- negative controls were much cheaper, roughly **1.16-1.17x** at 1 MiB.

Decision: preserve the information substrate but do not carry full relation histograms on every byte in this form.

## Causal interpretation / reopening predicate

The red is not semantic and not raw throughput; it is marginal carrying cost. The next rehabilitation must remove most relation-statistic work while preserving the full gate's nominations under adversarial placement. Sampling/deferred relation statistics are valid reopening classes. Threshold relaxation or simply accepting ~34% median observer overhead is not.

This result changes no stored ONE bytes and grants no product-reader or Genesis-comparator authority.
