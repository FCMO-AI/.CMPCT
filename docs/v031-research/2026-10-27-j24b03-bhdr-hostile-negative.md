# J24B03-H — frozen hostile-BHDR prediction falsified in hosted court

**Recorded:** 2026-10-27 UTC. **Status:** SCIENTIFIC NEGATIVE / UNRESOLVED NEW PHYSICAL OFFSET QUESTION.
**Original prereg:** [2026-10-27-j24b03-bhdr-hostile-prereg.md](2026-10-27-j24b03-bhdr-hostile-prereg.md), committed first at `91e362fa8651d8f346c39758f8d144796eea5245`.
**Instrument:** `research/j24b03_bhdr_hostile_court.py`, independent referee `research/j24b03_bhdr_hostile_referee.py`.
**Exact first hosted run:** [Actions #40554574952](https://github.com/FCMO-AI/.CMPCT/actions/runs/40554574952), Ubuntu/macOS jobs **FAIL** at the unchanged original scientific assertion on released `main`:

```python
assert selection["hex"] == PAYLOAD[7:15].hex()
```

Original 24-case J24B03 size-ownership court and independent referee on both hosts **passed before** this independently scoped hostile extension failed. The hostile extension had prospectively predicted that all five physical-header corruptions of RAW owners (magic, codec, `usize`, `csize`, `rml`), on both regular file and symlink, would be ignored by historical fast `read_range()` while returning the *original eight requested payload bytes*. At least one real source-exact corrupt-header sample **returned different bytes**, falsifying the stronger predicted data identity. The original assertion is intentionally **not changed** to declare success; the downstream candidate-side 10-case decision and ABBA economics never ran in these jobs and remain unmeasured.

**Mechanism-level explanation (source derivation, not a measured per-case attribution):** published `main@80c358f...` RAW `read_range` reads its offset from the physically decoded `BHDR.rml` as `base = pos + BHDR.size + rml`, without checking it against signed blob-table `ml` or verifying physical owner bounds. The prereg intentionally mutated `rml=1` while retaining the original physical payload placement and unchanged blob-table `ml=0`. That predicts an accepted but **one-byte-shifted** range for the metadata-length case. This is a materially different failure from the earlier size 136/128 tail spill and demonstrates why a physical offset must be validated, not merely a physical size. A stronger next independent diagnostic should record the exact fault and returned bytes on unchanged released source and demand *candidate rejection for every corrupt field*, without pretending the first prospective assertion passed. Preserve a distinct outcome/episode, exact control source and results before promotion.

**Strong controls:** original intact 128-byte wire and frozen vectors PASS in the initial J24B03 three-host court [#40546227217](https://github.com/FCMO-AI/.CMPCT/actions/runs/40546227217); published main RAW fast path source is separately browsable under `src/cmpct/reader.py:235-239`. This is not evidence that the candidate failed the safety invariant. The hosted failure occurred before the candidate hostile branch or performance rung; acceptance of the candidate's original 24-pair geometry court remains proven independently. No format/Reader product promotion, no weakening of frozen comparisons, no merge/release.

**Independent unblock:** J24B03-P original-versus-guarded economics has been given its own unchanged-threshold [workflow](../../.github/workflows/v031-j24b03-direct-range-cost.yml), so a scientifically honest hostile negative cannot prevent a separate economic decision.
