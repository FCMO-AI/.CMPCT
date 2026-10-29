# J24M01d — captured failing archive × fresh-child import provenance (2026-10-29 UTC)

**PRE-RESULT PREREGISTRATION.** Research only; no release or source/format/threshold modifications.

## Authority, exact sources, and historical negative
CMPCT main is v0.30.0/r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. Compaction integration owner is PR #738 `ec112a87ea34349b63885f3f0bea4689f192bd2f`; science owner PR #766 at `e1e5edf16d5ab1d7de78de66412e2ac26fb4c630`. Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`, Builder `387192edd783e02bf7a44a38945214bf9d6c183e`, inherited original test `dc31bd4a46c117e6621a76a91b7bdeef85579ebf`.

The unchanged general suite #40890827519 failed with 795 passed, 5 failed. Its fresh child running `CMPCT.verify()` reported **180,344 KiB** (threshold **131,072 KiB**). It captured its actual 1,160-byte revision-24 archive, SHA-256 `852a2e554cf2f984d9294858567168d6a39fe91ceb4ed16b83333158401a76f3`, logical SHA-256 `50c7a6d6fe5cdff870a4c4041bf456719fef36f62bf693570cf128b6ff74a90e`, 256 MiB logical file, **two 4,096-byte physical extents**, sparse storage tag 3. Provider artifact #12903943709, ZIP SHA-256 `b9e75b08c1dc0b691ae67f58552940443990417e2a38706bcc63e0d66562f104`; its original bytes have been independently downloaded and SHA-verified.

Prior 54 isolated controlled children in #766 showed 23,816–24,140 KiB, but were on different physical archive bytes. Different archive geometry is now disfavored by the captured full-suite archive; its encoded extent burden is just 8,192 bytes. The full-suite failing child import provenance and process state are still unknown.

## One primary question
Does the **exact captured full-suite input** produce high RSS in a new source-authenticated process outside suite order? And, when the original full-suite order is re-run, does the original failing child's inherited environment select a different Reader or context than a fresh control?

## Prospective controls
1. Freeze the original captured 1,160-byte CMPCT archive as base64 with its **prior SHA**, not a regenerated fixture. Read via a second independent parser/standard-library auditor before interpreting stage results.
2. Run the *unchanged test child script* on the exact archive in an isolated new process. Independently repeat with a staged variant that logs kernel ru_maxrss at before-import, after-import, after-open, after-verify; imported `cmpct.reader.__file__`, its git-blob SHA1, environment search-path fingerprint, logical SHA/geometry, verification count, and CPU/wall. Count instrument overhead separately.
3. For full-suite context, use an opt-in pytest plugin that passes the original test child `subprocess.run` **unchanged** and records its original output. Run a **separate follow-up probe** under the same inherited environment and exact archived bytes *after* original completion, never claiming that the follow-up proves the terminated child's original imported module. Keep plugin-probe results separate from uninstrumented #40890827519. Keep original failures as failures.
4. Preserve exact stdout/stderr, raw process peak and provenance, input SHA, original inherited ceiling, provider run/artifact identity. Ubuntu/Python 3.11 only; no cross-platform/global claims.

## Predictions / kill and narrow
- If captured archive under isolated original child consistently stays <128 MiB, **physical input difference is falsified as the sufficient cause** for that host; identify inherited environment/import or suite-specific process history as next fork. This does **not** retire the historical full-suite failure.
- If the exact captured file itself triggers >128 MiB fresh-child RSS, prioritize Reader/codec/physical-content mechanism, inspect imported Reader blob before changes.
- If full-suite original child remains high but a same-environment follow-up child is low, the cause may depend on interleaving or child import. Do not claim parent contamination or an import mismatch without direct evidence.
- If instrument changes original outcome materially, classify **instrument perturbation**; preserve baseline and run smaller controls before any attribution.

The strongest simpler control is the **same physical archive under original unmodified verification script**, rather than repeating invented 256 MiB sparse streams. No evaluator weakening, no threshold modification, no Reader/Builder/format/API change, no product win credited. No general Discovery Engine policy update from one episode; use PR #766/#738 handoff and keep shared `docs/discovery/STATE.json` untouched.

## Decision unlocked
Correctly distinguish fixture, code provenance, environment and suite sequencing as possible owners of the 180-MiB RSS spike. If no decisive distinction emerges in this bounded final attempt, retire this narrow repeated family as nonblocking research debt and focus on #749 safe publication / existing product convergence.