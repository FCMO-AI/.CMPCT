# G04 attempt-5 retained-intermediate A/B preregistration

Status: frozen prediction before result-bearing execution. Research/evidence only; no release credit.

## Question

Can G04 remove a redundant attempt-5 graph reconstruction by retaining the exact attempt-5 candidate that the accepted v0.29 portfolio already constructed, without changing any candidate bytes, final selected archive, tree semantics, locality, verification, fallback, or release threshold?

## Why this question exists

Current exact-head PR #132 evidence localizes the decisive ML create debt to G04. The superseded scheduler-contention episode was retired because shipping PrefixGraph is contract-ineligible on ML, so ML executes G04 only.

Code inspection then exposes a concrete ownership boundary. `entropygraph_v030_geometry_overlay_g04.build()` first calls `BASE.build()`, where `BASE` is `entropygraph_v029_release`. Its multi-file scheduler builds the exact v0.28 fallback and exact attempt-5 graph concurrently, selects the smaller accepted v0.29 artifact, and deletes the losing temporary candidate. G04 then calls `A5.build_graph()` again to reconstruct the pre-overlay attempt-5 graph needed by Geometry.

On the preserved ML receipt, accepted v0.29 is 13,836,665 B while the pre-overlay attempt-5 graph is 13,836,787 B: the graph loses the floor by only 122 B. Geometry then converts that same graph substrate into a 13,674,824 B final winner, saving 161,841 B versus v0.29. Therefore the losing intermediate is not dead work to G04; it is an immediately required downstream input that crosses an ownership boundary and is currently discarded/rebuilt.

## Hypothesis

A retained-intermediate implementation that preserves both exact v0.29 portfolio candidates until G04 has consumed the attempt-5 graph will remove most of the serial second `A5.build_graph()` cost. On ML this should yield a material complete-G04 wall reduction and plausibly cover the ~10.1% whole-product create reduction still needed for the unchanged 1.25x release ceiling.

The mechanism is reuse, not a new codec or changed selection rule. The accepted v0.29 floor must remain byte-identical. The attempt-5 graph handed to Geometry must be byte-identical to a fresh `A5.build_graph()` result. The final G04 archive must be byte-identical to current G04.

## Strong control

Compare current `G04.build()` against a reuse variant in balanced paired order on the exact ML corpus. The reuse variant must:

1. construct the same v0.28 and attempt-5 candidates with the same builders and process semantics;
2. apply the exact current v0.29 smaller-artifact rule and tie behavior;
3. retain the exact attempt-5 artifact instead of deleting/rebuilding it;
4. feed those exact bytes into the unchanged G0-G4 overlay audition/writer/verification path;
5. apply the exact current overlay-vs-v0.29 final tournament;
6. strong-verify final logical tree identity.

Record complete wall time, child CPU/wall, peak process-tree RSS, temporary retained bytes, candidate sizes/SHA-256, final archive size/SHA-256, selected representation, transform counts and locality evidence.

## Disproof / kill condition

Retire or narrow retained-intermediate reuse if any of these occurs:

- accepted v0.29 floor SHA/bytes differ from current BASE output;
- retained attempt-5 SHA/bytes differ from a fresh current `A5.build_graph()` control;
- final G04 SHA/bytes/tree differ from current G04;
- complete wall reduction is too small to materially approach the ML product gap after charging retention/materialization/RSS;
- the apparent win depends on benchmark identity, altered candidate admission, changed compression settings, weakened verification, or hidden gifted work.

A smaller real win may remain secondary debt but does not justify claiming runtime rehabilitation.

## Alternative explanations

The second attempt-5 build may be cheaper than expected because it runs after the contended v0.29 portfolio; overlay audition/verification may dominate instead; retaining the intermediate may increase peak RSS or temporary I/O enough to erase the wall benefit; or the release-product wrapper may already overlap enough independent work that G04-local savings do not transfer to fresh-process product timing.

## Quality-ratchet

No result may weaken compression/generalization, exact semantics, final archive identity, locality/read amplification, integrity/recovery, RSS limits, compatibility, portability expectations, fresh-process timing boundaries, comparator semantics, or release thresholds. Research timing can authorize productization work only; it cannot unlock v0.30 release.

## Decision law

- **REUSE_HEADROOM:** byte/tree identity passes and the complete G04 wall reduction is material enough to plausibly close the current ML gap after resource charges. Productize the smallest ownership seam, then rerun unchanged fresh-process authority.
- **SECONDARY_REUSE:** identity passes and a stable win exists but is insufficient for the product gap. Preserve the win only if carrying cost is justified; continue to the next dominant owner.
- **NO_MATERIAL_REUSE:** identity passes but wall/resource economics are immaterial. Retire this route as primary.
- **INVALID:** any identity, semantic, accounting, or instrumentation invariant fails. Repair evidence only; claim no mechanism result.

## Claim boundary

This experiment tests reuse of an already-computed exact intermediate. It makes no claim that attempt-5 itself is optimal, that v0.29 portfolio scheduling is globally optimal, or that Geometry should be admitted more broadly. It changes no shipping code until a measured result earns productization.