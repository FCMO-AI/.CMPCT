# O32 — installed-wheel static destination pivot conformance (prospective)

Date: 2026-10-24 UTC. **Research/evidence-enablement; no release or merge authority.**

## Source/baseline
O27 PR #380 source-exact `34a2059491fcd38bc09231cba178ec8541f74fdb` incorporates a static `lstat` destination-symlink preflight into the signed-generation-bounded Reader. Its unchanged focused original+intersection court was 9/9 on Ubuntu and 9/9 on macOS (run 40131876213). However its inherited `installed-native-package.yml` returned administrative SUCCESS while all actual packaging, CPython and aggregate jobs were SKIPPED (run 40131878742). This is *not* evidence that the guard survives building, installing, and running a distributable wheel. The exact-head official r24 parity run 40131878651 separately FAILED: binary/library/create 89.075 -> 103.632 ms (+16.34%/+14.557ms), on a route untouched by this guard; this result remains an actual red, with causal attribution unestablished.

## Question / hypothesis / prediction
Can a clean-installed revision-24 CMPCT wheel on **both actual Ubuntu and macOS hosts** reject a **pre-existing** destination directory symlink pivot *before publishing any earlier archive member*, then reconstruct the identical authenticated archive safely after removing the pivot, with a regular-file hardlink preserving inode identity? The hypothesis is YES, because O27's static preflight lives in shipped Python Reader code; actual `pip wheel`/sdist packaging should retain it. A successful result must be bound to the exact candidate source SHA, wheel environment, and original archive digest, and independently inspected by the aggregate.

## Stronger/simpler controls and alternatives
- The existing in-repository pytest 9/9 is a weaker proof of distribution behavior because it uses an editable/source install.
- The existing signed-**archive** symlink wheel court is NOT a pre-existing **destination** symlink pivot test.
- Rerun existing wheel suite without new assertion: cannot decide the question.
- Rebuild the whole product architecture: needless and conflicts with #381/#385 owning hardlink/Reader changes.
- Chosen: one small standalone wheel-origin hostile+positive test executed by existing Linux/macOS wheel builds, plus fail-closed receipt checks in the aggregate. Windows symlink creation rights and reparse-point semantics are *not* inferred from POSIX.

## Before-result disproof, admission and cost
DISPROOF: wrong module location (editable/source import), mismatch of exact HEAD or corrupted source fixture, absent hostile refusal, any early ordinary file, changed external sentinel SHA/inode, inability to reconstruct same bytes and physical hardlink after removing the pivot, negative missing from a host receipt, aggregate certifying a missing/duplicate/wrong-platform receipt, or skipped deep installed matrix. Any of these forbids product credit.

Expected CPU/I/O: two independent installed-wheel Builder operations and extract attempts; existing installed-native-package suite runs 3-OS build and 15 CPython jobs if explicitly activated. The test adds no runtime code, wire format, or archive bytes to the CMPCT product. Known limitations: static `lstat` is raceable, external preexisting regular hardlink aliases remain unsafe, Windows namespace/junctions untested, source lifetime not frozen, whole-tree publication not atomic. Preserve exact official comparator/threshold and the O27 red.

## Decision unlocked
If the exact-source installed POSIX wheel court and aggregate pass, close *only* the packaging-evidence gap for the O27 static guard. Do not promote/release until full canonical Reader composition and performance are reconciled. If packaging fails, identify and isolate cause without altering evaluator, expected failures or owner code.
