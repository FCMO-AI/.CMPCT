# O73 — Gap-separated physical ZIP owners: prospective charged oracle

Date: 2026-10-25 UTC. Status: **PREREGISTERED before instrumentation or measurement**. Research only; no product/format/release credit.

## Authority and coordination
Published CMPCT v0.30.0, r24. Parent is O70 PR #426 exact head `887e419b4ccbef06ac21a7920e06f55743333664` and Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. O70 measured 687.911× decoded-work export when eight ZIPs of heterogeneous physical sizes share a single `S_PACK`; its strongest noncohort comparator paid +2,122 complete bytes and 3.75× creation wall. O71 PR #427 independently owns VZIP content-reuse admission, not eight-ZIP physical ownership. Search of open PRs found no existing gap-separated physical-owner oracle. This research stacks on O70 without altering its owner branch, frozen result, thresholds or product code. The Discovery Engine STATE.json is stale and does not grant a claim.

## Primary falsifiable hypothesis
A **physical-size-gap** separation of the same eight real ZIPs can preserve most of the existing large-cohort creator benefit while avoiding whole-pack decode for tiny selective reads. Source-independent oracle: sort eight original ZIP physical sizes and take the largest adjacent ratio gap; only split when the larger/smaller adjacent pair exceeds **16×** and both sides are nonempty. Put the **larger** class in one authentic CMPCT `S_PACK` physical owner; send the **smaller** class through the existing individual VZIP/opaque path. Never use names, content hashes, a benchmark identity or private fixtures to decide the split. If no qualifying gap, run unmodified whole-cohort policy. This is an in-memory source transformation for scientific comparison; it is not shippable production admission.

Primary 6-large/2-small heterogeneous corpus: predict (i) verified byte-identical reconstruction for all eight files, (ii) selected small-member decoded blob bytes at least **20× lower** than the original full cohort and (iii) complete creation wall **<2× original** on the same runner, substantially less debt than the O70 all-independent control. Full stored-size debt must be **<=1%** relative to original for a credible bounded product path. The strict conjunction is the prospective `CREDIBLE_SPLIT_HEADROOM` outcome. Any component failing means **NOT_CREDIBLE_IN_TESTED_SCOPE** (with raw evidence preserved); no threshold adjustment.

## Strong controls and structural hold-out
Execute three genuine Builders on the **same exact source directory** with identical metadata: untouched eight ZIPs all packed; O70 all-individual in-memory count gate (only the original single expression changes); and gap-separated large/small owner oracle. Compare 6-large/2-small original, held-out 5-large/3-small, a hostile homogeneous eight-large cohort where the gap rule must leave archive bytes identical to shipping, and an independent 7-large/1-small corpus where the rule must not depend on number of tiny members. All inputs are deterministic stdlib ZIPs, each checksum frozen before running; no regeneration across alternatives.

Demand actual revision-24 complete archive bytes, create wall/CPU, kernel peak RSS when available, initial Reader construction and selective 64-byte read wall/CPU, decoded physical blob bytes, invoked blob count, full CMPCT.verify, full read and extract byte equality for all members. The measured read timing is fresh Reader, not necessarily cold OS cache. Each method is repeated ABBA/Latin-counterbalanced with multiple child-independent processes where practical; preserve raw readings.

## Alternatives / BONK / cost
- Keep shipping cohort: strongest known create/size control, worst small-read work.
- Disable all cohorts: strongest existing small-read control, expensive creation.
- Physical gap split: may preserve six-large pack and bound tiny-read; costs another owner, VZIP parsing on small members, index entries, allocation and creator selection complexity.
- New lazy index/range primitive: could preserve solid compression but needs new Reader architecture; postpone until this simpler fully charged oracle is falsified.
- Fixed size threshold is rejected as fixture gardening; a relative gap has a plausible corpus-independent signal but still needs hostile validation.
- Also price extraction/read CPU, RSS, index overhead and unsupported archives; no external ZIP/Zstd win, update behavior, cold disk I/O or cross-platform portability claim from this oracle.

## Kill and decision
Reject split-family productization when no credible Pareto trade-off remains after complete cost accounting, if homogeneous control diverges, if exact bytes or authentication fail, if the change only moves the cost to memory/decode, or if the result merely repeats a known owner. A positive result advances to **prospective generic admission + stronger held-out corpus**, not product merge. A negative result can retire gap partitioning here without obscuring O70's valid locality hazard.

## Exact provenance and constraints
Original Builder blob must match `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Oracle source text hashes, original source file SHA, inputs, actual source HEAD, process labels, archive SHA, per-sample data and scientific verdict belong to a raw JSON CI artifact. Test file runs isolated from unrelated research conftest. No weakening frozen gates, corpus, safety or format law. This prereg commit precedes research implementation.
