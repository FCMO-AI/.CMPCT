# r25 current-head runtime Forge result

Status: **ACCEPTED D0-D3 FORGE EVIDENCE / CURRENT PRODUCT RUNTIME RED / WHOLE-TREE MEMORY SUPPORTED / RELEASE CREDIT FALSE**

This record preserves the exact current-candidate runtime authority obtained during the unchanged-candidate revalidation wave and turns it into an explicit Forge gap ledger. It changes no product source, archive grammar, comparator, corpus, timing band, RSS band, locality limit, integrity/recovery rule or release law.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact measured source head: `5a316cdce29350a418d9c01cdc644ebec73bc21f`;
- candidate fingerprint: `953a94e15662a5bee5e92596806a4c33cb5bce26a243a63121f7763bdd423e11`;
- workflow: `CMPCT v0.30 runtime promotion gate`;
- run: `33772287627`;
- release-performance job: `100711457364`;
- ordinary paired-runtime artifact: `9901138440`, ZIP digest `sha256:b144bcae24cba6ac0fa373b034e8b159b1f28b5d844b0e91340872940ee0bb49`;
- whole-process-tree companion job: `100711457252`;
- whole-tree artifact: `9901186350`, ZIP digest `sha256:5c3d21f3112fe8eb1675a41b6a76fe8414269f16bc077f266d7aef4599371f7e`;
- release credit: **false**, because the frozen runtime gate failed.

The ordinary gate used two balanced fresh-process pairs per workload (`v029 -> v030`, then `v030 -> v029`) and preserved the frozen `1.10x` median / `1.25x` per-workload create+extract bands. No size regression occurred.

## Exact product result

| workload | v0.30 selected representation | v0.30 bytes | accepted v0.29 bytes | median create ratio | median verify ratio | median extract ratio |
|---|---|---:|---:|---:|---:|---:|
| Shifted | PrefixGraph | **1,700,666 B** | **1,723,056 B** | **1.297580x** | 0.488823x | **0.834727x** |
| Logs | logs-inverse | **3,550,342-3,550,345 B** | **3,550,609 B** | **0.008981x** | 0.831655x | **1.332975x** |
| ML | G0-G4 overlay | **13,674,823-13,674,824 B** | **13,836,439 B** | **1.369527x** | **1.844365x** | **2.211856x** |

Frozen aggregate runtime result:

- median workload create ratio: **1.297580x** — red;
- maximum workload create ratio: **1.369527x** — red;
- median workload extract ratio: **1.332975x** — red;
- maximum workload extract ratio: **2.211856x** — red;
- ordinary worker-self RSS maximum ratio: **2.081126x**, but this is not the final product-memory interpretation because the paired historical comparator spawns substantial child work that `RUSAGE_SELF` does not charge symmetrically.

The same-run whole-process-tree companion corrects that memory-accounting asymmetry while retaining the same target set and no-size-regression requirement. Its maximum decisive whole-tree RSS ratio is **1.000000x**, so memory passes the unchanged **1.25x** ceiling. Its externally observed timings are descriptive only and do not supersede the ordinary frozen timing gate.

Therefore the current blocker is **runtime latency, not current whole-process-tree RSS**.

## D1-D3 attribution — Shifted

Both repetitions select PrefixGraph and preserve a real compression win. The r25 tournament itself costs **38.217-38.262 s** inside a **38.291-38.336 s** complete pack.

Nested same-run timings show:

- PrefixGraph child semantic-owner build: **6.190-6.484 s**;
- G0-G4 candidate after the PrefixGraph child exits: **31.578-31.918 s**;
- of that G0-G4 time, its shared accepted-v0.29 candidate build alone costs **28.964-29.317 s**;
- G0-G4 ultimately selects its v0.29 fallback and loses the final r25 tournament to PrefixGraph by about **22.7 KiB**.

The shipping lifetime barrier is working as designed for memory: the PrefixGraph child must exit before G0-G4 begins. The exported debt is that exact serialization forces the product to pay the full losing G0-G4 audition after an eventual PrefixGraph winner has already been materialized.

This does **not** authorize deleting G0-G4. Its bytes are still part of the exact candidate tournament and cannot be gifted away in product evidence. It does establish a strong R1/R2 target: find a sound, cheap way to prove that G0-G4 cannot beat the already materialized PrefixGraph candidate in this regime, or reduce the losing G0-G4 audition cost without reintroducing simultaneous-lifetime RSS debt.

## D1-D3 attribution — ML

PrefixGraph is ineligible (`file-size-ceiling`), so ML is a separate mechanism family and must not be conflated with the Shifted scheduler debt.

The exact G0-G4 candidate wins by roughly **161.6 KiB** versus accepted v0.29, but:

- shared inherited v0.29 candidate construction: **20.181-20.442 s**;
- complete G0-G4 portfolio construction: **28.010-28.511 s**;
- incremental overlay/productization work: roughly **7.8-8.1 s**;
- transformed records: **9** (8 lane + 1 delimiter);
- complete product create ratio: **1.369527x**;
- strong-verify ratio: **1.844365x**;
- extract ratio: **2.211856x**.

The ML compression win is therefore preserved under Breakthrough Rehabilitation: the byte gain is not to be tuned away merely to make timing green. Forge must attack the exported overlay/read debt. The already-frozen ML native-FFI/shared-record-cache oracle is directly relevant to the verify/extract side and should be allowed to decide before inventing another reader family.

## Logs

Logs create is decisively green, but extract remains **1.332975x** versus the frozen v0.29 comparator. This is consistent with prior inverse-codec attribution showing material gzip ownership while the simple Python single-member `zlib` wrapper fast path was retired. No nearby wrapper variation is reopened by this result.

## Whole-tree memory reconciliation

The companion measurement reports:

- Shifted max pack whole-tree RSS ratio: **0.933578x**; extract **1.000000x**;
- Logs max pack whole-tree RSS ratio: **0.635844x**; extract **1.000000x**;
- ML max pack whole-tree RSS ratio: **0.725571x**; extract **1.000000x**;
- global maximum: **1.000000x**.

This is compatible with the accepted PrefixGraph isolation S6 and external whole-tree v2 authority. The ordinary worker-self RSS red must not be used to reopen process isolation or weaken the release ceiling; the child-aware accounting is the correct causal metric for the shipping lifetime boundary.

## Forge decision

**`CURRENT_HEAD_RUNTIME_DEBT_SPLIT_BY_OWNER`**

1. **Shifted:** preserve PrefixGraph and its process-lifetime memory win; attack the mandatory losing G0-G4 audition/exported scheduling debt. Do not re-overlap the two large candidates merely to recover wall time, because the lifetime barrier is evidenced product memory behavior.
2. **ML:** preserve the G0-G4 byte win; attack overlay creation and especially verify/extract cost. Consume the frozen ML native-FFI oracle before starting a competing reader intervention.
3. **Logs:** preserve the extremely fast create path; continue only causally distinct inverse-decode interventions after the retired Python wrapper family.
4. Do not aggregate these three debts into one generic optimization. They have different semantic owners and different lowest-sufficient interventions.
5. Runtime release authority remains **red** until a same-fingerprint successor clears the unchanged bands.

## Reopening / escalation law

- Shifted concurrency may be reconsidered only with new evidence that the simultaneous whole-process-tree RSS ceiling still passes under the exact shipping composition; historical in-process overlap is not sufficient.
- G0-G4 may be skipped or curtailed only if a product-valid lower bound/admission proof makes its inability to beat the current PrefixGraph candidate explicit without gifting representation bytes or required selection metadata.
- ML's byte win may be retired only if a lower-carrying-cost mechanism matches or exceeds its complete-product saving under all existing correctness/locality/recovery requirements, or if the Forge lease expires after the allowed reader/productization interventions fail.

## Strongest self-critique

The nested timings establish ownership, not yet a shipping fix. In particular, "PrefixGraph already exists" is not a legal reason to omit G0-G4: without a sound bound, the product would no longer know whether a smaller G0-G4 archive existed. The next Shifted experiment must therefore distinguish **oracle headroom** from a **deployable stopping proof** and account for whatever bytes/control metadata the deployable proof would require.
