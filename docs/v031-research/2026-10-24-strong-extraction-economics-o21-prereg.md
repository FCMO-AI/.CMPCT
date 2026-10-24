# O21 preregistration — price ordinary versus strong whole-archive extraction

Date: 2026-10-24
Status: FROZEN BEFORE INSTRUMENT AND OUTCOME
Source owner: PR #258, exact base `2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`.
Scientific lane only; not the owner of Reader, Writer, extractall, or release.

## Decision question
After O20 (#370) demonstrated that ordinary `extractall()` may publish CRC-repaired physical mutations rejected by the corrected `verify()`, what *actual installed-product wall, CPU and peak RSS cost* does the simplest stronger explicit policy—`verify(); extractall()` on one Reader handle—impose relative to ordinary extraction of exactly the same intact source? This controls whether a more complex fused verified extractor is plausibly worth creating, but cannot establish such an extractor's security.

## Baseline and competing actions
A: ordinary `CMPCT(path).extractall(dest, metadata=False)`.
B: `CMPCT(path).verify()` followed by `extractall(dest, metadata=False)` on the SAME open handle.
C: `verify()` alone, diagnostic timing for separating first-pass work.
The Reader already caches some decoded blobs; B must not be modeled as two independent processes or an always-cold second pass. Conversely the hot filesystem page cache and Python startup must not be hidden.

## Predicted causal result and alternative
Hypothesis: B pays a material CPU/wall premium on intact content, most clearly for many members sharing physical PACK storage; a same-handle cache may reduce second-pass work and export resident memory. Stronger alternative: verification is cheap enough versus filesystem publication that B is a practical opt-in policy until native/transactional semantics mature. Null: no reproducible material premium above same-runner noise. The new evidence is relevant to product design only if source identity and extracted trees match *exactly* and the cases actually exercise both S_PACK and RAW storage.

## Falsifiers and controls
- Build two deterministic actual CMPCT r24 corpora from one source each: >=128 small structured files with a real `S_PACK` physical owner, and >=2 MiB pseudorandom direct RAW payload. Fail rather than silently reclassifying storage; assert archive SHA/bytes, S_PACK membership and physical codec, source tree SHA and full extracted tree SHA.
- For each corpus, run separate fresh child processes for A and B in balanced ABBA and BAAB order, >=5 blocks total. Preserve *every* wall/CPU/high-water RSS observation, open/verify/extract phase boundaries, source SHA, content manifest, Python/package provenance and the host/platform.
- Same package/source/runner, fresh destination per child, no compiler/build time charged to either arm; warm page cache is allowed but named. Record source size, archive size, output logical bytes, number of entries and at least one physical owner.
- A and B have DIFFERENT integrity semantics; faster A is not a strict same-semantics win. O20's negative physical mutation is an independent prior control, not an excuse to benchmark corrupt bytes or remove verification. B is not a guarantee against mid-operation source or destination mutation.
- Report measured median B/A wall and CPU and peak RSS, paired-delta spread, effects by storage representation; if noise dominates mark AMBIGUOUS, not WIN.
- If B adds small cost without adverse RSS, prefer bounded simple strong mode (subject to source consistency and publication design); if costly on PACK, investigate one-pass physical-owner authentication before implementing; if the difference is unstable, raise measurement quality.
- Strong SHA from the archive is an internal consistency check, not external signer provenance; no release credit.
- Do not change `src/`, tests, frozen benchmark criteria, comparators, thresholds, package/version/format, canonical branch or discovery STATE.

## Claim ceiling
This is an integrity-cost *product-runtime diagnostic* on intact synthetic corpora, not a shipping stronger `extractall`, not tamper-resistant source snapshot, not a format improvement, and not a release ABBA comparison. Any implementation decision requires hostile source/destination cases, complete IO and platform tests, and project release gates.

## Counterfactual
If only a handful of cheap observations distinguish the two economic routes, do not initiate another independently maintained extractor before reading them. Record false positives and all negative outcomes.
