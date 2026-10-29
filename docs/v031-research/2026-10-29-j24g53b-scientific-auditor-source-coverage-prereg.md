# J24G53b — candidate-fingerprint scientific-referee coverage falsifier (prospective correction)

Date: 2026-10-29 UTC
Status: preregistration committed after J24G53 exact-donor transplant `a59442604e72c4b533909fc3d6ce64a788313269` and BEFORE modifying fingerprint manifest or tests. New knowledge must not rewrite the earlier J24G53 prediction.

## New independent observable / source

An exact GitHub tree census of the J24G53 source found 2,371 tracked blobs; a separate Python-glob-compatible matcher against #266's source manifest found 2,318 covered and 53 excluded. Among exclusions are **nine executable `research/**/*.py` files**, including `research/j24g50/independent_audit.py` and `research/j24g44/detached_zero_encoded_wire_audit.py`, which the inherited J24G50 three-host physical court actually executes. Thus an auditor can change while `tools/check_v031_candidate_fingerprint.py` computes the same candidate fingerprint, because its glob list never visits that path. This is a source-custody blind spot, not evidence of falsified results or a product codec bug.

Control: `src/**/*.py`, `tools/**/*.py`, `tests/**/*.py`, `docs/**/*.md`, and `.github/workflows/*.yml` are included and remain unchanged. The original exact donor code/manifest state is preserved in the preceding Git commit. The census itself does not prove an observed malicious substitution.

## Prediction / smallest fix

Add one prospective glob `research/**/*.py` and require the three exact referee paths used by installed #778 J24G50 / #773 J24G47 / #767 J24G44 courts. Add independently targeted test verifying (1) these real scientific referee paths appear among fingerprint rows, (2) all currently checked-out research Python files are covered, (3) a mutated synthetic research referee changes the fingerprint, and (4) removing a required referee fails closed. The original #266 files other than manifest remain byte-identical to donor.

An even simpler alternative is to leave scientific referees outside candidate *product* identity and bind them only by exact SHA in their own workflow. However the current claim and manifest explicitly advertise a **complete prospective source identity** consumed by tests/CI, and these referees can change the decision on the same physical archive. A 1-glob extension with ordinary tests is smaller than an additional specialized CI database and costs negligible hash work relative to a full test suite (measure actual hosted wall if material).

## Kill / narrow

- If the control `fingerprint_globs` already includes the referee paths, the premise is false: do nothing.
- If adding the globs breaks the accepted inherited product-source corpus or causes unbounded dynamic/generated file traversal, narrow the glob or retire this fix; do not ignore the red.
- If the mutation, removal or untracked-symlink controls can evade fingerprint identity, fix the source-identity instrument prospectively without weakening tests or historical release authority.
- Do not treat source-fingerprint coverage as physical archive authenticity, native product correctness, benchmark/release proof or same-UID publication safety.
- Do not include mutable research episode history by default: only executable Python scientific referee source is part of the incremental candidate source identity.

## Evidence tier and applicability

The original tree-glob mismatch is a static source-bound derivation; a source-identical fingerprint trial and exact-head all-PR CI are needed to validate implementation. Do not mislabel the prior #266 standalone green as applying to this enhanced manifest. If complete full-suite and mutation controls pass, transfer this discovered gap to #266 for owner adoption; the downstream composition remains unmerged and unreleased.
