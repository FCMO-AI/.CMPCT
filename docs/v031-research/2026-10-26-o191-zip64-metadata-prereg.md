# O191 — ZIP64 fallback DOS metadata fidelity (preregistered)

Date: 2026-10-26
Status: prospective, **before product mutation**.
Parent candidate: O190 PR #518 at 00896f9aeded487e44f92dfae3de4aba59a9dcbf; Reader blob `4af0223af96eb725ea164d9d47812bfa4898045e`.
This is a stacked, independently scoped ZIP64 writer change; O190 retains ownership of signed-time conversion and its genuine small-r24 cross-host positive court.

## Primary question and baseline
O190 repairs the custom fast ZIP export writer's DOS calendar conversion. The same source has a distinct fallback when **any declared logical file size >= 0xffffffff**: stdlib `ZipFile.writestr(ZipInfo(...))`. The constructor defaults to 1980-01-01 regardless of the authenticated CMPCT mtime, and this branch never invokes `_zip_dos_time`. Thus a nominal in-range 2000 timestamp is lost in the fallback. This is a **source-level causal prediction**, not yet a genuine >4GiB archive reproduction.

## Competing actions and BONK
1. Run another small regular-ZIP O190 calendar court: already owned/tested by #518; does not address fallback.
2. Implement separate ZIP64 writer: higher complexity, greater correctness risks, unnecessary for metadata parity.
3. Reuse O190's exact DOS packed-time conversion and decode it to `ZipInfo.date_time` only in the existing fallback. **Selected**: smallest reversible change, no second time semantics.
4. Drop fallback timestamp fidelity as a declared limitation: acceptable only if expense outweighs opportunity, but an O(1) reuse patch is cheaper.

## Falsifiable prediction, strongest control and kill
Baseline: `ZipInfo(name)` preserves default 1980-01-01, even for a 2000 CMPCT source. Candidate: forcing the existing `>=0xffffffff` branch on a *genuine tiny installed CMPCT archive* by changing **only an in-memory row's declared size** (without allocating 4GiB) will produce a valid ZIP whose independent `zipfile` parser reads the same O190 calendar as the ordinary writer for signed 1960, ordinary year 2000, and signed year 2110. Negative control: the identical source without the patch emits 1980 for all, so 1960 happens to match while 2000 and 2110 disagree. Force this branch for each test; do not treat tiny fake-declared-size output as genuine >4GiB compliance evidence.

Kill or narrow if the patched fallback corrupts members, changes payload CRC, changes ordinary writer bytes/behavior, violates an inherited platform policy, cannot pass installed source custody, or if `zipfile` has an unrecognized datetime/ZIP64 constraint. Preserve tests of ordinary valid year/legacy-local behavior plus min/max signed dates. Underlying format r24 is unchanged.

## Evidence ladder / boundaries
- Rung 0: static source and stdlib control showing default 1980 independent of `mt`.
- Rung 1: source-exact installed **synthetic branch activation** using authentic small r24 inputs and independent ZIP bytes/CRC/date checks on Ubuntu, macOS and Windows.
- Rung 2: only then genuine sparse/large-file acceptance, charged RAM/materialization and exact semantics; **not attempted in this PR**, because legacy fallback calls `self.read` on giant content and can materialize >4GiB. Such a test without explicit resource budget is unsafe and not justified by the narrow calendar question.
- General CI and official same-input comparison remain required before release. No product promotion or ZIP64 full-conformance claim here.

## Concurrency
The implementation is restricted to the fallback `ZipInfo` creation path in `src/cmpct/reader.py`, plus a new test, new workflow, and one result record. No modifications to O190 helper semantics, unrelated Reader protections, other agent branches, frozen comparisons, thresholds, `docs/discovery/STATE.json`, format or release law. Before any later shared write, recheck O190 head and rebase/reconcile rather than overwrite.
