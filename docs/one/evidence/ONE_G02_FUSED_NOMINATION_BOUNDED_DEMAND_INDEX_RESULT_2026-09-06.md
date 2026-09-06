# ONE-G0.2 fused nomination bounded demand index — terminal result

Date: 2026-09-06
Experimental line: ONE-G0.2

## Exact CI authority

- branch source head: `832e59f88a078705d52927648bb5f81821235d1a`
- PR merge test SHA: `45507b3505c0edf87153cd77067612522bd5edf1`
- workflow run: `34005699591`
- job: `101412341596` (`demand-grown-index`)
- conclusion: **success**
- artifact: `9980903715`
- artifact ZIP SHA-256: `1ae93bd4b740c897069fce6afb09c2991d48387ee77a7c9889f370925be9f9aa`
- ONE semantic/hostile tests: **93 passed**
- decision: **`advance_bounded_demand_nomination_index`**

## Result

The fused nomination kernel preserved selector semantics, selector trace, nomination counts and negative behavior against the independent selector + fixed event-consumer oracle across the frozen 4, 8, 16, 64 and 256 KiB matrix with seeds 7, 29 and 53.

There were:

- no selector mismatches;
- no trace mismatches;
- no nomination mismatches;
- no false exact nominations;
- no capacity errors;
- no state regressions under the frozen gate.

The research prototype/oracle reserves **198,144 B** for its fixed event index. The fused demand-grown candidate instead reserved at most **13,824 B** for its event index on the frozen envelope, including 256 KiB rows. That is **0.069767x** of the fixed prototype index (about **93.02% less event-index state**).

The promoted minimizer state remains **41,056 B**. Maximum observed total fused reserved state was therefore **54,880 B** on the 256 KiB rows that required 512 global entries. Other 256 KiB rows used 128 or 256 global entries and total state of 45,664 B or 48,736 B respectively.

The largest observed global peak was 272 entries on a 256 KiB independent-random row; geometric growth selected a 512-entry capacity. This remains an observed-envelope fact, not a universal proof that arbitrary future inputs can never approach the 8,192-entry hard cap.

## Causal interpretation

The earlier 198,144-byte carrying-cost concern belonged to the fixed semantic replay prototype, not to the demand-grown fused mechanism. Nomination state can be carried according to observed demand while retaining the same hard 8,192-entry cap and exact semantics.

This closes the specific fixed-index regression debt sufficiently to advance the fused writer-discovery path. It does **not** prove product writer speed or establish that event-index state is globally negligible: future larger/hostile matrices must still expose demand and worst-case behavior explicitly.

## Next decisive question

Integrate the already-advanced relation witness proof-deferral principle into the native fused nomination/admission path. The witness remains an Opportunity Gate only; the safe exact relation proof remains sole Law authority. Charge elapsed, proof/source traffic, demand-grown index state, negative controls, overlap safety and safe fallback together. Do not reopen fixed 198,144-byte storage or replace it with another globally preallocated index.
