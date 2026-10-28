# J24G18/J24G18b — authentic signed Reader transfer: finite native predecode gate breaks acceptance/recovery

**Date:** 2026-10-28 UTC. **Scientific decision: FALSIFIED as a semantics-preserving default Reader gate.** Research only; no product/format/version/release mutation. This conclusion is anchored in the exact physical and source-bound hosted court below, not in a self-reported C microbenchmark.

## Ownership, inherited law, and preregistration

- Published baseline: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, on-disk revision 24. Actual published Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Parent research/scanner: J24G17 #684, `06617f194c45ebb38dda0592ff5e5196e204af80`, Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. J24G17's ~1.064x ordinary CPU result and hostile RSS saving-by-refusal are **component-tier only**; not re-earned here.
- J24G18 preregistration: `45fe006e1009da92d9db17a8e1684c488619ce77`, committed before the experiment. Distinct published-Reader control addendum preregistered at `63ee7c53aa524a0945f0d33fdbab44e82bf067c6` **before** its separately measured hosted court.
- No edits to #684's owner branch, #681's scanner parent, #574's Discovery `STATE.json` ownership, released source, or existing frozen evaluators.

## Physical evidence, strongest controls, and results

**Initial exact-source successful court:** [GitHub Actions #40726472459](https://github.com/FCMO-AI/.CMPCT/actions/runs/40726472459), code/evaluator HEAD `6d5fbd2374f5fe3a08a34f2520bee2cb60cd7f19`, artifact `12833650948`, artifact ZIP SHA-256 `6979d62ae8f27a4efa23e8346a7b557a9f1f4dd5cec2457dfe16f77958a24628`. Six physically saved `.cmpct` files from one authentic first-party Builder base; a genuine Writer `append_rename` control; four separately appended SHA-256-signed deltas. Three fresh subprocess runs per case per arm: **54 raw observations**.

The same physical archives were replayed by (i) unmodified installed parent Reader, (ii) a research subclass running existing J24G17 native token scan after signed-footer verification and before original MessagePack decoding, and (iii) a research subclass that maps `TooManyNodes` into an invalid generation and continues fallback. **No Reader product source is modified.**

| SHA-authenticated scenario | Parent unmodified Reader | Native cap=65,536; exception propagates | Catch-and-continue policy |
| --- | --- | --- | --- |
| Builder clean checkpoint | owner at depth 0 | same | same |
| Genuine Writer rename | renamed member at depth 1 | same | same |
| Signed valid linked delta, 70,000 tiny extension objects | **renamed member at depth 1** | **TooManyNodes: open fails** | **owner at depth 0: silent stale generation** |
| Signed valid orphan delta, 70,000 objects, `prev=0` | **old owner recovered at depth 0** | **TooManyNodes: no fallback** | old owner recovered |
| Signed valid under-cap linked rename | renamed member at depth 1 | same | same |
| Signed malformed nested map key | ValueError (reject) | ValueError (reject) | ValueError (reject) |

Every opened arm read the exact member, read a nonempty range, checked its SHA and executed `verify`. The **canonical accepted linked delta** is not a fixture identity exception: the benign unknown `extension` map key is accepted by original MessagePack and ignored by the same original delta-operations interpreter in both actual published and parent Readers. The appended footer covers its entire payload hash.

Original hosted referee: **447 positive assertions; four deliberate record forgeries rejected**. Subsequently a completely separate external `struct`/SHA-256/MessagePack/Zstd audit replayed the actual GitHub ZIP, independently reconstructed the physical revision-24 Builder checkpoint and its Zstd `S_BLOB` member from raw bytes without importing CMPCT, and checked **432 assertions and four manipulated controls**. Its scope is the six-file corpus, **not a complete independent CMPCT Reader**.

**Published-source historical control:** [GitHub Actions #40727047486](https://github.com/FCMO-AI/.CMPCT/actions/runs/40727047486) at exact code HEAD `331d20a3798b01354b25ff99af0a4d696cf8ec91`, artifact `12833118357`, ZIP SHA-256 `1fe3e31afe306fd03dc44d1871fa5db8240f150f955f56a235e5224bd7e736e5`. A fourth arm compiles the **actual original released Reader Git blob**, source-verified at `main@80c358f8`, in an isolated Python module against the same installed revision-24 codec stack. It returned the exact same published acceptance and fallback outcomes on all six archives: the signed 70k linked delta is accepted with renamed content, orphan tail recovers owner, malformed fails. Thus the negative is **not limited to the parent experimental Reader**.

The first published-source court's special job itself finished **FAILURE from an independent referee expectation bug**, which incorrectly expected `released` to have depth zero in the linked-overcap case; its complete physical archive/result ZIP was preserved. The behavior under test succeeded, and a separate independent external replay over all **72 raw observations**, six physical files, actual Builder-index and S_BLOB/Zstd bytes, signed SHA/pointers, and published identity reported **554 assertions PASS and four manipulated controls REJECTED**. The hosted referee was fixed in follow-up source commit `52cf658115a9b04d05a1567ef43671b60ea8c04a`. Historical Reader source compilation was also moved outside Reader-open timing in `ca0d489103e3dcbaee710a27f34977ea74566ec7`, since the earlier released-arm ~10 ms readings included Git/subprocess/compile work and **must not be used for performance comparisons**. The subsequent exact-head hosted run must be checked before calling the final HEAD specialized job green.

## Disproof, alternatives, and scientific disposition

- **Hypothesis (naive default finite native gate): FALSIFIED on exact accepted revision-24 bytes.** The gate substitutes a changed acceptance contract for memory control. A SHA-signed but oversized orphan triggers an exception that aborts the recovery scan rather than finding the previous committed checkpoint.
- **Catch-and-continue mitigation: FALSIFIED for correct latest-generation selection.** It recovers an orphan, but it also discards a signed, semantically valid latest rename generation and silently exposes an older file tree. It cannot distinguish those cases from token count alone.
- **Always defer to canonical full decoder on cap exceed:** this simpler countermechanism preserves acceptance, but by construction **forgoes the high-memory materialization avoidance** in the high-node case; a scan may incur extra CPU without delivering the claimed global RSS bound. This is a causal bound, not a measured integrated solution.
- **Alternatives still open:** schema-first streaming with full malformed-key semantics, parse-time bounded objects without changing accepted input, or a separately authorized, explicit opt-in resource policy with truthful failure/recovery semantics. Their product economics/portability have not been demonstrated.

The cheapest transferable prospective discriminator was a single originally accepted **signed linked delta** above the cap, paired with a signed orphan on the same Builder checkpoint. This pair identifies the incompatibility and catch-and-continue ambiguity without spending a full benchmark suite. The C microcourt could have been accompanied by this pair before considering productization; the experiment earns a **localized selection lesson** but not yet a new Discovery Engine policy amendment.

## Final-form evidence debt and publication boundary

The research did **not** change compression ratio, archive bytes, create/extract throughput, native ABI, Windows/macOS, full product memory bounds, published baseline, format revision, version or release. The released control dynamically compiles real Git reader source and uses the current compatible revision-24 codec namespace: it proves source semantics, not a reconstructed historical wheel timing. No timing numbers from different worker/source-setup boundaries should be compared as speedups. General tests, exact-head specialized rerun, full system fuzz/conformance and version-promotion checks remain independent gates.

**Next highest-leverage target:** Do not merge this default finite-token preflight; preserve J24G17's economical C scan as a research seed for **explicit policy** or a future semantics-preserving parser. Under the current accepted archive contract, the native preflight alone cannot both reject a valid high-node delta and claim equivalent reconstruction. Switch frame to one-pass, validation-preserving semantic materialization/streaming or a higher-value product owner; do not garden 65,536 or create another catch exception workaround.
