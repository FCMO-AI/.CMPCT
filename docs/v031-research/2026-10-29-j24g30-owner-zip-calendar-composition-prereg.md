# J24G30 — existing owner ZIP calendar × failure-atomic publication composition, preregistration

Date: 2026-10-29 UTC. Status: **PREREGISTERED BEFORE ANY PRODUCT SOURCE MUTATION**.

## Authority and nonduplication

Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0 / r24. Parent ZIP publication owner is **O149 #492**, exact `ca01d885fedc8ffc343b9c3c624eddd134158452`, Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`. Independent earlier ZIP DOS calendar owner **O190 #518**, exact `00896f9aeded487e44f92dfae3de4aba59a9dcbf`, Reader blob `4af0223af96eb725ea164d9d47812bfa4898045e`; its ZIP64 fallback metadata continuation **O191 #519**, Reader blob `74aa7b286dec9700b070b948f5975b22028e41fe`. O193 #521 separately owns streaming ZIP64 materialization; do not copy that work here.

J24G28/29 #722 incorrectly duplicated O190 and introduced two proven source-level semantic flaws; it is now **closed unmerged** with exact negative evidence. This **composition**, not a new timestamp algorithm or exporter, transplants the *unchanged* owner O190 helper and O191 fallback date assignment onto the existing O149 ZIP publication branch. Parent branches stay untouched. Scientific history and existing tests remain unchanged.

## Hypothesis and disproof

H1: The full O190 integer-floor, timezone-bound DOS helper on staged #492 preserves both signed i64/calendar acceptance and **local DOS dates around 1980 UTC cutoff**, unlike the retired #722 premature UTC clamp. H2: O191's existing fallback ZipInfo date assignment closes inherited ordinary-time metadata loss in the ZIP64 fallback without changing O149 destination/atomic-publication logic. H3: For identical generated r24 inputs, ordinary in-range ZIP contents/CRC/bytes remain unchanged on the same host between parent and composed candidate; pre-1980 and post-2107 dates are *intentionally normalized* only within ZIP. H4: Inherited ZIP O149/O140/O135 and direct Deflate integrity gates remain positive on candidate; no weaker validator, source-identity or release policy.

**Kill/hold:** any wrong local calendar on integer-floor nanoseconds, false archive acceptance/corruption, destination altered on injected failure, ordinary ZIP byte difference on same host, or failed exact-source three-host reproduction invalidates this composition. No blanket acceptance, release or merge claim from one small court.

## Cheapest evidence rung and controls

1. Source hunk identity before mutation; preserve exact O190/O191 semantics, not an invented clipped heuristic. Independently establish 32,774 source-level calendar-oracle cases across seven TZ settings (O190 0 mismatches; #722 13,057, including 457 lower-local-bound and 12,600 float-rounded nanoseconds). This is mechanism evidence, not product proof.
2. Installed-package same-physical first-party r24 three-host court on signed/ordinary/upper and near-cutoff/1ns controls, with SHA-bound source and unchanged ZIP payloads; separate parent source as control.
3. Re-execute unchanged inherited O149/O140/O135 tests (and direct-Deflate) without changing historical frozen source-fingerprint checks.
4. Cross-branch interactions with #492 source/kind/staging and O191 fallback; release gates, ZIP64 real 4GiB/metadata/resource economics, namespace races and trailing Deflate acceptance remain debt.

## Alternatives and opportunity cost

- Reopen #722 and repair it: duplicate owner and worse semantics; rejected.
- Reimplement ZIP writer, change timezone from local to UTC, or change archive format: unjustified new contract; rejected.
- Cherry-pick all #518/#519 commits wholesale onto #492: drags independent docs/CI lineages and may override O149; rejected.
- **Chosen:** surgical exact-source semantic composition and a distinct controlled cross-owner test. No changes to main, existing owner branches, discovery state, evaluator, benchmark thresholds, version or release.

## Resource, portability and scientific scope

Only O(1) date arithmetic and one ZipInfo date tuple per fallback file; no new decoded work/bytes, but no comprehensive performance credit until measured. ZIP64 fallback still materializes large logical members; staged publication still has known namespace races and temporary disk/owner/xattr debt. Current experiments cannot claim complete ZIP64, crash durability, hostile concurrent stage safety or any product release.

**Decision boundary:** preserve result-bearing negatives, preserve owner provenance, allow base to win. The next operator must inspect actual exact-HEAD CI and source SHA before any claim.