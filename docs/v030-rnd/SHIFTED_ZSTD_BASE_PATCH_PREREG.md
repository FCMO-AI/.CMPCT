# Shifted R4 native base+patch preregistration

Status: research-only decision record. No release credit.

## Referee / pre-mortem

**Strict target:** every frozen row must be strictly smaller and strictly faster to create than ZIP/Deflate and solid Zstd-19 while retaining the accepted v0.29 byte floor and all product invariants.

**Target family:** near-duplicate regular-file sets with large shared bodies and sparse inserted/replaced regions. The decisive frozen instrument is `resemblance_hostile_v1/01_shifted_versions`, but the representation code does not receive the workload name, corpus hash, or benchmark path.

**Current exact size gap motivating the test:** shipping CMPCT `1,701,341 B` versus solid Zstd-19 `1,694,674 B`, a `+6,667 B` strict size red. ZIP is `30,283,112 B`, so the relevant size boundary is Zstd-19. Recent exact shadow evidence has creation already on the winning side for Shifted; the new family must preserve that margin rather than export the size fix into creation time.

**Diagnosis:** D4 representation/physical-layout floor. Existing PrefixGraph/cluster/dictionary variants are saturated as primary directions. Active triggers: S2 repeated low-yield work, S3 family retirement, and S4 exported-cost loops. Minimum justified radicality: **R4**.

**Research Priority Score: 82/100.** Breakdown: necessity 15/15; upside 17/20; root-cause fit 15/15; generality 6/10; information gain 12/15; decisive-test efficiency 8/10; survival path 5/10; simplicity/portability 4/5. This is admissible despite reader debt because it directly changes the representation that sets the losing size floor and can be falsified on one bounded workload.

**Hypothesis:** encode one deterministic structural anchor once and represent every other member as a native Zstd patch from that anchor. This is not PrefixGraph, a shared dictionary, or a solid cluster: the physical semantic unit is an exact reconstruction dependency (`base + patch -> member`). If sparse edits are the true causal structure, patch bytes should be substantially smaller than storing/auditioning whole candidate bodies.

**Simplest strong control:** solid tar+Zstd-19 already exploits long-range redundancy and is the strict size comparator. ZIP/Deflate-9 remains the strict creation/size comparator. No weaker custom-delta baseline receives promotion credit.

**Strongest failure explanation:** solid Zstd may already capture nearly all cross-version redundancy inside one window, leaving a base+17-patch container larger after per-patch framing. Separately, serial native patch construction may preserve size but lose the creation contract. Either failure is enough to deny promotion.

**Invariants:** exact tree; one complete artifact; SHA-256 per member; bounded/safe relative paths; source scan, anchor selection, hashing, patch construction, framing and publication inside candidate creation time; no benchmark identity in representation/admission; no selector, canonical grammar, recovery, locality, native/Android, or release changes from this oracle.

**Disproof condition:** no tested structurally identical fixed policy is simultaneously smaller than accepted v0.29, ZIP, and solid Zstd-19 and faster to create than both ZIP and Zstd-19 after exact reconstruction. A size-only result is not a win.

**Materiality threshold:** cross the current `+6,667 B` Zstd size gap while retaining the already-green external creation margins. Because the row is near the boundary, crossing the exact strict boundary is sufficient even if percentage gap closure is not otherwise meaningful.

## Builder / decisive instrument

`benchmarks/v030_shifted_zstd_patch_oracle.py` builds a self-describing single artifact with one deterministic median-size/content-hash anchor, native Zstd-19 storage for that anchor, and native Zstd `--patch-from` bodies at levels 1/3/6/9. Each arm is charged independently; level search cost is not hidden inside a purported selected candidate. The reciprocal decoder reconstructs every file and checks size/SHA/tree identity.

The exact-head workflow is `.github/workflows/v030-shifted-zstd-base-patch-oracle.yml`. It preserves exact receipts across unrelated pushes and grants `release_credit=false` regardless of outcome.

## Hostile reviewer / post-mortem decision law

- If at least one arm is a strict five-way win, decision = **PROMOTE_NEXT_PREREQUISITE**. Next test: content-agnostic generic admission plus locality/read-amplification and corruption/recovery semantics before any canonical writer integration.
- If size wins but creation loses materially, decision = **REHABILITATE_DEBT** only if profiling shows a bounded native construction cost owner sufficient to cross the time gap; otherwise **RETIRE_FAMILY**.
- If all arms remain above solid Zstd-19 in size, decision = **RETIRE_FAMILY** for one-anchor Zstd patching. Do not tune more levels. Escalate only if the receipt exposes a specific anchor-coverage failure that justifies a bounded multi-base reconstruction family rather than scalar parameter search.
- If exact reconstruction or framing/integrity fails, decision = **RETIRE_FAMILY** unless the failure is demonstrably harness-only.
