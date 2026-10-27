# O217 — C-backed chunk-owner histogram: valid strict mechanism, insufficient full-Reader gain

**2026-10-27 UTC · Scientific result · no product or release promotion.**

## Provenance / preregistration

- Exact parent O216: PR #570 at \`6989b25640be2c82436bb77ec545dd15816f698b\`; owner J24C02 #569 at \`c5e13bb3fbb4cdade8b64246658ce7c7818de41f\`. Historical release remains v0.30.0/revision 24.
- Prospective O217 contract committed **before the instrument** at \`f0fc63bc7f01b4ead27d5e399c856f2ce1e6ac56\` ([preregistration](2026-10-27-o217-multiplicity-batched-chunk-admission-prereg.md)).
- First source-tested real Reader installation HEAD **\`b2f01032c31f1315369e512ab5e16dd4eb38b2f2\`**, original unchanged Reader Git blob \`dbd4ac576a05a47eae97e1e40de89cf1de4405166\`, unchanged validator \`51c2849061f99a4afeddb7666956b24566ce7de0\`, O216 original experiment \`7002fe2db2bfc41fffbc94584cc1904922d1c1fb\`.
- GitHub [Actions #40460065751](https://github.com/FCMO-AI/.CMPCT/actions/runs/40460065751): **SUCCESS**, Ubuntu 24.04 / CPython 3.11. Original archived [artifact #12714445362](https://github.com/FCMO-AI/.CMPCT/actions/runs/40460065751/artifacts/12714445362), downloaded ZIP SHA-256 **\`1e3edc50801e4daf15b69b63f8843aab05d9503541108ff221214582ca9391e0\`**; ZIP CRC independently checked, source HEAD and Git validator/Reader blobs matched. Inherited original O215 tests: **12 passed**.
- **25/25** strict source-validated semantic cases matched the original validator (19 inherited O216 cases + six new mixed-owner/late-malformed cases). Additionally a separately executed **30,000-case LOCAL MODEL** cross-check found no original-vs-Counter mismatch; this is subordinate to installed product evidence and did not execute CMPCT.
- 6 structurally distinct signed r24 fixture shapes; **144 independent process observations / 720 timed wall and 720 timed CPU samples**, raw retained in artifact. Reported timings are per complete installed Reader constructor+close, excluding process startup, source archive construction, and independent archive receipt parsing.

## Exact scientific comparison

Four arms on exactly the same physical archive within each shape: original strict validator; O216 strict exception-only loop; O217 strict type-scan + Counter + weighted sum; and **deliberately unsafe** no-check lower-bound oracle (timing control, zero safety/product credit). Units are milliseconds for median-of-process-median real Reader wall time.

| Authenticated archive structure | Original strict | O216 strict | O217 batched strict | Unsafe timing lower bound | O216 / O217 |
|---|---:|---:|---:|---:|---:|
| 1 reference / 1 owner | 0.1170 | 0.1149 | 0.1196 | 0.1092 | **0.961x** |
| 4,096 repeated / 1 owner | 1.7571 | 0.4821 | 0.4766 | 0.1509 | **1.011x** |
| 65,536 repeated / 1 owner | 26.1045 | 6.2373 | 5.7769 | 0.9951 | **1.080x** |
| 262,144 repeated / 1 owner | 103.3914 | 24.2817 | 22.7189 | 3.7462 | **1.069x** |
| 65,536 refs / 256 owners | 26.8400 | 6.9188 | 5.4450 | 1.2045 | **1.271x** |
| 4,096 distinct refs / 4,096 owners | 2.8766 | 1.4554 | 1.8455 | 1.2262 | **0.789x** |

**Preregistered decision: \`BATCHED_REF_OWNER_COUNTER_INSUFFICIENT_OR_NARROW\`.** The prospective claim required >=1.25x improvement over already optimized O216 for **both** high-count repeated-owner shapes. Observed improvements only **8.0%** and **6.9%**. One positive mixed-owner shape at 1.271x does NOT rescue the hypothesis: all-distinct input slows down ~26.8% versus O216 (1/0.7886), and the strongest possible compression of repeated refs still leaves large absolute constructor debt.

At 65,536 repeated refs O217 full-Reader wall remains 5.777ms versus 0.995ms unsafe bound; at 262,144 it remains 22.719ms versus 3.746ms unsafe bound. This is **not** a valid substitute for the strict safety mechanism, only a reason to seek a fundamentally different execution/proof frame.

## Causal interpretation and negative debt

The type-check loop visits every input ID in Python and the Counter traversal creates per-ID counts in a native-backed layer. Both passes consume work; Python object allocation scales with **number of distinct IDs**. The measured slight gain over O216 on repeated references is inadequate for the next product architectural step, and distinct-ID cases can lose. This is a negative against *this Counter formulation*, not against all batch/native validation nor against a future separately authenticated sparse index summary.

O216's ~4x per-reference fastpath result remains true and source-controlled, but is **also insufficient for promotion**; O217 adds no generic product improvement strong enough to retire J24C02's material cold-open debt.

## Self-critique / generalization boundary

- Research-only runtime substitution of Python validators into the original installed Reader; **no shipping product patch**. The high-count repeated fixture is deliberately structural, not representative corpus prevalence.
- Single Ubuntu runner and synthetic r24 inputs; no macOS/Windows, native-core, real corpus, RSS or allocation-specific high-water measurement, sustained concurrent open, hostile filesystem, or format transition. These cannot be assumed.
- The initial scientific SUCCESS is a result on HEAD \`b2f01032...\`, not automatically green CI on later documentary/auditor commits. Later exact-head CI and independent auditor are separate.
- The unsafe control skips fixed-reference admission; it fails correctness and cannot be promoted even when substantially faster.
- Local model 30,000-case fuzz is not equivalent to a test of installed CMPCT and cannot upgrade the source scope.

## Counterfactual / discovery lesson

The fastest prospective falsifier was to compare against **the already optimized O216 path**, not the original expensive validator, and include one all-distinct structural control. Both conditions could be recognized *before* implementing a product change. O216 and O217 jointly show that Python-loop constant-factor work is not enough for robust, fast, exact on-open admission of extremely high-cardinality r24 reference lists. This result justifies **local scientific retirement**, not modifying global discovery policy from one extra mechanism.

## Immediate handoff

1. **Do not merge or promote O217 Counter admission.** Preserve all 25 strict cases, original ratio negatives, source identities and raw hosted evidence.
2. Owner J24C02 #569 must retain S_CHUNKS/S_CDC/S_SPARSE admission correctness and preserve its +25.56/+102.05ms baseline product debt. J24C02 #569 and O216 #570 already own this surface; this science changes neither.
3. Highest-value new **different-frame** action: test an implementation that validates contiguous reference vectors with a bounded native/typed scan and exact per-entry integer/range/sum semantics, OR prove when a separately authenticated layout can subsume the scan without changing r24 correctness. Charge native conversion, startup, memory, hostile invalid-index semantics and 3-host complexity. A cheaper static lower-bound/discriminator should precede another full product path.

No \`docs/discovery/STATE.json\` edit: active coordination #574 owns outdated state reconciliation and this narrow negative is already durably discoverable in the PR. No release, new format, version bump, weakening of evidence gate or canonical product mutation.
