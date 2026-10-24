# O1 preregistration — authenticated hardlink alias as an impossible ancestor

2026-10-24 UTC. **Freeze before adding O1 test.** Parent PR #338 currently fixes signed regular ancestors at `e929f3ec65fe88fc8d20b0e26b4b28e13e64b88d`; original source-negative run 40078750750, positive exact-head run 40078888706, original immutable regular-ancestor test untouched.

## Distinct unresolved question
The fail-before-write trie handles `K_HARDLINK` as a non-directory parent by source inspection, but signed authentic archive behavior has not been tested. Can a newly added hardlink row `alias.bin -> parent.bin` and valid physical child renamed `alias.bin/child.bin` be individually read while the aggregate tree is impossible, and will the prewrite fix refuse it before creating either owner or hardlink? This is a structural **held-out mechanism perturbation**, not parameter gardening on the original file-prefix case.

## Controls, prediction, kill
Create a real r24 archive with Builder, keep its physical blobs unchanged, reauthenticate both compressed indexes after adding a spec-shaped `K_HARDLINK` row and renaming another file beneath it. Reader must return exact bytes for owner, alias and child. This tests semantic admission, not arbitrary data corruption. On fixed source, expect `IOError('non-directory archive ancestor ...')` before member writes; on parent/source without guard, expected partial owner and/or alias. A legitimate exact hardlink sharing an inode with the owner must still work, and the original four file/implicit-dir controls stay immutable. Any false acceptance, partially written destination, or valid-hardlink regression disproves the implementation's claimed generality. Independently confirm host is capable of hardlink extraction.

## Alternatives and cost
A symlink-root test is weaker because prior safe-symlink preflight already covers it; a file-prefix retest is redundant. Stronger alternative is a shared Reader/preflight tree validator, but that is additional ownership and requires a separate structural court. No archive version, format or benchmark change; no full system economics claimed. Preserve this prediction separately from any observed results.
