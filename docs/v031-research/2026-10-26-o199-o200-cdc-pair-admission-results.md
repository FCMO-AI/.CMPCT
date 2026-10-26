# O199/O200 — prospective CDC admission falsified; held-out indistinguishability replicated

**Date:** 2026-10-26 UTC. **Decision:** RETIRE the tested static, fixed-window, pair-local CDC admission rule as a safe general selector; preserve conditional native CDC representation research. **Evidence:** two genuinely result-bearing source-authenticated hosted scientific runs, both successful as experiments; neither confers product/release credit.

## Exact authority, frozen hypotheses and provenance

- Owner: Draft PR [#516](https://github.com/FCMO-AI/.CMPCT/pull/516); published CMPCT v0.30.0/r24, optional native C table gear blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364`. No Builder, Reader, format, native algorithm, benchmark thresholds or source-lock files changed here.
- O199 preregistration **before O199 implementation/results:** commit `0fa276bff2d88bdccccdc8f9ee2febd4f3833166`, document `2026-10-26-o199-prospective-cdc-pair-admission-prereg.md`.
- O199 hosted run [40375508195](https://github.com/FCMO-AI/.CMPCT/actions/runs/40375508195), HEAD `d5a06b3b7e03062c447b6fa8269da49140760f73`, job `121757361114`, all real steps **SUCCESS**. [Raw artifact 12672984932](https://github.com/FCMO-AI/.CMPCT/actions/runs/40375508195/artifacts/12672984932), ZIP SHA-256 `863f6923299f91f60aaa6a6e124ec6d7762444f0c88ef7f19d096ca8a6c6c8db`.
- O200 preregistration **after fully disclosing O199 and a local pilot** but before held-out seed 811–813 evaluation: commit `24a1b76fa3b7bbefac9e36025434824faf001105`, document `2026-10-26-o200-adversarial-sample-blindspot-replication-prereg.md`. **Do not credit O200 as a wholly unseen mechanism**; only its predeclared new held-out observations are prospective.
- O200 hosted run [40376139680](https://github.com/FCMO-AI/.CMPCT/actions/runs/40376139680), HEAD `6a61e8f787278da082afb60dc32c7e71cd7a62d6`, job `121759585812`, all real steps **SUCCESS**. [Raw artifact 12673234851](https://github.com/FCMO-AI/.CMPCT/actions/runs/40376139680/artifacts/12673234851), ZIP SHA-256 `f85f0c629dc445659326c7025ecc63ae02586bb64b8fcd61025c8b642a820167`.

Source authenticated in each workflow against original O197/O198 owner Git blobs. No source or evaluator relabeling. Both retained `results.json`, `output.txt`, `source.txt`. Green means **experiment completed**, NOT selector hypothesis or product acceptance.

## O199: prospective conservative pair detector, honest negative

The fixed content-only rule sampled 3 × 64-byte anchors, searched up to ±4096 B around each, and compressed twelve stratified 4096-byte windows with zlib-6. It admitted native only when ≥2 anchors matched, a consistent nonzero displacement appeared, and sampled compressed/raw ratio ≥0.90. These numerical conditions were **frozen** before the new held-out run; the rule used no filename, seed, mutation, family or result labels. The experiment assumed one candidate sibling had been supplied; generic corpus pair discovery was NOT implemented.

On 108 paired source-exact cases (seeds 711–713; entropy/repeat/mixed; 4 positions including near-tail; overwrite/shift1/shift256), plus 9 independent unrelated negative pairs:

| Direct result | Hosted observation |
|---|---:|
| Overwrite false admissions | **0** |
| Unrelated false admissions | **0** |
| Eligible high-entropy shifts (excluding tail) | **18** |
| Eligible high-entropy shifts admitted | **18 / 18** |
| Native losses despite admission | **2** |
| Loss #1 | Entropy seed 713, shift1 at byte 2,097,152; **−12.540729%** vs strongest fixed |
| Loss #2 | Same seed/position, shift256; **−12.541333%** vs strongest fixed |
| Total gated-vs-hindsight-best-fixed byte delta across 108 cases | **−20,721,611 B** |
| Unconditional CDC-vs-best-fixed byte delta | **−7,075,639 B** |
| One-shot sum detector CPU (108 source pairs) | **57.844 ms** |
| Detector sampled bytes over 108 pairs | **5,308,416 B** |
| Bounded lookup-window bytes (upper-bound sum) | **2,674,944 B** |

The aggregate research-proxy gain does **not** redeem a false-safe negative: two admitted cases are worse than best fixed. The control chosen when rejecting CDC is an explicitly *gifted hindsight best* of fixed256/512/1024, not free implementable selection. No final archive/CPU/RSS/selective-read measurements follow from these numbers.

An independent local reconstruction of historical SplitMix64 table/CDC arithmetic reproduced all **36×4 = 144** O198 per-policy charged-storage values exactly, before applying the same logic to O199 held-out seeds. This corroborates local mathematical parity; only the linked hosted run is claimed as original-code, source-authenticated execution.

**O199 preregistered strict conservative-safe claim: FALSIFIED.** Zero false positives on unrelated and unshifted cases is real, but insufficient.

## O200: prospective held-out replication of a structural blind spot

A bounded fixed-window selector can inspect the same 49,152 sampled bytes and 192 anchor bytes in two semantically unrelated bodies. O200 kept those exact bytes from a SHAKE high-entropy original while zeroing every other byte. The 1 MiB insertion and equal tail trim were applied to both the original and the masked body. **Seeds 811, 812, 813** and insertion amounts **1 and 256** were frozen after the disclosed earlier pilot, before their hosted result.

- All **6 pairs** of original versus camouflaged data had **identical selector decisions, anchor displacements and sample compressibility ratios**, and all were admitted.
- All **6/6 camouflaged** held-out cases had *negative* source-exact charged CDC savings versus best fixed, around **−19.7%**.
- **4/6 original random** control cases had positive native savings, the other two had losses. All original/native/fixed compressed chunks were independently inflated and **both exact original + sibling bytes reconstructed**.
- Predeclared criterion (≥4 masked losses, ≥4 original wins, identical detector outputs): **MET**. Exact status: `REPLICATED_SAMPLING_NONIDENTIFIABILITY`.

This is stronger than a noisy timing result: **identical bounded decision observations coexist with materially different full-payload economics**. The result does not prove every possible sampled/adaptive policy impossible. It does prove that **this specific 12-window/3-anchor conservative heuristic cannot guarantee positive full-proxy savings**, so it should not be productized or threshold-gardened.

## Counterfactual, strongest critique and next frontier

The cheapest earlier discriminators were (1) preserve the stronger fixed512/1024 controls when measuring shifted suffixes, and (2) put compressible bytes *outside* a detector's inspected windows. Both would have killed the false-safe admission claim before any native-wheel/default-Builder effort. The O200 adversary was intentionally designed after O199 negative evidence, so it does not justify broad claims of blinded unbiased real-world generalization.

The research still has gaps: sibling candidate lookup across N files and its possible O(N²) cost, source native buffer copies, real multi-codec CMPCT storage/index/recovery, CPU wall/RSS/temp memory, selective-read and cross-host packaging. Proxy bytes cannot be represented as final archive bytes; summed detector milliseconds are one-shot measurements, not repeated process-controlled benchmarks. The O185 ABBA failures and O175 cache thrash debt remain **unresolved and unmodified**.

**Disposition:** Retire the current static sample-only *guaranteed-positive* gate. Preserve optional CDC as a narrow high-upside exact representation. Next scientific route must change information/ownership, not tweak sampling thresholds: either derive a *provable charged upper bound* on potential reuse from existing stored physical chunk/index data, or prove an affordable corpus-level relationship candidate-discovery/index path with explicit false-positive, memory, CPU and maintenance costs before attempting real Builder integration. A baseline fallback is an acceptable winner. Separately, high-severity known extraction publication integrity defect [#528](https://github.com/FCMO-AI/.CMPCT/issues/528) merits owner-led product hardening; do not duplicate its ongoing implementation.

**Discovery state:** `docs/discovery/STATE.json` remains an out-of-date cache and was not overwritten. No policy change, merge, release or version bump earned. Both tests are *scientific falsification/evidence*, not a new product feature.
