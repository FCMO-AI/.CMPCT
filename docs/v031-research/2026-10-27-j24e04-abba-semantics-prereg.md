# J24E04 — ABBA evidence-semantic custody preregistration

**Date:** 2026-10-27 UTC. **Owner:** independent stacked J24E04 lane; research/evidence only. **Parent:** PR #576 exact `01b30b9456eb8239a20bfe69956cdd1f36ebff13`, released v0.30.0/r24 unchanged. **Original aggregator blob:** `c55780c9f2d9b1784567daa8f5b40ae9421adceb`; **original comparator blob:** `691576229684df73da68ed39f77583ad870acd32`.

## Primary falsifiable question

J24E01–J24E03 reject duplicate JSON and invalid numerical claims before median arithmetic. Can two *individually well-formed, numerically identical* ABBA input records assert contradictory **measurement semantics** (timing statistic, cache regime, integrity semantics, filesystem comparison disclosures or corpus semantics) and still be aggregated into a single apparent comparable record because the reducer copies only the first run's provenance? Can a base/candidate comparator similarly PASS when each aggregate internally agrees but their reported measurement semantics differ?

**Prediction BEFORE experiment:** Both inherited scripts will accept an adversarially changed semantics label, and the resulting aggregate/report will conceal the contradiction. A minimal candidate can reject mismatches without changing numeric thresholds, arithmetic, bytes, corpus, codec or any production source. The control with identical metadata must retain byte-for-byte equivalent aggregate values and A/A PASS; genuine +7%/+7ms and +1 B regressions must stay FAIL.

**Cheapest rung:** actual script-level subprocess A/B on synthetic deterministic eight-corpus-compatible parity JSON, plus actual previously hosted [J24E03 official artifact #12715177918](https://github.com/FCMO-AI/.CMPCT/actions/runs/40461699834/artifacts/12715177918) as an independent historical legitimate control: all 4 raw arms have identical metadata at HEAD `01b30b94`. Failing a metadata-integrity experiment is **not** evidence that the previous raw numeric performance receipts are false.

## Independent controls and kill/narrow conditions

- Compare untouched original tool source from **the exact prereg parent**, not a paraphrased comparator.
- Preserve source numbers, 0 B size gate, 5% AND 3ms timing gate, ABBA median arithmetic and duplicate/nonfinite checks.
- A semantics-only base/candidate divergence cannot earn PASS, or the candidate is falsified.
- A legitimate matching-semantics historical current run that the new guard rejects falsifies overbroad admission.
- Missing/all-absent provenance remains an independent issue: a consistency guard cannot attest that untrusted self-reported metadata is *true* nor prove same underlying physical corpus. Do not claim cryptographic provenance.
- Aggregate metadata equality is necessary but insufficient; final base-vs-candidate comparison must also check advertised measurement semantics.
- Real product performance cost, RSS and all Reader/Builder/storage operations remain **unmeasured/unchanged**.

## Alternatives

Reject all records without cryptographic attestation (not supported by current benchmark harness), rely on the official same-workflow runner (strong custody context but leaves malformed imported evidence ambiguous), compare metadata only within each ABBA arm (insufficient across base/candidate), or strict two-boundary consistency on currently emitted semantic descriptors (smallest testable improvement). **Choose the last**, with a clear limitation about unverifiable metadata truth.

## Handoff

Research branch only, stack on #576; no merge/release/format/version bump. Before late edits re-read #576 HEAD and source files, avoid touching other owners' branches. Preserve negative historical and source-exact receipts. Decision-changing outcome belongs in PR notes and owner handoff, not automatically in discovery/STATE.json while #574 owns reconciliation.