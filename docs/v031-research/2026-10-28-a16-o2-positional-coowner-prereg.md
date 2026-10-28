# A16-O2 — positional co-owner proof, prospective frame review

Date: 2026-10-28 UTC. **FROZEN prediction before O2 implementation or measurement.** Research-only; no CMPCT r24 archive, Reader, format, release, or shipped performance claim.

## Authority / base / collision
- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/revision24.
- Source parent: A16-O0/O1 PR #683, `acaa48a74c2e8859e476c629bf1debab25e89f37`. Original unmodified `research/a16_o0_sharing_run_court.py` blob `afe87fc617cc4c694a7db6437c508e39a20088d1`, and prior O1 adversary remain immutable controls.
- Discovery `STATE.json` on main is stale; #574 owns reconciliation. Existing #683 owns **binary shared-class** coalescence, already falsified; O2 is a different, preregistered **positional exact-equivalence proof frame**, isolated on a distinct branch. No existing open PR found on this narrow proof. No shared source changes.

## Observed baseline and frame review
A16-O0's binary globally shared/unique segmentation saves 0.9768% on 32 x 64KiB prefix/suffix 12-share data versus nonredundant fixed CHUNKREF (below its locked 1% requirement), with a ~3.9x component full-member decode benefit. A16-O1 establishes 7.855x **storage amplification** when all individual blocks are shared across incompatible co-owner sets. A15-O1 establishes a large fixed-block storage benefit and real decode-unit cost. Three adjacent ownership investigations justify stopping heuristic threshold gardening. The changed question is whether an **exact positional equivalence certificate** can provably preserve reusable physical owners, not another shared-count threshold.

## Mechanism / strongest control / alternative explanation
For each 4KiB *position* and exact byte value, collect the set of source-member indices that contain that value at that position. Merge two adjacent blocks in one member **only if their exact positional co-owner member sets are equal**. Under that condition every member in the set has the same two bytes at the same adjacent positions; induction extends to a maximal run, so the concatenated owner remains shared by the same members. Count all headers, Zstd-19 frames, SHA-256, references, variable-length owner fields, full source membership-index construction, and any selector/fallback. SHA alone never proves equality: exact byte equality must control identity.

Strong controls remain *unchanged* A16 fixed CHUNKREF and direct 64KiB/member, with the O0 binary SEGREF kept as a losing reference, and same-input source SHA. A simpler whole-envelope minimum selector is the non-optimistic alternative; it can prevent **stored** byte losses after all arms are evaluated, but its creation CPU/memory must be counted. A surviving decode benefit may merely reflect fewer Zstd calls, not a superior universal format.

## Frozen questions / predictions / kills
1. **Hostile transfer:** On O1 independent positional permutations, seeds 20261030/20261031, predict positional-coowner O2 does *not* merge all 16 blocks; raw O2 size must stay <=1.01x fixed CHUNKREF with exact 32/32 member reproduction. A counterexample >1.01x or lost sharing despite identical positional groups rejects this narrow claimed containment. No threshold changes.
2. **Original positive transfer:** On 20261028/20261029 prefix12/suffix12, predict O2 preserves the same 2 units/member and complete size within 0.5% of former SEGREF. Do **not** relabel inherited 0.9768% (<1% threshold) as a passed product criterion. Primary conditional product-path headroom still demands >=1.0% complete-byte reduction *and* >=1.5x CPU and wall full-member decode improvement against fixed CHUNKREF on BOTH original partial-sharing seeds. If absent, do not promote.
3. **Held-out structural hostility:** Add a position-shift/permutation family and two independent seeds fixed before data observation; exact source and member SHA must match all arms. The new proof must not use fixture/regime names, source file identity, or decoder-visible gifted oracle facts.
4. **Safety and economics:** A detached parser must reconstruct all original members from complete serialized envelopes; reject bounds overflow/truncation/forged index/hash/trailing data. Record raw repeated CPU/wall for full-member decode with same libzstd, Zstd frame/decoded-unit counts, creation CPU/wall including building positional member sets, transient object memory where measurable, and exact complete stored bytes. In-process decoder results do not confer full installed-Reader economics.

No numeric v0.31 release or merge can be earned by this science. Lower-tier positive evidence is only a reason for a product-level admission/Reader gate; a negative keeps this family parked.

## Cheapest execution / counterfactual
First mathematically prove the incidence-preserving rule and run a small adversarial structural falsifier. Then evaluate full-size exact envelopes on inherited O0/O1 plus held-out permutations. Only if a complete-byte and read-work win survives strong existing controls and safety costs would hosted three-OS/product work be justified. Counterfactual: a set-equality check at adjacent positions would have rejected binary-class merging before expensive A16-O1 execution; its predictive value remains a hypothesis until tested on both positives and hostiles.

## Boundaries
No mutation to original frozen preregistrations, benchmark records, release/version/format law, shared Discovery state, other branches, or CI evaluators. Preserve negatives even if the conditional product-path criterion fails. Source timestamp and SHA govern all experimental claims.