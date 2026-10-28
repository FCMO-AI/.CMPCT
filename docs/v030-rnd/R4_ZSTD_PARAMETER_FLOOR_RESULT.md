# v0.30 R4 Zstd parameter-family floor result

**Status:** CLOSED / PROVEN FLOOR FOR THE MEASURED PARAMETER FAMILY  
**Authority branch:** `agent/v030-authoritative-integration`  
**Exact analyzer head:** `4a2f831e06228ad4b4ad47fd9e6a15dd8fab071c`  
**Workflow run:** `34634444661`  
**Artifact:** `10276859489` (`v030-r4-zstd-parameter-decomposition-4a2f831e06228ad4b4ad47fd9e6a15dd8fab071c`)  
**Artifact digest:** `sha256:a72ac789a46f505e2752ff445b1cc824d62f8c2f10ba56e2fd9b12a8b1b5f9e1`  
**Shipping credit:** none

## Question

After the fixed `strategy+searchLog` whole-archive hybrid failed its product hypothesis, one loophole remained: perhaps a content-driven selector over *all* already-measured level-15/level-19 parameter combinations could still beat the inherited v0.29 floors without paying full level-19 cost.

The exact floor oracle removes that loophole before any more threshold tuning. For every distinct captured final payload it grants perfect foresight over every measured parameter variant, then solves the exact Pareto dynamic program across payloads. It is intentionally optimistic:

- workload identity is available to the oracle;
- each payload may choose its own parameter variant;
- negative measured timing deltas are clamped to zero;
- no selector metadata or discovery cost is charged;
- only the already-measured payload size/time points are used, so no new measurement noise is introduced.

Failure under this oracle is therefore strong evidence that the measured parameter family itself cannot close the red.

## Hosted result

| Workload | L15 fixed archive | Accepted v0.29 | Strict saving required | Maximum family saving | Optimistic floor | Reachable? | Unclosable shortfall |
|---|---:|---:|---:|---:|---:|---|---:|
| Office | 6,081,882 B | 5,954,026 B | 127,857 B | 126,990 B | **5,954,892 B** | **No** | **867 B** |
| Analytics | 6,569,059 B | 6,135,172 B | 433,888 B | 447,824 B | **6,121,235 B** | Yes | 0 B |
| Developer | 838,930 B | 744,337 B | 94,594 B | 27,941 B | **810,989 B** | **No** | **66,653 B** |

### Office

Even an impossible perfect per-payload selector cannot make the fixed representation strictly smaller than accepted v0.29. Its absolute optimistic floor is `5,954,892 B`, still 866 bytes larger; strict victory requires one additional byte, hence the 867-byte unclosable shortfall.

This is a Forge **S1 proven floor** for the measured final-compression parameter family on this representation. More thresholds, selectors or preset mixtures cannot repair Office.

### Developer

The result is much stronger: perfect foresight leaves a **66,653 B strict shortfall**. Parameter selection is not the owner of this red.

### Analytics

Analytics is the only target where perfect foresight can cross the inherited density floor. But the exact optimistic minimum measured **marginal final-compression time** required merely to become one byte smaller than v0.29 is:

**5.769721788 seconds above the level-15 final-compression baseline.**

This lower bound is optimistic: it excludes selector/discovery cost, filesystem staging, verification, metadata publication and any new reader dependency. The same workload's fresh ZIP/Deflate-9 complete create time in the effort/whole-archive receipts is roughly 1.36–1.53 s. Therefore the measured parameter family cannot satisfy the joint density + external-time product objective even with perfect per-payload foresight.

## Decision

**Retire Zstd level/preset/parameter recombination as the primary R4 for these reds.**

This closes, rather than merely discourages, the following rescue attempts on the fixed representation:

- another global effort level;
- sparse promotion to ordinary level 19;
- a fixed `strategy`/`searchLog` hybrid;
- workload-blind threshold tuning over the measured variants;
- a perfect-oracle selector over the measured variants.

The positive mechanism-level lesson is retained: Zstd `strategy`/`searchLog` explain a large fraction of Analytics' density movement. The negative engineering conclusion is that buying that movement through the measured search family costs too much, and on Office/Developer cannot cross the inherited floor at all.

## Next R4 boundary

The next experiment must change how useful context is represented or reused, not ask the same independent pack compressor to search harder. Candidate mechanisms must remain generic, pay their own bytes/time/dependency costs, and preserve integrity, recovery and bounded selective access.

A shared-context mechanism is therefore admissible as a new hypothesis. One concrete next falsifier is a fully charged, self-trained shared Zstd dictionary over cheap-gated final payloads: dictionary bytes, training time, compression work and per-reference physical tax are charged. A positive oracle result would still require a real bounded owner representation and all-15 evidence; a negative result should retire that family quickly rather than begin another parameter sweep.
