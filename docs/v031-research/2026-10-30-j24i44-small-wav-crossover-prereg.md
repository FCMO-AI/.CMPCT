# J24I44 — prospective native WAV verification small-member crossover

**Preregistered 2026-10-30 UTC, before the new instrument and any result.** Scope: existing open draft #788, inherited direct codec-2 `Archive::verify_complete()` only. This is a diagnostic admission/performance court, **not** an attempt to change ABI, on-disk format, reader semantics, a frozen benchmark, a release or product behavior. Research branch source HEAD at start: `d48c43b803cb09e2bd64f385ab46c56ab885328b`.

## Why this decision matters
J24I43 proved 2.18x (8 MiB) and 5.18x (32 MiB) native full-verification time gains on real Builder WAV/FLAC, plus substantial RSS/rchar savings. Those WAV files have a 44-byte RIFF header that crosses a multiple-of-8-MiB boundary, provoking an extra *full* decode under the old 8-MiB-range-loop. The gain does not establish a positive speed result for **small direct WAV** where the baseline decodes only once. The complete-verifier fast path is unconditional for direct codec 2. A small-case regression could reverse the engineering promotion choice or require generic bounded routing; a positive result would justify a simpler unconditional architecture.

## Primary falsifiable question
Under unchanged Builder codec selection and authenticated physical bytes, does the streaming Rust product verifier avoid material wall/CPU or memory regressions against the exact old Rust product verifier for genuinely selected sub-8-MiB direct WAV/FLAC? Identify the crossover if it exists; do not choose a threshold by fixture identity.

## Prediction and controls
On deterministic single-file PCM16 mono 44.1-kHz random-walk WAV at 64 KiB, 256 KiB, 1 MiB, 2 MiB, 4 MiB and 8 MiB *PCM*, test real Builder selection. **No forced codec:** if a case selects a different codec, record and exclude it from codec-2 timing claims; preserving fallback is a product property. For each selected FLAC, assert Python exact read and verify, detached SHA-256 of original/physical archive, and source-exact installed Rust original/candidate acceptance and exact member size. Two separately compiled native probe binaries must be measured on the **same physical archives**, same runner, ABBA/BAAB interleaving and raw warmup-excluded repetitions; record per-call monotonic wall, Linux rchar and VmHWM, with A/A controls for drift. A 8-MiB overlap is calibration to J24I43, not independent confirmation of the 32-MiB claim. No product speed claim unless both source and semantic parity hold. Baseline is exact #784 parent `0faa25827e7393f927252876d40e9f6cb53e5a24`; candidate is the exact #788 current source without product edits.

## Kill/narrow condition
Any accepted/correct Builder original rejected by candidate is correctness red; any native candidate overhead materially above noise on a small FLAC is a regression debt (even if large WAV wins). No cherry-pick by selecting only winning sizes. A/A sham must not be ignored if its drift explains a speed delta. If Builder never selects codec-2 for small cases, classify that empirical admission boundary rather than synthesize forced direct-codec bytes. Preserve all raw observations and source/fixture hashes. Any non-equivalent smoke, missing artifact, missing exact-source pin, incorrect negative or ambiguous noise => UNPROVEN, not a win. Generic admission may follow only after a repeatable physical crossover and whole-system economics.

## Alternatives / BONK
1. Keep old complete verifier: simpler for one decoding pass but expensive larger FLAC / RSS.
2. Unconditional streaming (#788): 64-KiB PCM staging, lower memory; might be slower for small sample counts due to per-sample overhead.
3. Split by generically authenticated physical codec/logical size if a real crossover emerges: adds branching/testing burden, not justified before this court.
4. Rewrite Claxon sample iteration to blocks: wider mechanism and product complexity; defer unless current instrument shows material residual cost.
5. Leave both as draft and prioritize other product debt if the small-case signal is weak.

## Scope/custody
One operator updates only `research/j24i44/`, this prereg and a new J24I44 scoped workflow in #788. Existing J24I43 workflow and source Rust product files remain untouched. No concurrent owner of this narrow cost-crossover question was found in current open PR title/search review. The existing `docs/discovery/STATE.json` remains staleable cache and is not a lock. New CI run must attach raw physical evidence with explicit failure on missing artifacts and report its run ID + source SHA. Exact frozen corpora/comparators and release thresholds are immutable.
