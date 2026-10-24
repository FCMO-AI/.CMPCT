# O2 prereg — repair detached inode and symlink-target admission only

**Status:** prospective research-model repair on PR #329 head `cb18d002fa52243f6e19130c312b8e06db1ef05b`; **no CMPCT product or format change**. O1 positive tree court passed hosted Linux UTF-8/ASCII, and its two independent hostile reauthenticated research-model failures passed hosted negative courts at exact head. The original failing reference oracle, negative source files and test outcomes remain untouched.

## Question
Can an **additive** stricter preflight on the O1 detached authenticated manifest reject the eight symlink-target portability counterexamples (four per grammar) and two hardlink-inode xattr contradictions, while still admitting all three positive source cohorts and preserving identical physical output? Specifically, does inode owner-first metadata parity and target-resolved portable component validation suffice for these known gaps?

## Mechanism/prediction
- On `casefold` target, normalize relative symbolic link target components against its link parent without filesystem writes, reject invalid UTF-8, reserved device, trailing dot/space, platform metacharacters. Do NOT treat target spelling as a new filesystem entry or reject it because it references an existing entry.
- On each hardlink alias, validate **mode and xattr key/value rows equal to its canonical earlier regular-file owner's inode-wide metadata**, independently of bytestring path. Preserve ordinary hardlink alias groups.
- Use `preflight` O1 (unchanged) as baseline then additive strict checks, but still perform *all* checks before writes.

## Simple control and falsifier
The simplest control is O1's original `preflight`; it accepts the signed hostile cases. A false fix could overreject all symlinks/hardlinks or silently remove xattrs. Require positive source cohorts to pass with all raw data, modes, xattrs, inode aliases, and symbolic link targets unchanged. The negative cases must reject specifically inside strict preflight. A regression on legitimate relative link targets, a change in size/bytes of the detached packet, or any output write before rejection kills the repair. No portably complete Windows semantics claimed by a toy casefold abstraction.

## Scope, evidence and continuation
Focusing solely on two well-explained semantic gaps; not complete host policy, secure race-resistant descriptor traversal, POSIX full metadata/time, macOS, Windows, native ABI, real CMPCT format, recovery/update or release. Preserve both positive and negative witnesses and report exact hosted commit + artifacts, not a product improvement. Do not modify Discovery policy, thresholds, canonical release, or neighboring PRs.
