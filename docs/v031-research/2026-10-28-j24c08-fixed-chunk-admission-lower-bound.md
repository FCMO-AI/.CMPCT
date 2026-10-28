# J24C08-LB — why bounded fixed-chunk admission cannot become O(1) by merely changing languages

Date: 2026-10-28 UTC. **Analytical lower bound / design constraint, not a benchmark, shipping result, new format or release gate.** This is an adjacent counterfactual to J24C08's optional ABI3 experiment, not a second active implementation.

## Exact question and model

In revision-24 the Reader receives an arbitrary `S_CHUNKS` list of `N` blob indices and a logical-size declaration. Correct admission requires (1) *every* index is a valid non-bool integer in `[0,M)`, and (2) the sum of the referenced exact blob lengths equals the declared logical size, before the public tree may admit the member. These index bytes are self-hashed inside an archive; a malicious archive constructor can create a different well-hashed index. The hash authenticates the index's bytes, not that their arbitrary contents satisfy the semantic invariant. Existing fixed conformance and signed hostile cases remain normative.

## Lower-bound argument (deterministic, no separately trusted proof)

For a direct reference-validation algorithm whose information about semantic validity comes **only from the individual reference values** (not from a trusted semantic proof, a previously established immutable validation receipt or a precomputed semantic classifier), assume it inspects fewer than `N` references on a valid input. At least one position `k` is unread. In the direct-reference observation model, changing only `refs[k]` to an out-of-range integer `M` leaves every examined reference unchanged but changes the required answer. Therefore any zero-error algorithm in **this model** must examine each arbitrary reference, `Ω(N)` in worst-case reference visits. Even if checking reference bounds is unnecessary, sum validation has the analogous adversary using two in-range blobs with different lengths. This is a decision-tree lower bound on *semantic inspection of arbitrary references*, independent of the implementation language.

**Cryptographic digest caveat:** recomputing the signed/hashed index on the mutated archive **does change its digest**. Thus the argument does not claim the two *entire archives*, including their hash fields, are observationally indistinguishable. Rather, a self-consistent archive digest is not an externally trusted semantic certificate of correct reference ranges/sums: an adversary can compute the digest for an invalid array too. A hypothetical digest-keyed perfect semantic classifier, a separate proof with verified soundness, or cached prior authenticated semantic admission is an **additional information source excluded by this model** and must be separately evaluated. In particular this is not an unconditional computational lower bound against arbitrary cryptographic preprocessing.

A revision-24 archive-level checksum or an index digest **is not such a proof**: an adversarial writer can hash an invalid index. A separately trusted admission attestation, independently verified proof system, or format/ownership redesign could change the information available, but must charge proof bytes, creator time, reader cost, trust/failure semantics, portability and hostile falsification. A local cache is not a proof after file mutation.

## Decision for current candidate and strongest alternative

J24C06 measured 2.81–4.66× *constant-factor* constructor acceleration with stable ABI3 under six OS/minor combinations, with direct CPython C still faster at the research level. J24C08 asks whether the optional wheel transfers that gain to a real installed Reader with strict fallback. **The lower bound does not predict J24C08's measured performance**, only constrains algorithmic ambition. A successful native scanner does not retire an `Ω(N)` cost as N grows; repeated threshold gardening at the same per-reference algorithm cannot achieve a generic sublinear bound.

The broader frontier after this measurement is to reduce the number of independently validated arbitrary relations through generically discoverable representation/ownership (e.g. bounded repeat-run/reference-group encoding), or to carry and validate a true proof that replaces per-element checking. Any such research needs its own prospective exact-format/byte/proof/verification economics; it is not imported into this draft. The simpler safe control remains original strict Python with no new C dependency.

## Disproof / limits

This is a *decision-tree lower bound*, **not** a claim that every valid archive necessarily takes Ω(N) wall time on every machine, that vectorization is useless, or that a trusted proof/stronger representation is impossible. It does not apply when a different archive contract supplies a stronger verified invariant, when rows are compressed as a generically safe structured group and N is no longer the actual independent relation count, or when a prior trusted validation result is immutably and correctly shared. If evidence demonstrates such a non-circular shortcut with complete charged costs, the applicable model changes and this bound no longer precludes it.

No frozen scores, released format, existing admission requirement or discovery policy changed.
