# J24R04 — Sparse short-vector direct traversal × large-vector binary search (prospective freeze)

**2026-10-27 UTC, scientific/product-candidate only. Freeze before changes to Reader/tests.**

## Repository authority and concurrency
Released checkpoint v0.30.0 / disk revision 24; active v0.31 research remains unmerged. Owner J24R01 PR #584 has exact HEAD `70336307312b5b277f0885c0057d2cddab0aefc1` (Reader blob `ca1763b9d69b385eab80d0ed67a914672dbe93fc`). Authenticated composed parent J24C02 PR #569 is `c5e13bb3fbb4cdade8b64246658ce7c7818de41f` (Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`). J24R02 PR #586 and J24R03 PR #593 are distinct **measurement-only** courts; do not modify them. Discovery STATE has a separate owner in PR #574. `CONCURRENCY_PROTOCOL.md` and `tools/discovery_claims.py` do not exist at this source at freeze. Scope: only short-vector S_SPARSE `read_range()` dispatch in a new stacked branch, no Owner branch edits.

## Primary question and falsifiable mechanism
J24R02's source-exact hosted ABBA proved unconditional binary search improves late reads at E=4096/65536 by 55×/775×, but slows the original baseline at E=1/4 by 26–30%. J24R03 transferred benefits to early/middle/balanced/32-extent reads but kept small E debt. A binary search incurs an unnecessary `bisect` callback for a *bounded short-vector* of sparse extents, while a direct traversal is already correct and avoids callback cost. Can an explicit small-vector path preserve old E=1/4 efficiency with no loss to high-E, exact bytes or validator law?

## Strong controls, predictions, kill conditions
Control A: **original** #569 source and exact fixture r24 bytes. Control B: unchanged unconditional `bisect` owner #584. Candidate: branch only for E<=4 using one original direct traversal; use the exact J24R01 binary search unchanged for E>4. Count <=4 is an explicitly bounded short-vector *algorithmic specialization*, not a corpus fingerprint or semantic override. The threshold is frozen here, not fitted after observing this candidate.

Expected: E=1,4 late-position 256-query medians improve materially against #584; E=4096/65536 preserve >=10× versus #569 and stay within 5% of #584 under paired hosted timings. Hold out E=2,3,8,16,37,129 plus early/middle/late, hole/extent-crossing and boundary queries; old and candidate bytes and errors must be identical. Full read/verify and corrupted geometry rejection must be unchanged. Preexisting S_CHUNKS cold-open cost and publication bugs are not this question.

**Kill / narrow:** any wrong logical byte, incorrect hostile bound/rejection, extra indexed O(E) allocation, source/fingerprint inconsistency, confirmed >5% small-E paired median slowdown versus #569 outside measurement noise, or material large-E loss vs #584 forces investigation/narrowing. Do not massage thresholds after results. If the short vector still loses or high-E overhead grows, preserve negatives and attempt a structurally different single-loop dispatch or retire. Do not lower repository release-performance thresholds.

## Evidence ladder and whole-system limits
Cheap local micro/oracle already compared linear, callback bisect, Python binary and short-vector selection (not product evidence; noisy). Next: reuse unchanged inherited O212 genuine wire/validator tests; add held-out semantics in new tests. Hosted exact-source installed-reader three-way ABBA on identical revision-24 files, separately measure open CPU/wall, selective CPU/wall, same archive bytes, peak RSS as host-limited diagnostic, corruption/geometry and conformance. Source hashes/fixtures, raw observations, repeated medians and failures must be retained. Compare original and #584 directly rather than infer from historical ratios. Measure no compression/create benefit (code only changes Reader range). Official same-runner parity and full safety/platform gate are separate obligations; no merge/version/release credit from research-only tests.

## Alternatives and counterfactual
Alternative 1: new O(E) offset array (rejected: adds cold-open/memory carrying cost). Alternative 2: custom pure-Python binary loop (micro control often slower than C bisect). Alternative 3: unconditional original scan (fails large E). Alternative 4: short-vector direct plus large-vector bisect (chosen; bounded and reversible). Earlier recognition of bounded small-vector overhead could have predicted E=1/4 failure before implementation; held-out transfer and exact installed ABBA remain required.

## Public/format constraints
No codec selection, Builder, Validator, archive format/revision, reader integrity, public claims, licensing, frozen thresholds or other repository changes. Parent #584 owns unconditional mechanism and retains its negative result; this is a stacked research candidate. Report historical/source HEAD, exact CI, negatives, pending/missing evidence and merge=NO.
