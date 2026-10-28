# J24C08-LB — why bounded fixed-chunk admission cannot become O(1) by merely changing languages

Date: 2026-10-28 UTC. **Analytical lower bound / design constraint, not a benchmark, shipping result, new format or release gate.** This is an adjacent counterfactual to J24C08's optional ABI3 experiment, not a second active implementation.

## Exact question and model

In revision-24 the Reader receives an arbitrary `S_CHUNKS` list of `N` blob indices and a logical-size declaration. Correct admission requires (1) *every* index is a valid non-bool integer in `[0,M)`, and (2) the sum of the referenced exact blob lengths equals the declared logical size, before the public tree may admit the member. These index bytes are self-hashed inside an archive; a malicious archive constructor can create a different well-hashed index. The hash authenticates the index's bytes, not that their arbitrary contents satisfy the semantic invariant. Existing fixed conformance and signed hostile cases remain normative.

## Lower-bound argument (deterministic, no separately trusted proof)

Assume a decision procedure examines fewer than `N` arbitrary references on some valid input. There exists an unread position `k`. Construct a second archive whose authenticated index is recomputed accordingly: retain every examined reference, row and blob unchanged, but replace `refs[k]` with out-of-range integer `M`. The procedure observes identical fields in every reference it did inspect and must give the same decision, yet one archive must be accepted and the other rejected. Contradiction. Therefore exact acceptance/refusal must inspect every arbitrary reference, `Ω(N)` in worst-case input reference visits. Checking only aggregate lengths has an independent indistinguishability attack with two in-range blobs of different lengths. This argument holds irrespective of C, Rust, SIMD or Python. It assumes the scanner has neither a trusted external proof of validity nor an alternative representation that eliminates per-position arbitrary references.

A revision-24 archive-level checksum or an index digest **is not such a proof**: an adversarial writer can hash an invalid index. A separately trusted admission attestation, independently verified proof system, or format/ownership redesign could change the information available, but must charge proof bytes, creator time, reader cost, trust/failure semantics, portability and hostile falsification. A local cache is not a proof after file mutation.

## Decision for current candidate and strongest alternative

J24C06 measured 2.81–4.66× *constant-factor* constructor acceleration with stable ABI3 under six OS/minor combinations, with direct CPython C still faster at the research level. J24C08 asks whether the optional wheel transfers that gain to a real installed Reader with strict fallback. **The lower bound does not predict J24C08's measured performance**, only constrains algorithmic ambition. A successful native scanner does not retire an `Ω(N)` cost as N grows; repeated threshold gardening at the same per-reference algorithm cannot achieve a generic sublinear bound.

The broader frontier after this measurement is to reduce the number of independently validated arbitrary relations through generically discoverable representation/ownership (e.g. bounded repeat-run/reference-group encoding), or to carry and validate a true proof that replaces per-element checking. Any such research needs its own prospective exact-format/byte/proof/verification economics; it is not imported into this draft. The simpler safe control remains original strict Python with no new C dependency.

## Disproof / limits

This is a *decision-tree lower bound*, **not** a claim that every valid archive necessarily takes Ω(N) wall time on every machine, that vectorization is useless, or that a trusted proof/stronger representation is impossible. It does not apply when a different archive contract supplies a stronger verified invariant, when rows are compressed as a generically safe structured group and N is no longer the actual independent relation count, or when a prior trusted validation result is immutably and correctly shared. If evidence demonstrates such a non-circular shortcut with complete charged costs, the applicable model changes and this bound no longer precludes it.

No frozen scores, released format, existing admission requirement or discovery policy changed.
