# ONE-G0.2 stage-owner reachability and hash-charged cross-check — 2026-09-08

## Mission Lock / Referee

The current speed question is whole-writer stage ownership after demoting the positional fused-observation cache against a competent native fresh observer. The frozen owner adjudicator remains in `benchmarks/one/one_g02_native_writer_stage_owner.py`: a stage needs at least 20% median wall share on at least two 1 MiB rows; an adjacent pair needs at least 40% combined share on at least two 1 MiB rows when no single stage qualifies. No threshold, row, repetition count, semantic gate, or resource gate is changed here.

Falsifiable hypothesis: the repaired exact-head stage-owner lane can reach its decision function without another evidence-lane failure, and any later `root_hash` ownership can be interpreted only after distinguishing unavoidable current-root authentication from potentially already-known previous-root identity.

Disproof: any missing test/benchmark entrypoint, loss of the 1 MiB decision scale, semantic/oracle failure, or inability to bind evidence to the exact source SHA invalidates an ownership claim. A green unrelated workflow is not a stage-owner result.

## Builder

Primary branch source before this receipt: `69054364282ac4bf53f554d5dde399ff55e005ea` (`research/cmpct1`, ONE-G0.2).

The dedicated workflow `.github/workflows/cmpct1-one-g02-native-writer-stage-owner.yml` now contains a fail-fast reachability step which checks:

- `tests/one/test_native_observe.py` exists;
- `tests/one/test_native_writer_stage_owner.py` exists;
- `benchmarks/one/one_g02_native_writer_stage_owner.py` exists;
- the benchmark exports a callable `run()`;
- `PROFILE_SIZES` still contains the 1 MiB decision scale.

This hardening changes no scientific criterion. It prevents runner time from being spent on a lane that cannot reach its preregistered decision.

The older `.github/workflows/one-g02-root-hash-charged-direct-emitter.yml` was also hardened after hostile review exposed that its PR path used bare `actions/checkout@v4` plus `github.sha`. The branch version now binds `EVIDENCE_HEAD` to `${{ github.event.pull_request.head.sha || github.sha }}`, checks out that exact revision, asserts `git rev-parse HEAD == EVIDENCE_HEAD`, and names the retained artifact with the same source SHA. Its scientific benchmark gates are unchanged.

## CI evidence boundary

PR #88 intentionally uses frozen deferred-v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772` as its base. That base does not contain `.github/workflows/cmpct1-one-g02-native-writer-stage-owner.yml`. On source `69054364282ac4bf53f554d5dde399ff55e005ea`, the commit check surface contains no check named for the dedicated native-writer stage-owner workflow. Therefore no stage-owner decision is claimed from hosted CI at this source.

Run `34198262852`, `ONE-G0.2 root-hash-charged direct emitter`, completed successfully while PR #88 reported head SHA `69054364282ac4bf53f554d5dde399ff55e005ea`. However, hostile review found that this older workflow did **not** bind checkout to the PR head. Its retained artifact is named `one-g02-root-hash-charged-direct-emitter-ee29ca384838d023ca5326f39667e5c8f948a9f8`, consistent with `github.sha` resolving to the PR merge revision rather than the branch head. Accordingly, this run is merge-ref evidence, not exact-head authority.

The successful merge-ref run still establishes a bounded compatibility fact about that tested merge revision: the semantic/hostile test step, frozen root-hash-charged direct-emitter falsifier, and artifact preservation all passed. The benchmark exits successfully only when its frozen gates pass, which means that tested merge revision satisfied semantic/oracle gates plus productive median <= 0.95, at least 18 productive rows <= 1.00, every productive per-size median <= 1.03, worst productive row <= 1.10, and every control per-size median <= 1.05. These bounds must **not** be promoted as exact-head `690543...` measurements.

The benchmark charges SHA-256 of **both** previous and current version roots inside both compared writer paths. Its merge-ref green therefore remains supporting evidence that the direct-emission idea survives a less flattering writer bill, but it does not establish which whole-writer stage owns current creation time, does not split previous-root from current-root hashing, and does not establish product-writer or v0.29/v0.30 superiority.

## Hostile Reviewer

The strongest current ambiguity is `root_hash` attribution. The stage-owner profiler times `sha256(source)` and `sha256(target)` together. For an adjacent-version writer, a previously committed generation may already carry its trusted root identity; if so, rehashing the previous root is not necessarily unavoidable current-update work. Therefore an eventual `OWNER_ROOT_HASH` result must be decomposed before authorizing authentication/observation fusion. The frozen combined `root_hash` stage should remain the owner-adjudication quantity so the experiment is not rewritten after seeing data; supplementary attribution should split previous-root and current-root cost without moving the decision gate.

The second negative is evidence plumbing itself. The branch check surface reported 153 checks for `69054364282ac4bf53f554d5dde399ff55e005ea`. A campaign whose law is marginal information yield per compute should eventually path-gate or retire stale experiment lanes. That CI cleanup is secondary to obtaining the current stage-owner result and must not be used to rewrite frozen v0.30 comparator history.

A direct clone/run attempt from the available execution container failed before repository access because DNS could not resolve `github.com`. No local timing or scientific result is claimed from that failed attempt.

## Decision / handoff

1. Keep the fused observation cache demoted as the general speed path.
2. Keep native fresh observation as the competent observation baseline.
3. Do not infer a stage owner from the green hash-charged direct-emitter merge-ref workflow; it is bounded supporting evidence only.
4. Obtain an exact-source execution of `one_g02_native_writer_stage_owner.py` through a lane that can actually execute on the research branch, preserving the frozen 20%/40% adjudicator and 1 MiB requirement.
5. Require exact-head binding for any subsequent hash-charged direct-emitter authority; the research-branch workflow now contains that hardening.
6. If `root_hash` wins, split prior-root versus current-root SHA cost before spending implementation budget. If native observation wins, split Python/ctypes copy overhead from C-kernel work. If another stage wins, move native optimization upward. If only an adjacent boundary qualifies, test pass fusion. If none qualifies, prefer global pass/memory-traffic reduction or deeper Law-discovery economics over local polishing.

No stored-byte, reader-complexity, decode, selective-read, reconstruction-work, blast-radius, v0.29, or deferred-v0.30 scoreboard claim changes from this receipt.
