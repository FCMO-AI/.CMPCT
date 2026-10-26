# O180 preregistration — J24W01 Win32 symlink restoration cross-host falsifier

Date: 2026-10-26 UTC. Status: PREDICTION, not a result.

## Authority / source identity
CMPCT shipping v0.30.0, on-disk revision 24, prospective v0.31. Scientific continuation of O171 #508 and O176 #511, not a product change. Exact stacked base O176 `4e943dc7de00ab56cc33d08ae9061a80573444e0`. Source donor J24W01 #507 `7436bb34e5019639b8e00541b437b5153dee7462`, Reader blob `88b6706ba748306b6a4a13274fff2220eec0c32a`. Positive comparator O167 #504 `841c32d435494f6e4d83c44cd00a1a2f8f7ab148`, Reader `c50522443b88e78ee2cc8361c4ec2bddbb4f0bbb`. Original O171 court blob `8c943128f135607dd36abd083bf1019bc9e4433a`.

## Causal hypothesis and alternative
O167 catches `(OSError, NotImplementedError)` when applying symlink `os.utime(..., follow_symlinks=False)`. J24W01 reuses the O167 helper for **regular files/dirs** but retains `except OSError: pass` for **symlinks** (`reader.py` lines ~455-458), therefore the same authentic Linux-created r24 tree archive should verify but fail extraction on Windows with `NotImplementedError` on a symlink. Strong alternative: a prior step or platform behavior now suppresses that exception, so J24W01 succeeds and the static prediction is false. A third outcome (source drift, unavailable symlink permission, wrong input, different failure) is inconclusive, not confirmation.

## Cheapest decisive native test
Reuse the **unchanged** O165/Linux producer and original O171/Windows physical-fidelity court from #511. On **one Windows runner, same transferred binary**, independently install three exact sources, each in a separate process with source identity checks: O171-derived historical Reader expected to fail in the original way; O167 expected to pass the full original O171 topology court; J24W01 #507 is the source under test. Archive sha/size and installed wheel reader/helper Git bytes must be attested before/after all three. Run the original O171 court unchanged, retaining JSON, stdout/stderr and exit status on both positive and negative. **Do not** adjust `metadata`, weaken physical link checks, or catch exceptions in the product to make the court pass.

**Prediction:** historical negative reproduced, O167 full court passes, J24W01 verify passes but extract fails with the original `NotImplementedError: utime: follow_symlinks unavailable on this platform`. **Disproof:** J24W01 passes the unchanged original O171 court with source-exact identity and same binary; record the hypothesis as falsified. Any other red is a distinct or inconclusive failure that must remain visible. A nonrepresentable native link or absent artifact invalidates the claim.

## PARETOBONK
Versus another handler, a static line comment, or generic CI, one same-archive triple-source native experiment best separates data transport, host capabilities, a previously positive comparator, and a real integration regression. No third product fix; if red, hand this discriminating evidence to #507/#504 owners for consolidation. No source/format/release/frozen benchmark mutation, and no performance, recovery, race-safety, ACL, xattr or universal Win32 claim.

## Promotion boundary and next action
A result-bearing native Win32 run can decide this narrow regression and guide owner convergence. It cannot approve v0.31 or replace official same-input r24/ZIP performance, generic exact-head CI, upstream PR owner review, broader path/metadata threats, or genuine filesystem fidelity on other Windows hosts. Preserve raw negatives and source fingerprints; no `STATE.json` mutation while another owner reconciles it.
