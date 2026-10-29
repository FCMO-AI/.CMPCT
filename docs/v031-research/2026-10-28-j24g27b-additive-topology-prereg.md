# J24G27b superseding preregistration — additive topology digest, preserve legacy API

**Freeze before rework:** prior scientific J24G27 prereg at `918df2104b6f0800b6225aad636bea86d891b653`; first prospective topology mutation at `88fc1ac50ecfc9577b57645f1bc6c63473e12ed8`; isolated four-entry topology court at `114add8338a11c7bc6e9639373c447cfbe3bbb4c`. This note is a **new prediction and productization decision**, not a retroactive rewrite of the original prereg or its evidence. As of this note the prior branch implementation of `tree_digest` changes ALL digest bytes from the published public compatibility facade, even when no symlink/hardlink is present. Previous local topology science is retained as such; hosted original-head CI must be evaluated separately.

## Discovered compatibility debt and new decision

The currently exported `cmpct.core.tree_digest` is part of a deliberately preserved public compatibility facade. A topology-corrected digest without versioned naming is a possible breaking public behavioral change for consumers storing expected v1 hashes, despite no format or Reader changes. Making a new hash superior does not make its different outputs compatible. The strong simpler control is **retain the exact v1 legacy implementation and name**; expose **`tree_topology_digest`** as an opt-in, domain-separated SHA-256 topology witness. This may leave the old helper ambiguous; add documentary specificity that v1 is content-oriented and cannot prove link topology.

## Hypothesis and disproof

H1: exported `tree_digest` is text-identical to published Git blob suffix, retaining byte-identical hashes for ordinary and link trees (including their known collisions). H2: newly named `tree_topology_digest` passes the full 8-case host test and 15 four-entry hardlink-partition oracle without changing the archive format. H3: public facade exports both, and no preexisting call sites require signature changes. H4: there is no additional runtime/resource cost for callers that keep using v1. H5: existing CI does not introduce new failures outside inherited baseline, across tested hosts.

**Kill:** wrong legacy hash; alias replacing old function; lack of cross-root topology consistency; unsupported test host; substantive ecosystem caller needing same old name to take on new semantics; inability to keep proof and implementation separate. If H1-H3 hold, only call topology comparison valid when user explicitly invokes v2 helper.

## Counterfactual and opportunity cost

The earlier observation that `tree_digest` is intentionally re-exported by `core.py` was already prospectively recognizable. The additive design could have been selected before the first product mutation and avoids an entire compatibility issue without sacrificing the prospective topology oracle. Do NOT modify Discovery Engine policy based on one episode. This note does not touch the separate r24 link-integration owners #709/#716 or the stale `docs/discovery/STATE.json` owner #574.

## Acceptance and self-critique

Compare the original legacy function source with `main@80c358f8` and source branch `agent/v031-development@4545d7d5`. Keep at least one old-collision test to show why topology requires opt-in. Observe separate new-head CI; old-head results cannot automatically pass the new head. The research change does not improve actual archives, Reader, compression or release, and should remain draft until cross-platform and use-case value are evidenced.