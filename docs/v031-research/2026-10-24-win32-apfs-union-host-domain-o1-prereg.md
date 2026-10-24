# O1 — host-domain separation for joint Win32 and APFS regression evidence

Date: 2026-10-24 UTC. Status: prospective correction to O0's overly broad cross-host applicability assumption; O0 and its negative CI remain immutable.

## Observed O0 contradiction and falsifier

Exactly integrated source `e239972f880f6906ec016e814fba2bc1c9add5e0` ran one unchanged Windows-owner test on *all three hosts*. Exact-head union workflow run `40076842895` reported Ubuntu and Windows **SUCCESS** but macOS **FAILURE**: `test_real_posix_extractor_keeps_legal_windows_incompatible_names`. The original Windows-owner positive test creates both `Case` and `case` on non-Windows POSIX. Original APFS-owner policy explicitly rejects that pair conservatively, even on case-sensitive macOS volumes. Running the Windows-only owner suite verbatim on default case-insensitive APFS therefore poses logically contradictory expected outputs; it does **not** falsify either security guard. Keep the original test source, its failure log and original O0 prereg unchanged.

## New narrower scientific question

Can all original owner assertions be preserved on the **host domain that motivated them**, while the rest of both original test suites and a joint invariant control still run on the one composite HEAD, without weakening any actual platform security check?

Preregistered resolution:
- Shared lexical + dual policy helper tests + original APFS suite run on Ubuntu, Windows and macOS, with their own platform skip markers visible.
- Full original Windows suite runs, unchanged, on Ubuntu and Windows (exact same source hosts as its PR #332 control).
- On macOS, run *every* original Windows suite test **except** `test_real_posix_extractor_keeps_legal_windows_incompatible_names`; explain the excluded test by its impossible `Case`/`case` assertion on default APFS in workflow output. Never edit test source, weaken a guard, or hide the explicit exclusion.
- The full original APFS O1/O2 tests must still execute on genuine Mac, and full Win32 extraction/collision/drive tests on genuine Windows.
- All jobs must use exact Git HEAD and real installed CMPCT; report separately host-executed tests and platform skips.

## Kill conditions / alternative explanation

If any platform-relevant original invariant fails, retain the red. If the Mac-specific original controls disappear from the Mac execution, or Win32 native originals disappear from Windows execution, reject this new evidence route. If `Case`/`case` is actually distinct on a specific Mac host, the O0 broad run could have been valid there; here the default APFS normalization probe and Mac owner test establish the expected alias semantics. Do not reinterpret the exclusion as universal POSIX safety or a new CMPCT product improvement.

The alternative of editing `test_v031_windows_member_namespace.py` to skip macOS globally is rejected because that would mutate a frozen owner test. The alternative of dropping the Windows module entirely on Mac wastes legitimate host-neutral derived checks. Explicit runner-level test-domain partitioning is both cheaper and more scientifically honest.
