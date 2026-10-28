# J24G19 — certified ignored-field projection for authenticated MessagePack deltas (prospective freeze)

**Date:** 2026-10-28 UTC. **Status:** FROZEN BEFORE MEASUREMENT. **Classification:** scientific research only; neither a Reader product patch nor a policy change.

## Authority / current ownership
- Canonical `FCMO-AI/.CMPCT` main release v0.30.0 / physical revision 24, original published Reader source blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Parent/owner #686 exact `804ccdc9576b860ff3b9d722c7b1e8ad0ac8176a`; J24G18 falsified both mandatory fixed-token admission and catch-and-continue on a signed valid linked delta. No mutation to that branch or to other agents' work.
- Current concurrently owned lanes: #690 signed negative extraction sizes, #687 indexed read locality, #574 discovery state; do not duplicate those patches, modify frozen evaluations, or edit discovery state.
- This work changes the representation of **ignored metadata**, not accepted archive semantics. New branch exclusively adds research implementation, physical source-bound experiment and CI.

## Primary question and worldview delta
A valid signed delta may contain large unknown MessagePack fields that the released interpreter does not consult. Currently `msgpack.unpackb(raw=False)` materializes their entire object graph and then discards them. **Can a narrow native *acceptance certificate* for the ignored subtree, plus streaming projection of only `ops` and `blobs`, avoid that allocation while accepting exactly the same bytes and selecting the same latest valid generation?**

Instead of *rejecting rich metadata to bound memory* (J24G17/18, incompatible), *prove an ignored region safe to elide*. This is a deliberately different information/ownership boundary, not a token cap.

## Mechanism and strong controls
1. Build a native scanner **that never authorizes rejection**. It certifies only a deliberately restrictive fully checked MessagePack subset: nested arrays/maps, ASCII fixstr map keys and ASCII fixstr strings, nil/boolean/fixint and bounded integer encoding, with exact framing, reasonable depth and correct map-key position. Any unsupported, suspicious or malformed construct returns "cannot certify", triggering the original `msgpack.unpackb(raw=False)` unchanged. It never returns an accepting verdict on malformed keys.
2. When certification succeeds on an authenticated kind-1 delta, use the real `msgpack.Unpacker` to parse the top-level map keys and values of `ops` and `blobs` with their original semantics; skip only other complete values. Duplicate top-level keys retain last-value-wins semantics. **Do not use this route for kind-0 checkpoints or unchanged Reader normal paths**.
3. Compare with the actual parent installed Reader, plain `msgpack.unpackb`, and a cheaper nonsemantic `Unpacker.skip` control. Never compare different archive files or include compilation/setup in Reader-open timings.

## Prospective disproof / kill criteria
- **H1 exactness:** A signed linked delta above 65,536 nodes must still select the *latest valid* rename; a signed orphan must recover the older checkpoint; malformed nested map keys, invalid UTF-8, trailing bytes, unsupported ext and non-certified bytes must follow the unchanged canonical path. Any wrong-byte, wrong-generation or accepted-invalid input **kills** transparent projection.
- **H2 resource leverage:** On an actual signed linked delta with `extension=[{"x":0}] * 200000`, measured candidate open peak RSS improves by >=16 MiB versus the same physical released/parent Reader while latest-generation semantics, `read`, `read_range`, `verify` and member hashes agree. When RSS instrumentation is unavailable, no H2 credit.
- **H3 ordinary economics:** On admitted 10,000-map extension input, matched same-process/worker CPU overhead must be <=25% versus canonical decode on identical bytes. Record all raw repetitions and distribution. Above 25% kills promotion as default, irrespective of H2.
- **H4 generic/hostile:** At least 2,000 seeded varied valid supported structures and hostile wire mutants, including map keys, Unicode/UTF-8, recursion, duplicates and lengths; the certificate must never claim safe on a value the original `unpackb` rejects. A single certified-invalid example kills the fast route.
- **H5 carrying costs:** Report every C source SHA, compiled hash, source head, archive/payload bytes, process CPU/wall, subprocess startup separated, peak RSS, proof work, and fallback frequency. Compare against plain direct and (where practical) the simple unbounded Reader. Product archive size/format must remain unchanged.
- Negative controls must be explicit; a green CI job isn't proof of product equivalence. No Windows/macOS or global-memory-bound claim without such tests.
- If H1 or H4 fails, retire/narrow promptly and investigate cheapest independently rooted counterexample; never weaken validation. If H2/H3 fails, preserve negative and prefer deletion/retirement. A passing micro-oracle cannot earn release credit.

## Evidence ladder
- Local C compile and deterministic direct-oracle differential fuzz, before full Reader integration.
- Source-locked signed real Builder/Writer archive A/B with independent physical-footers verifier.
- Fresh-process CPU/wall/RSS on hosted runner; exact-head GitHub artifact hashes and auditor where possible.
- No product source mutation, no merge, no version bump; promotion would require separate product-owner review, full inherited gates and cross-platform proof.

## Continuity
One active question J24G19, next decisive action implement safe-subset certificate + projection; do not expand the mechanism to all MessagePack before this cheapest class resolves. `docs/discovery/STATE.json` is stale on main and has independent #574 ownership; do not alter it.
