# ONE-G0.2 — Proof-led branch-and-bound admission result

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Decision:** `advance_proof_led_admission`  
**Result-bearing source:** `c54baabeb5e0b323c43e6fa616a71587200d93c2`  
**Workflow:** `33961530718`  
**Job:** `101294129445`  
**Artifact:** `9968094327`  
**Artifact zip SHA-256:** `a1f27cd01cc974547175e69de4309c4b8eb4b1ce7fd5545653a32e2a397b6dcb`

## Mission lock

The immutable stratified-proof damage envelope established that the global >=50% one-byte coverage majority was a recall bottleneck: it prevented any exact proof attempt while 16–32 KiB of real minimizer-only exact reuse survived. The preceding every-32-byte fragmented adversary also established that one-byte coverage by itself is not a sufficient admission signal.

This superseding experiment removed **only** the global majority prerequisite. It preserved:

- 64-byte coverage stride;
- signed displacement set `{-2,-1,+1,+2}`;
- inherited minimum four support hits for nomination;
- sixteen deterministic proof strata;
- at most one coverage-supported proof owner per stratum;
- four exact 64-byte proofs required for admission;
- maximum sixteen proof attempts;
- 5% gate / promoted incremental-selector elapsed ceiling;
- 25% modeled read-traffic ceiling;
- all inherited false/positive controls;
- the frozen contiguous-damage matrix and 16 KiB mandatory surviving-opportunity floor.

The hypothesis was that distributed **exact proof** could own specificity, making the global majority redundant.

## Exact result

`tests/one`: **76 passed**.

The immutable transfer returned:

> `advance_proof_led_admission`

### Previously lost damage regime recovered

| Damage | Marginal exact reuse | Exact proofs | Gate / incremental selector | Modeled read fraction | Admission |
| --- | ---: | ---: | ---: | ---: | --- |
| 32 KiB front | 32,768 B | 4 | 0.812% | 8.958% | pass |
| 32 KiB middle | 32,767 B | 4 | 0.714% | 8.203% | pass |
| 32 KiB tail | 32,767 B | 4 | 0.707% | 8.209% | pass |
| 40 KiB front | 24,576 B | 4 | 0.869% | 9.151% | pass |
| 40 KiB middle | 24,575 B | 4 | 0.861% | 9.145% | pass |
| 40 KiB tail | 24,575 B | 4 | 0.680% | 8.185% | pass |
| 48 KiB front | 16,384 B | 4 | 0.878% | 9.358% | pass |

All frozen damage rows at or above the mandatory 16 KiB marginal-opportunity floor were admitted. The prior majority gate had produced **zero proof attempts** on most of these rows.

The rows below the frozen floor remained diagnostic. They reveal an expected geometry boundary rather than a promotion failure: with only 12 KiB, 8 KiB or 2–4 KiB of surviving relation, fewer than four of the sixteen proof strata may contain exact support, so the unchanged four-proof requirement can reject them.

### Specificity survived without majority

The crucial hostile control remained rejected:

- `false_fragmented_shift_every32`: 0 B marginal opportunity, +1 one-byte coverage hits = **1,019 / 1,024**, **16 proof attempts, 0 exact proofs**, gate disabled; cost ratio **0.706%**, modeled read fraction **8.197%**.

The positive fragmented control remained admitted:

- `fragmented_shift_every96_control`: **760 B** marginal opportunity, 1,023 coverage hits, **12 attempts / 4 exact proofs**, gate enabled; cost ratio **0.691%**, read fraction **8.606%**.

Random/incompressible and compressed controls also remained disabled. On random 1 MiB the proof-led gate cost **0.781%** of promoted incremental-selector elapsed and modeled **8.324%** reads. On zlib-random payload it cost **0.820%** and modeled **8.547%** reads. Zero 1 MiB exited before proof at **0.500%** of incremental-selector elapsed and **1.563%** reads.

### Inherited shifted positives survived

- ordinary one-byte shifted 512 KiB pair: **524,288 B** marginal opportunity, 4/4 exact proofs, cost ratio **0.685%**, read fraction **7.835%**;
- zero-anchor shifted 8 KiB starvation case: **8,192 B** marginal opportunity, 4/4 exact proofs, cost ratio **2.224%**, read fraction **10.937%**;
- hostile +/-1 and +/-2 64 KiB relations: **65,534–65,535 B** marginal opportunity, 4 proofs in 4–5 attempts, roughly **0.669–0.705%** of incremental-selector elapsed and ~**8.17–8.19%** modeled reads.

## Scientific interpretation

This is stronger causal evidence than a threshold win. In the tested relation family, global support majority was redundant once the writer required **distributed exact reconstruction evidence**. Removing that redundant prerequisite substantially improved recall under localized damage without accepting the known high-resemblance/zero-reuse adversary.

The surviving reusable principle is:

> use cheap coverage to nominate a candidate relation, but let bounded distributed exact proof—not global resemblance percentage—own admission specificity.

This fits ONE's speed law: expensive discovery should be branch-and-bound by cheap falsification, and admission must be tied to exact reconstructable information rather than a resemblance score.

## Strongest surviving criticism

This is still not a general discovery engine. The testbed knows a half-to-half relation and only auditions four small signed displacements. It proves an **admission architecture**, not a universal candidate generator. It also spends up to sixteen exact proof attempts on random data; that remains cheap here, but only because the candidate family is tiny.

The next result must therefore charge the branch-and-bound path against the complete promoted discovery cost. A cheap gate that merely adds work in front of the normal minimizer is not a product win.

## Next decisive test

Freeze an end-to-end writer A/B using the current tail-return 8 KiB selector as baseline. The candidate may use proof-led shift admission to short-circuit the expensive general selector only when it has four exact proofs; otherwise it must preserve the baseline path. Measure complete discovery elapsed, source/proof traffic, retained state and recovered opportunity per row, and derive the break-even frequency of shift-positive cases on ordinary negatives.

Promotion requires exact opportunity preservation on the inherited matrix and a materially positive **marginal information yield per total encoder work**; shifting cost into a pre-gate or relying on a favorable workload mixture is not enough.

## Claim boundary

Writer-discovery research only. No reader-visible ONE operation, CMPCT format, v0.29/v0.30 comparator, product-speed claim or release authority changes.
