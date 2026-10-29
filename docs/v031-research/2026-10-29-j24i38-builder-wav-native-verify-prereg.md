# J24I38 — Real-Builder WAV-FLAC native verification amplification: preregistration

**Pre-result prediction; research-only.** Prepared on 2026-10-29 UTC, source base [J24I37 #772](https://github.com/FCMO-AI/.CMPCT/pull/772) at exact `2d0dd4031b8c0fb2c42b715b6a4569199a2309a3`, before adding this probe. No product, format, release, benchmark, or correctness criterion is altered. This is a *different admission/population* than J24I37's fabricated direct-Zstd archive, rather than a duplicate implementation of native core owned by #765/#759.

## Question and why it matters
Does the confirmed J24I37 `ceil(N/8MiB) × N` native verify amplification affect the **canonical Builder's actual WAV/FLAC representation** for otherwise ordinary large PCM WAV files? Builder's `.wav` exception avoids CDC at >1MiB; native codec-2 reconstructs whole member for each `read_range` slice. This is a strong candidate for real-world manifestation of #772's synthetic-only effect.

## Existing evidence / baseline
J24I37 #772 at `2d0dd40…` measured direct-Zstd research archives (8/32/64MiB) with ~8x compressed read-character amplification and 4.24x wall at 64MiB, but the high-RSS one-shot comparator does not preserve the verifier's bounded-memory contract. Current code in `src/cmpct/builder.py` retains entire `.wav` even above 4*CHUNK rather than using CDC, and `native/cmpct-core/src/wavflac.rs` documents full reconstruction before slicing. No Builder WAV full-verify amplification is accredited by the Zstd result.

## Prospective hypothesis / predicted observations
Construct two deterministic PCM16 mono RIFF/WAVE source files with exactly 8MiB and 32MiB of PCM data (plus the ordinary 44-byte WAV header), using a bounded pseudorandom walk with seed 24138. Install the exact branch Builder and create archives with `Builder(..., workers=1, reproducible=True)`; do not patch or force its candidate/selector. Predict that both files are admitted as one physical `CODEC_WAVFLAC=2` direct blob with `S_BLOB=0` and unchanged r24 layout. Independent audit must prove exact WAV reconstructed bytes, both indexes, CMA4 SHA+CRC and footer. Source exact native verify A and a one-shot read+SHA+CRC B, alternating ABBA/BAAB, should show 32MiB verify `rchar` / one-shot `rchar` **>1.5** and a wall ratio >1 (directional, not a promotion threshold). If Builder selects Deflate/Zstd rather than FLAC on either file, record genuine admission as a **negative/narrowing**; never rewrite the specimen after seeing the result to force it.

## Strongest controls and alternatives
- Control B is an explicitly **high-RSS oracle**: one full `read_range`, one SHA and one CRC on the identical archive. The original verifier remains unchanged. A one-pass bounded streaming verifier is a *future implementation hypothesis*, not claimed by this control.
- A direct-Zstd synthetic comparison already exists; do not run another one as J24I38.
- Simpler source-level only proof predicts repeated decode but cannot establish Builder adoption, runtime cost or exact physical correctness.
- Different WAV signals/codec competition may narrow representational generality; this test intentionally fixes the signal before measuring, not a threshold search.

## Disproof / decision
If no Builder-authentic `codec 2` files survive exact audit, *this fixture fails to demonstrate production incidence*. If 32MiB physical-read ratio ≤1.5, the proposed work amplification is not supported even if source inspection suggests it. If native/Python disagree on verified bytes, or the independent oracle fails, the scientific result is invalid and must be fixed at the instrument layer without relaxing semantics. A positive result prioritizes a **separately preregistered bounded one-pass WAV/FLAC verifier** under Native Core owner review; it does not authorize promotion or imply ordinary-population prevalence.

## Cost and safety
Record full archive bytes, source bytes, physical encoded bytes, wall, read-character counts (not physical disk sectors), VmHWM and actual source Git SHAs, raw repetitions. Preserve unknown CPU, cold open/list/extract, create wall, true storage I/O, decoder memory traffic, large hostile FLAC frames, concatenated/truncated stream, Windows/macOS and complete release parity as unmeasured. The high-RSS oracle intentionally exports memory; no false product speed credit.

## Concurrency/ownership and continuity
Existing open PRs #765 (native CRC), #759 (symlink + dual SHA), #772 (direct Zstd research) own their surfaces; this PR stays in `research/j24i38/**`, one scoped CI file and new research docs. No mutation to native core, Builder, frozen conformance, historical benchmark or `docs/discovery/STATE.json`. Branch/CI source pins and original artifacts are durable evidence. Repository law and exact measurements outrank this preregistration.

**Decision threshold:** 32MiB >1.5x `rchar` under authenticated source and unchanged native semantics. Any result beneath this threshold narrows the WAV path hypothesis, rather than lowering the criterion.
