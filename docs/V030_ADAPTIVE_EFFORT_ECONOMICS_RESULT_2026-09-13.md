# v0.30 H-EFFORT-4 Adaptive-Effort Economics Result — 2026-09-13

Status: **durable R0/R3 causal research evidence; `EFFORT_ECONOMICS_STRUCTURE_PRESENT`; no selector, release, representation, locality, or product credit**.

## Evidence identity

- Frozen mission lock: `docs/V030_ADAPTIVE_EFFORT_ECONOMICS_MISSION_LOCK_2026-09-13.md`
- Exact result-bearing source: `02cff111f89f14775eef7f38c7b038bc41643172`
- Hosted workflow run: `34783921598`
- Artifact: `10326390223`
- Artifact digest: `sha256:c99e98bae041b4a588252e88319d89178511e323f8dae9e3773fb1a3523fbad8`
- Referee exit code: `0`
- Historical policy blob remained source-bound by the frozen referee.
- Frozen substrate: the exact ten-workload current15 stable substrate asserted by H-EFFORT-3.

The hosted referee completed its observational census without modifying the encoder or fitting a selector. It measured the same physical pack bytes at levels `1,3,6,9,12,19` with three repeated same-process measurements per level and preserved complete pack-level curves for hostile adjudication.

## Decision

**`EFFORT_ECONOMICS_STRUCTURE_PRESENT`**

Both halves of the frozen H-EFFORT-4 criterion show transferable structure across multiple surfaces:

1. useful later-level byte headroom is strongly concentrated in false-stop recovery packs and is usually exposed by a generic post-stop observation;
2. sequential-ladder CPU futility is strongly associated with a generic pre-terminal state available after the first paid rung, without workload/path identity.

This decision authorizes only a new preregistered minimal Builder experiment. It does **not** authorize a shipping threshold, a workload-specific selector, direct product integration, or reinterpretation of historical evidence.

## Full census

Across **396 physical packs**:

- historical first-worse stopping misses **621,309 B** versus the best measured level in `{1,3,6,9,12,19}`;
- **38 packs** have historical missed headroom;
- all **38/38** missed-headroom packs exhibit later strict recovery after the first worse rung;
- those later-recovery packs account for **621,309 / 621,309 B (100%)** of historical missed bytes;
- level 9 detects later recovery on **26 packs** accounting for **583,921 B / 621,309 B = 93.98%** of all missed bytes;
- after level-9 detection, another **443,859 B** of headroom remains at level 12/19, confirming that recovery detection and continuation depth are separate decisions;
- **328 / 396 packs** have historical cumulative ladder CPU greater than direct level-19 CPU;
- those CPU-dominated packs represent **126,369,244 raw bytes**;
- aggregate ladder CPU is **15.1404 s** versus **18.4129 s** for direct L19 over all packs, so the project must not infer that “direct L19 everywhere” is globally cheaper. The economic defect is pack-conditional.

The last point is important: the local futility signal is real even though the aggregate ladder remains cheaper. A future selector must preserve that portfolio advantage rather than replacing one universal ladder with one universal terminal encode.

## Transfer structure by workload

| Workload | Packs | Historical missed B | Later-recovery packs | L9-visible missed B | Ladder CPU > L19 packs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Developer Repository | 21 | 15,424 | 6 | 0 | 15 |
| Office | 28 | 1,134 | 3 | 77 | 25 |
| Media | 63 | 2,616 | 1 | 2,616 | 62 |
| Analytics | 57 | 414,213 | 20 | 413,594 | 37 |
| Logs / Telemetry | 22 | 0 | 0 | 0 | 22 |
| Incremental Backups | 53 | 288 | 1 | 0 | 28 |
| Incompressible / Encrypted-like | 47 | 0 | 0 | 0 | 47 |
| Many Tiny Files | 4 | 0 | 0 | 0 | 4 |
| ML Artifacts | 37 | 187,634 | 7 | 167,634 | 24 |
| Large Mixed Binary | 64 | 0 | 0 | 0 | 64 |

Headroom recovery is therefore not an Analytics-only effect: later recovery occurs on Developer, Office, Media, Analytics, Incremental Backups, and ML. CPU-dominated ladder behavior appears on every workload in the frozen substrate.

## Headroom-side causal structure

The historical rule is wrong in a very specific way: **every pack on which it leaves measured bytes behind later becomes smaller again after the first strictly worse rung**.

The strongest byte-weighted observation is the frozen level-9 observer:

- total historical missed bytes: **621,309 B**;
- missed bytes on packs where L9 visibly recovers: **583,921 B (93.98%)**;
- remaining post-L9 headroom on those packs: **443,859 B (71.44% of all historical missed bytes)**.

This supports two separate causal facts:

1. non-monotonic effort curves are a real transferable mechanism, not a single-workload anomaly;
2. merely detecting recovery is insufficient — many winning packs still justify later effort after L9.

The fixed H-EFFORT-3 L9 policy failed because it collapsed those two decisions into one. H-EFFORT-4 shows that the right abstraction is a bounded continuation decision, not “one magic rescue rung.”

## CPU-side causal structure

A hostile sign-state audit was performed on the frozen output without fitting a numeric threshold or using workload identity. The observation is the same zero boundary already inherent in the historical incumbent rule:

> after paying level 3, did level 3 fail to become strictly worse than level 1?

Across the frozen substrate:

- all **328 / 328** packs whose cumulative historical ladder CPU ultimately exceeds direct L19 satisfy `L3_bytes <= L1_bytes`;
- among all **360** packs satisfying that generic state, **328 (91.11%)** are eventually ladder-CPU-dominated by direct L19;
- the signal therefore has **100% recall** and **91.11% precision** for the observed CPU-dominated class on this substrate;
- it transfers across all ten workloads; no workload identity, path, fixture hash, extension, or tuned numeric boundary is used.

This is sufficient for H-EFFORT-4's scientific question: generic pre-terminal observations contain material information about ladder futility. It is **not** sufficient to ship the rule. The 32 false positives are real and concentrated materially in Developer, Office, Incremental Backups, and ML; direct terminal effort can also lose density on those packs. A future Builder must therefore prove a bounded decision policy against both byte and CPU regret rather than treating this sign-state as an automatic jump-to-L19 command.

The CPU census also exposes an important accounting fact. Packs whose historical policy reaches L19 necessarily pay earlier ladder levels plus L19, so hindsight comparison against direct L19 contains a structural component. The product question is not whether that hindsight statement is true; it is whether the earlier observations can identify enough of those packs soon enough to avoid material speculative work without harming the false-positive class. H-EFFORT-4 establishes information content, not the final decision rule.

## Strongest hostile review / limitations

### 1. The CPU signal is promising but partially tautological

The no-worse-at-L3 state is causally connected to whether the historical policy keeps spending. Its high observed precision is therefore not equivalent to independent predictive proof. A Builder must preregister its decision surface and transfer court before result-bearing execution, and must be allowed to fail on byte regret or CPU regret.

### 2. Aggregate economics do not support universal L19

Even though 328 individual packs are ladder-CPU-dominated, total ladder CPU across the complete substrate is **15.1404 s**, lower than **18.4129 s** direct-L19 CPU. Large expensive packs where the ladder stops early or avoids terminal work matter disproportionately. Replacing the ladder wholesale would destroy the very compute advantage the research line is trying to preserve.

### 3. L9 is an observer, not an endpoint

L9 exposes 93.98% of byte-weighted missed headroom but still leaves 443,859 B after successful detection. The next policy cannot equate “recovery observed” with “stop here.”

### 4. The result is substrate-scoped

The stable ten-workload substrate provides broad internal structural transfer, including incompressible and large-binary controls, but it is not evidence for every possible file universe or platform. Claims remain scoped until a future Builder survives its own frozen transfer/adversarial court.

### 5. Timing remains same-process hosted evidence

The referee intentionally compares compatible per-pack encode timing boundaries within one hosted process. It is causal research evidence, not fresh-process product performance or release authority.

## What is now falsified

Preserve these negatives:

- “first strictly worse effort means later effort cannot recover” — false;
- “one fixed L9 recovery probe is enough” — false;
- “the historical sequential ladder is always cheaper than direct terminal effort” — false at pack level;
- “direct L19 everywhere is cheaper overall” — also false on this substrate.

The surviving mechanism is therefore **conditional bounded effort allocation**, not another universal effort sequence.

## Authorized next step

A subsequent activation may freeze a **minimal Builder Mission Lock** using only generic observations demonstrated here and must define, before implementation:

- the exact sequential decision points it may use;
- a direct historical-policy control and direct-terminal control;
- a byte-regret budget relative to the measured per-pack oracle;
- a CPU-regret budget relative to both historical ladder and direct terminal effort;
- held-out/transfer surfaces and false-positive accounting;
- preservation of hot/locality semantics and unchanged physical geometry for this mechanism test;
- an explicit kill condition that retires this selector family if the generic policy cannot retain most useful headroom while materially reducing speculative CPU.

Do not derive the shipping thresholds from this result after the fact. The next freeze must choose its policy and gates before its own result-bearing execution.

## Product-credit boundary

H-EFFORT-4 changes no archive representation, reader grammar, filesystem control, integrity, recovery, locality, platform code, release score, version, or historical benchmark. It earns **research-causal credit only**. Product credit requires a separately frozen Builder, hostile transfer, materialized archive evidence, and the repository's full promotion law.