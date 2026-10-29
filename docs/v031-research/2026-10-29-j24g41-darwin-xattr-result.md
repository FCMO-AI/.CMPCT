# J24G41 — Darwin-native xattr composition: first physical product result

**Research status 2026-10-29, 11:31 UTC:** candidate-positive on three-host *specialized* court; NOT merged, NOT released, NOT a general filesystem-fidelity guarantee.

## Source identity and preregistration
- Parent: O72 #428 exact `48b4a90487d5df6c1fe06896933689e7a8369f6d`, preserving O65 Builder and O69 Reader controls.
- Preregistration: `ce14be9a0727bea3032d09dd716c54a16c4cbc96`, before candidate source changes.
- Product-bearing source HEAD for these observations: `d2f7c2360968d9c0c3606796fa1c561fded9d0ba`. **Any later documentation commit must not relabel an earlier job as an exact-head run of the later commit.**
- PR: [#757](https://github.com/FCMO-AI/.CMPCT/pull/757). Defect: [#753](https://github.com/FCMO-AI/.CMPCT/issues/753). Independent negative: #752/J24G40.
- Published `main` remains v0.30.0, r24. No version/format change, no merge or release.

## Primary question and decision
A real Darwin xattr is visible to native OS tools but missing from the CPython `os` interface. Does a native syscall provider permit the exact O65 fail-closed Builder and O69 strict Reader to encode/restore those bytes through an authentic r24 file, rather than merely simulate a monkeypatched `os` API?

**Yes for the physical fixture studied.** On macOS 14 arm64, a separate `/usr/bin/xattr -wx` created binary xattr bytes `J24G41 native xattr\\x00\\xff\\x01`, independently read back via `/usr/bin/xattr -px`; installed Builder captured name+value in authenticated fsmeta; installed Reader `verify()==1`; strict `extractall(require_xattrs=True)` restored a native destination key whose independent value matched. Source logical SHA preserved. Native `XATTR_NOFOLLOW` symlink test also passed.

### Positive exact-source evidence
[Actions run #40865721624](https://github.com/FCMO-AI/.CMPCT/actions/runs/40865721624) on `d2f7c236...`:
- macOS 14: **SUCCESS, 20 passed / 2 skipped**, native source-and-destination xattr test **executed, not skipped**; JUnit audit `ADMITTED`; artifact **#12892434934**, provider artifact ZIP SHA-256 `b78387a391bbb1ef6942568244bb89035bc95d536d791173ac3bfa550635af53`.
- Ubuntu 24.04: **SUCCESS, 20 passed / 1 skipped**, genuine kernel-backed Linux xattr roundtrip executed; JUnit audit `ADMITTED`; artifact **#12893063135**, provider ZIP SHA-256 `e98327bb07e713e7f9fa3b2dfea2cf2f254db839604e8d019dc5f57cde22d617`.
- Windows 2022: **SUCCESS, 18 passed / 4 skipped**, unsupported-OS fallback and injected O65/O72 controls accepted; JUnit audit `ADMITTED`; artifact **#12893781282**, provider ZIP SHA-256 `5f270b396781dd8b1cc0e6cb7542fffec622be195dea42f0981bfde36374b799`.

These are SHA-256 values **reported by GitHub Actions artifact upload**, not separately downloaded and rehashed ZIPs. The suite copies the untouched owner tests to an isolated directory and fails closed if required native positives are absent; xattr fixture is real, not solely mocks. No claim of 3 independent large workloads: single tiny synthetic member on each POSIX host.

### Preserved negatives and contradictions
1. First specialized run [#40865438847](https://github.com/FCMO-AI/.CMPCT/actions/runs/40865438847) had macOS and Linux SUCCESS but Windows **FAILURE** before tests: Git binary blobs were LF while Windows installed source came from checked-out CRLF materialization. The workflow was changed to require a clean Git checkout and exact installed-to-checkout bytes; latest 3/3 passed without loosening product tests. This is a custody-infrastructure correction, not a product change.
2. Inherited [O69 workflow #40865721693](https://github.com/FCMO-AI/.CMPCT/actions/runs/40865721693) is **Windows PASS, Linux PASS, macOS FAIL (1 test)**. Its unchanged test simulates `delattr(os, 'setxattr')` and expects strict extraction to reject a missing Python interface. **But the new Darwin *native* provider is available even when the Python module lacks this attribute.** The old test now asserts a pre-provider condition inconsistent with new native capabilities. This is a genuine historical evaluator conflict; do **not** mark historical workflow green or weaken its test silently. Owners should version the test semantics to distinguish deliberate provider unavailability from CPython API absence.
3. Inherited [O72 workflow #40865721512](https://github.com/FCMO-AI/.CMPCT/actions/runs/40865721512) **FAILS all three hosts at exact historical Git blob gate**, because it fixes original Builder/Reader identities. Its tests are executed **unchanged** by J24G41 court with positive results; that does not make the old gate green.
4. Engineering Evidence #40865721602 failed due to missing required **level-two** PR body headings. PR #757 body has been repaired to use exactly the required headings and falsifiability markers; a **fresh event/HEAD run is required** to establish green. No evaluator was changed.
5. Full General Tests at this exact head were pending on last evidence read; administrative r24 parity workflow success does not mean measured performance. Full zero-byte archive parity, macOS unusual/protected attributes, 4MiB names /64MiB values, CPU/wall/RSS/temp-I/O, source mutation races, Windows ADS, ACLs, same-UID compaction publication (#749) and power-failure durability remain unproven.

## Scientific scope and counterfactual
- Earlier strong control: a native kernel-backed positive would have disproved the hypothesis that the *filesystem* simply lacked the attribute and should be a mandatory setup gate on macOS.
- Product improvement is provisional but material: a real macOS xattr previously omitted silently can now cross Builder→authenticated r24→Reader strict extraction.
- No independent interpreter of all r24 wire bytes was run in this activation; `CMPCT.verify` is common-mode to some claims. The native `xattr(1)` readback establishes an independent OS endpoint but not a full independent CMPCT format decoder.
- The inherited O69 negative requires an explicit **semantic contract** decision by the owner; preserve that test and distinguish unsupported host from unsupported Python wrapper. Do not tune to a stale simulated assumption.
- No Discovery Engine policy changes earned. Do not modify shared `docs/discovery/STATE.json` based on this one bounded success.

## Next gates
1. Run next HEAD specialized and Engineering Evidence, reconcile provider artifacts and source exactness.
2. Coordinate with #428 O72 and #420 O65 owners on native provider awareness, historically failed #O69 API absence test, and strict source/destination semantics; add a stronger independent macOS metadata readback set (empty and non-ASCII, symlink, binary).
3. Run full unchanged general/native/fuzz CI and 0-byte same-input archive parity / timing gates; inspect protected Darwin attrs and failure-path resource bounds.
4. Only then discuss merge/release. Release credit: **zero**.
