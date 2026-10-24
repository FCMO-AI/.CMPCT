# O28 preregistration — ordinary Reader hardlink graph × static destination containment

**Timestamp (UTC):** 2026-10-24T21:06Z. **Status:** PRE-RESULT / NO PRODUCT CREDIT.
**Exact parent:** PR #380 `agent/phased3-v031-static-dest-safety-o27-20261024@34a2059491fcd38bc09231cba178ec8541f74fdb`; Reader blob `4ed4e0e20bc460d95bb101ee595041a051d05d31`.
**Independent source owner:** PR #378 `agent/phased1-v031-reader-hardlink-graph-o25-20261024@208006289361b9f5cb7a6fcdea1d342ca1fe5080`; Reader blob `7274e055f210bc1bb53290a8d898c5724820b035`.
**Released floor:** v0.30.0, physical format r24; no change permitted to format, constraints, comparison semantics, or either owner branch.

## Primary question / intervention

Can the existing, independently proven iterative hardlink terminal-owner resolution (O25) and static pre-existing destination-path pivot refusal (O27) coexist in **one installed Reader** while keeping the exact surgical code of both owners and preserving authenticated signed-generation resource and symlink safety? This is **product convergence**, not a new compression hypothesis.

The source changes are expected to be disjoint: O25 modifies Reader initialization and four read/SHA surfaces, while O27 modifies a destination preflight helper and one extractall call. Compose the O25 exact diff onto the O27 full Reader, with no text rewrites to either algorithm and no modification to frozen fixtures or release gates.

## Prospective predictions and independent controls

- **P1 source identity:** The resulting Reader is exactly PR #380 plus only the five hunks in original PR #378; all O27 extracted snippets and all parent Reader code outside O25 must remain byte-for-byte identical.
- **P2 safety:** The eight original O25 cases (self-cycle, two-cycle, wrong kind, absent owner, >1,300 valid acyclic edges, one direct owner, plain checkpoint and fanout) retain the same assertions and pass. In particular malformed archive graph is rejected at ordinary Reader construction; a large valid graph can read, range-read and SHA without recursion. Strict preflight oracle retains its original outcomes.
- **P3 static destination:** The O27 real-archive prewrite pivot test and original O27-inherited #269 static pivot tests still pass, including full outside-sentinel inode/bytes checks and legitimate hardlink/authorized symlink extraction. **No pre-existing pivot guard is weakened.**
- **P4 integration:** A separate combined real-r24 test must include a multi-edge valid hardlink graph plus a late pre-existing symlink destination pivot; preflight of the destination must reject before earlier members are written, and safe re-extraction must preserve contents and owner identity. On a cyclic signed graph ordinary open must fail before a destination is touched.
- **P5 provenance:** The release format remains r24, no new codec, no builder, writer, validation, env ceiling or evaluator modification. Product performance remains unmeasured until exact-head compare.

**Strong simpler controls:** Keeping O25 and O27 independent retains both local green courts but cannot demonstrate their joint Reader semantics. Copying entire O25 Reader would erase O27's destination protections. Reimplementing either algorithm increases divergence. Prefer strict union without novel algorithm.

**Alternative explanation / failure condition:** Each suite may pass independently but their composed Reader could fail due to constructor ordering, raw graph alias targets or extraction hardlink publication order. Any lost owner assertion, new safety exception, source-hunk collision, unstable Windows/macOS behavior or material regression is a **stop-and-diagnose**, not permission to weaken assertions. CI infrastructure failure does not demonstrate product failure.

## Evidence ladder and decision

1. Pin both exact Git heads/blobs and verify patch applies without fuzz or ambiguous context.
2. Add unchanged O25 owner tests and a separately rooted combined r24 adversarial test, without changing O27 owner's tests.
3. Exercise focused courts on all supported CI platforms, plus exact-head preexisting regression/installed package/security checks when available.
4. Release promotion requires its own complete performance, package and safety gates; green focused research never authorizes release.

**Concurrency:** O25 and O27 owners retain their PRs and working branches; this new branch alone owns their composition, and neither `docs/discovery/STATE.json` nor other shared authority is modified. Re-read owner heads before final writes.

**Prospective decision:** Promote the union for further productization only if all source and semantic checks pass; otherwise preserve the negative and return to the minimal failing pair. This experiment carries no independent compression or archive-byte claim.
