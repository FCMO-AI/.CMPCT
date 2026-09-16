# Federated Office/Analytics product-floor result

Status: **CLOSED FOR THE CURRENT v0.30 OFFICE/ANALYTICS REDS**

Evidence source: GitHub Actions run `33582270410`, substantive job `office-analytics-productization`, exact experiment head `27e7e4dae4e497aa15b81b48f9c3873f8a522c7a`, artifact `9828955764` (upload digest `01e5b83b1916e92e80170451f104fbc8c98c6606de05f4e50db4cb770573325d`). The current authoritative branch contains only the subsequent regression ratchet for this gate; it does not change the candidate representation tested here.

This is a **scoped Forge negative result**, not a Foundry thesis and not a universal rejection of federated/level-1 EntropyGraph representations. It answers one concrete question: can the existing dedicated Office/Analytics federated candidate repair the current v0.30 complete-artifact reds while preserving the already required external-competitor, locality, decode-unit, recovery and verification conditions?

## Decision

**No. Retire this candidate family as the current v0.30 repair path for both Office and Analytics.**

The candidate remained strictly smaller and verified-create faster than ordinary ZIP/Deflate-9 and solid Zstd-19, remained strictly smaller than freshly rebuilt genuine canonical r24, matched the repaired historical source identities, and remained inside the frozen locality/decode-unit/recovery/verification constraints. It nevertheless lost materially to the accepted v0.29 complete-artifact floor on both target workloads.

| Workload | Accepted v0.29 | Genuine r24 | Federated candidate | vs accepted v0.29 | vs genuine r24 |
|---|---:|---:|---:|---:|---:|
| Office workspace | 5,954,026 B | 15,445,450 B | 6,428,158 B | **+474,132 B worse** | **9,017,292 B better** |
| Analytics/database | 6,135,172 B | 10,392,496 B | 7,096,260 B | **+961,088 B worse** | **3,296,236 B better** |

Gate summary from the result-bearing run:

- exact target count: pass;
- strict ZIP/Zstd four-way size/create test: pass for both;
- genuine-r24 product floor: pass for both;
- accepted-v0.29 product floor: **fail for both**;
- repaired historical identity: pass;
- <=8x locality: pass;
- <=8 MiB decode unit: pass;
- two-way recovery/fail-closed behavior: pass;
- dedicated candidate identity: pass;
- overall productization gate: **fail**.

## Causal interpretation

This candidate is not merely a little short of the inherited product. Its representation is already excellent relative to conventional external formats and to canonical r24, so further work justified only by those comparator wins would optimize the wrong objective. The inherited v0.29 frontier has already captured substantially more of the available information on these exact workloads.

The shortfalls are large enough to reject ordinary parameter tuning as the default next move: Office needs at least **474,133 B** of additional complete-artifact saving merely to become strictly smaller than accepted v0.29; Analytics needs at least **961,089 B**. Any claimed rehabilitation must also retain the existing four-way, source-identity, locality, decode-unit, recovery and verification passes.

This result therefore closes the current D5 productization path. It does **not** prove that all federated representations are futile, nor that no future representation can reuse parts of this mechanism. It says the present candidate cannot be promoted as the fix for these two current product reds.

## Reopening predicate

Do not rerun or retune this candidate family for the current Office/Analytics reds unless new causal evidence demonstrates a mechanism capable of recovering at least the measured accepted-v0.29 deficits **without borrowing bytes or semantics from any frozen invariant**. Examples of qualifying new evidence would be:

1. a new representation/ownership model that removes a specifically measured >=474,133 B Office or >=961,089 B Analytics cost component;
2. a structural ablation proving that a large charged component of the present candidate is redundant and can be removed generically; or
3. a distinct mechanism that subsumes the useful external-competitor strength while also beating accepted v0.29 on the exact repaired source identity.

A new threshold, corpus identity, comparator setting, relaxed locality/recovery/integrity requirement, or another externally impressive ZIP/Zstd result is **not** a reopening predicate.

## Next Forge implication

Return Office and Analytics to the exact current all-15 gap ledger. Prefer mechanisms that explain why accepted v0.29 is already 474 KiB / 961 KiB ahead of this candidate, rather than polishing the candidate that just failed. If closing either gap requires changing the information ontology rather than a bounded R0-R4 repair, escalate that question to Foundry under the normal Thesis Initiation Gate instead of disguising it as more D5 tuning.
