# A16-O0 — Sharing-class run coalescence, preregistration

Date: 2026-10-28 UTC
Status: FROZEN PREDICTION BEFORE EXPERIMENT IMPLEMENTATION. Scientific component-only; not a new CMPCT on-disk format, release, product improvement, or claim of an existing component.
Source of prior negative: A15-O1 PR #680 (`a02034ed3c23f84d0827d1cbb448423c9e1e6bec`) on fixed 4-KiB content-addressed blocks and A15 direct member frames. Published baseline: `main@80c358f8824ec1b20d349c92ed94c898090969b0`.

## Changed information frame

A15-O1 exposed a size/read-work tradeoff: globally shared **4-KiB owners** save bytes but need 16 decompressions for each 64-KiB member, approximately 2.76–2.98x the in-process time of one direct member frame. Rather than add bytecode syntax to A15, test whether *physical owner boundaries themselves* can be discovered from the overlap graph. Group maximal consecutive runs of blocks with the same boolean **globally shared (multiplicity >=2) versus unique** classification per member. Deduplicate the resulting segment by SHA **and exact byte equality**, not source filename, position, seed, expected regime, or fixture identity. This is a new bounded research oracle and is not claimed to be novel across archival systems.

An exactly reconstructing self-describing SEGREF envelope stores Zstd-19 frames, per-owner SHA-256, per-member SHA-256 and size, explicit offsets/lengths and per-member references. No preknown facts are gifted to the decoder. A strong direct (one zstd-19 frame per member, same SHA semantics) and a strong exact 4-KiB CHUNKREF control are measured under the same source members, compression level and same member-selective read semantics. Count *complete* bytes including all metadata, owner lists, reference counts and type/selector overhead. A portfolio control chooses the smallest of the two existing envelopes and pays the selector byte; the candidate portfolio may also choose SEGREF with the selector and includes the cost of attempting all arms during creation.

## Prospective question / criterion

Can run coalescence reduce **both** complete bytes and in-process verified member-read CPU/wall on an independently generated partial-sharing family versus the stronger existing CHUNKREF control, without causing any byte or CPU regression on unrelated blocks after the explicit fallback is charged?

Primary positive criterion: on two independent seeds of 32 x 64-KiB high-entropy members with 12 of 16 shared 4-KiB units, SEGREF complete bytes at least 1.0% below CHUNKREF and >=1.5x faster on median *full-member* verified decode CPU and wall. If size improvement is <1.0%, decode <1.5x or the source/semantics are mismatched: do NOT claim the joint win. Secondary regimes: all-identical and all-distinct; verify no >1.0% complete-byte blowup after portfolio fallback on distinct. Do not claim Q1 selective-byte range, RSS, creation improvement, format compatibility, overall product, or release authority.

A **different structural perturbation** uses shared suffix instead of prefix and a broken/alternating shared pattern; run the same mechanism with no thresholds/logic changes and report both gains and failures. This establishes whether the mechanism is general beyond one tidy prefix. No post-result threshold gardening.

## Stronger alternative explanation and adversarial controls

The observed win might simply follow fewer Zstd invocations, not a universal IR; report actual decode units, decoded bytes, and frame counts, and compare to direct member frames (usually faster but bigger when content is shared). Any positive must not be credited to an A15 opcode or to avoiding per-owner SHA. Run length may reduce owner count but harm dedup when grouping rows with incompatible neighborhood boundaries: detect exact owner counts and ensure the portfolio never silently omits the strongest direct/CHUNKREF arms. Include malformed reference, truncation, SHA corruption, size inconsistency, and trailing bytes; independent decoder must not import producer; full SHA binding of original member bytes is non-negotiable.

## Cheapest decisive execution and stop/kill

First count valid bytes and decode units (cheap bound); then run one local independent-parsed fully charged court and verify raw repeated in-process decode CPU/wall against fixed source material. A full installed Reader/hosted product benchmark only follows if this lower rung changes the decision. Kill or park this narrow family if the wins fail on both partial and held-out structural perturbation, or if exact product eligibility/portability cannot be bounded. Do not touch `src/`, `native/`, format, release, published benchmark, protected prior experiment, `docs/discovery/STATE.json`, or other owners' branches. Preserve defeats, not just favorable cases.

## Ownership

Independent Phased1 A16-O0 research branch; no duplicated implementation identified among open #662/#676/#679/#681/#682 or A15 #677/#680 at this snapshot. Follow exact-head branch custody and leave PR Draft; all measurements must identify original SHA and tool/platform.
