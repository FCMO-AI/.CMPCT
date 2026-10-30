# J24I50f — healthy-archive pathname substitution fools a late reopen, not the held Reader

**2026-10-30 UTC.** Dependent on J24I50e exact `92adc1c4a48d3e52349880acd3655e781862dec8` on [#807](https://github.com/FCMO-AI/.CMPCT/pull/807). New, narrower source-identity discriminator frozen before modifying the physical test. No production ABI, Builder, reader, format, release or benchmark change.

## Counterfactual: is one corrupted replacement too weak?

The J24I50d/e control rebinds a corrupt-but-index-admissible pathname and proves: held Python verifies *old* inode, old C verifies *old* inode, new C rejects the replaced path. This proves descriptor retention, but it does not yet demonstrate the dangerous **both-successful-for-different-archives** outcome of a naïve future Python-to-native delegate.

## Strongest simple falsifier

Reuse the very same held `CMPCT(original)`, held C archive handle and retained unchanged WAV/FLAC golden from J24I50e. After the corrupt-new-path control, **overwrite the replacement pathname** with the *second already-committed builder-independent* direct RAW conformance archive from `tests/conformance/v24-direct-codecs.json` (codec 0, member `raw.bin`), validate its *published* full SHA-256 and distinguish both physical objects.

Expected:
1. Held Python `CMPCT.verify()` still succeeds on original `wav16.wav`, and held native C verify remains 1 for the original source.
2. A **fresh C ABI `cmpct_open(original)` and complete verify also succeed** — but it verifies the distinct foreign archive. A fresh Python Reader on that pathname names `raw.bin` rather than `wav16.wav`, while the original already-open Python object still names `wav16.wav`.
3. Exact physical SHA of the retained original remains frozen, and the *foreign* SHA matches its independent fixed vector. Original pathname and resources restored before leaving the control.
4. Structured result reports both success statuses together with the **different member identities**. Fail if the source objects become conflated.

**Decision:** if the two simultaneously successful verifications authenticate different archive identities, a future `CMPCT.verify()` implemented as a late `cmpct_open(self.path)` has the wrong owner even if all checksums and error codes function perfectly. This is not a claim that shipping Python currently delegates or that an attacker lacking pathname write authority can force a swap. It does not address mutating the same inode, Windows rebinding, journal recovery or same-handle concurrent mutation. The C ABI should remain separate until it can use Python's original held source/generation, or its narrower independent pathname contract is explicitly surfaced.

No frozen evaluator change; no new release credit; this is a semantic integration falsifier against the strongest healthy-archive control.
