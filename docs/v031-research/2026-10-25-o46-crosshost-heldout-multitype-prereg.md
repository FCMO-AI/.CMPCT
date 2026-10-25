# O46 — held-out cross-host reproducible-mode topology falsifier

Date: 2026-10-25 UTC
Status: preregistered before implementing or executing the held-out instrument.

## Exact authority / ownership
This is an independent **scientific follow-up**, stacked on the current O14 owner PR #372 source `a8429ac195b1f1426b24eec3d5bd5ee0ab486c68`. Released v0.30.0 / revision 24 and all frozen performance, size, identity, release and native contracts remain unchanged. O14's source-exact three-host result (run 40119076117) supports mode-only normalization for **two regular files + one directory**; it explicitly does not generalize to other file kinds. O42 #396 handles release corpus semantic identity; O44 #398 handles *research-corpus materialization* hardlink topology, not the actual Builder's cross-host reproducibility. O45 #399 owns sparse admission. Do not edit their branches or broad metadata semantics.

## Primary question / prediction
Does O14's `K_FILE/K_DIR` row-mode-only intervention suffice for byte-identical *complete* reproducible CMPCT archives from an independently constructed, held-out tree with an executable member, empty regular member, nested/empty directories, a real physical hardlink alias, and an independent equal-byte copy? Cross-host Ubuntu/macOS/Windows, with two fresh builds per mode, original installed Builder, exact source tree, and installed Reader strong verify/read/extract.

Preregistered branches of the decision:
- **H1_TRANSFER:** baseline archives differ, but O14 file+directory mode-only complete archive SHA, physical SHA and index ignoring modes agree across all three hosts; the hardlink relation and independent same-byte file survive, with no other semantic alteration.
- **H2_MISSING_MODE_KIND:** O14 mode-only differs, but independently applying fixed modes to all file-kind rows including `K_HARDLINK` makes complete archives equal while physical bytes / non-mode index remain equal within each host.
- **H3_NONMODE_OWNER:** even expanded all-kind mode normalization differs in complete bytes, or physical blob/index semantics differ, notwithstanding identical source logical bytes.
- **INDETERMINATE:** source logical bytes/physical-hardlink relation differ across hosts, installed environment does not permit hardlinks, base cannot pass strong verify, or any source/codec/checksum custody invariant fails. This is a real blocker, never a favorable result.

The strong simpler control is the original O14 mode-only oracle, which must not be silently strengthened after observing results. The expanded alternative is a separate, preregistered *research-only* arm. Never interpret a changed mode policy as the same filesystem semantics or shipping improvement.

## Method and cheap rung
Use `Builder(src, reproducible=True, reproducible_epoch_ns=0, workers=1)` and O14's ModeOnlyOracle. Construct a small synthetic root (payload <= 512 KiB) using `os.link` to force one hardlink equivalence class and a deliberately independent same-byte copy. Add a second research-only all-kind-mode oracle that differs *only* in serialized mode fields. Build twice per arm per host; source SHA, list/read/strong verify/extract, expected hardlink vs copy identity, raw archive SHA, physical-region SHA, non-mode index digest and per-kind modes are required. A cross-host referee checks every host receipt and emits an explicit evidence-only verdict; workflow success does not imply H1. Preserve raw host receipts and referee.

## Kill / negative / economics
Any non-mode mutation between original and either oracle within a host, differing physical region between arms, loss of SHA/read/extract, hardlink mistaken for same-byte copy, unsound independent identity comparison, false green from a skipped host/referee job or source-HEAD mismatch invalidates admission. Exported cost: 3 hosts x 6 small archive builds, package installation, full verify/extract and a referee; no timed product speed, compression win, or release claim. Retire the mode-only-generalization assertion if H2/H3 appears; avoid variants/threshold gardening.

## Concurrency, policy, handoff
O14 #372 remains owner of its original experiment; this explicitly preregistered child is an independent structural-transfer falsifier. Do not modify O14 instrument, benchmark generator, source tree, docs/discovery/STATE.json, release law or comparator. Report source SHA, raw artifacts, actual host executions and exact negative evidence before proposing any change to product mode policy.
