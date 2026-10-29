# J24I30b — Separate native optional-SHA admission from symlink verification (prospective amendment)

**Addendum committed before changing J24I30 Rust court or running the new independent referee.** Do not rewrite J24I30's original preregistration or classify its first hosted red as a product pass.

## Observation forcing a sharper model

Initial J24I30 installed-source hosted [Actions #40860613366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40860613366), exact commit `e015b83a5f37df8f158afaae516b041987181e09`: Ubuntu compiled the original native Rust court successfully and installed Python generated all five authentic revision-24 symlink variants; Python accepted the historical empty-row-SHA `b''` sentinel, while native `Archive::open` rejected that particular reauthenticated variant with `invalid index schema: file row 0 has invalid logical SHA-256 length`. The original whole five-case Rust scientific test **FAILED** at `present-empty`; the remaining cases were not executed by that native test. macOS of the initial workflow was cancelled by a concurrent follow-up push. The actual negative is a **native/Python parser admission difference**, not evidence yet of native acceptance of a bad payload.

## Distinct questions, prospective outcomes

1. **Admission case / already observed:** Native `parse_hash` refuses `b''` while installed Python preflight and `CMPCT.verify()` accept `b''` on the exact re-signed archive. Future test MUST preserve and assert the observed native refusal explicitly, rather than quietly dropping the case, silently skipping, or loosening native parser policy.
2. **Symlink verification case / not yet observed:** For the parse-admissible `None`, correct 32-byte SHA, contradictory 32-byte SHA and physically corrupted payload variants, expect native `verify_complete()` to return `Ok(0)` without validating the symlink payload. Python strong verification rejects the latter two. A native rejection of any parse-admissible bad specimen falsifies or narrows this second hypothesis.
3. **Independent physical referee:** A standalone Python tool, importing neither CMPCT nor the Rust implementation, must independently decode primary/tail committed indexes, verify record CRC32/SHA256, and affirm exactly one physical mutation plus a logically inconsistent-but-physically-untouched signed-index variant. This distinguishes instrumental corruption from product behavior.

## Strong controls and kill conditions

Keep original single-symlink actual Builder archive as a required native+Python accepted control. Preserve the existing source-locked Rust/native blobs, original test failure and Python observations. Source SHA in hosted CI must equal the exact head, and source blobs must still match the preregistered parents. Do not merge a binary whose strong-verify contract is unreviewed, and do not change native parser or any frozen evaluator under this research lane.

If native rejects `present-foreign` or `physical-wrong` for an actual integrity reason, the second H1 is false; report precisely. If independent referee shows that index framing or record identity changed unexpectedly, the specimen is invalid and no negative is claimed. Any missing hosted job or missing artifact means evidence pending. Even if second H1 holds, it is evidence of a *coverage limitation*, not a signed-archive forgery or certified exploit.

## Ownership and product economics

This work is a research-only supplemental test to #750. #751 independently investigates hardlink alias logical SHA and is not changed. Native core/product source, format revision, official performance measurements and release gates stay untouched. A future fix belongs to native/core portability owners and must separately preserve legacy `None`/empty compat, bound verify resources and prove its own product CPU/RSS costs. Discovery STATE is already stale and owned by #574; no state mutation.
