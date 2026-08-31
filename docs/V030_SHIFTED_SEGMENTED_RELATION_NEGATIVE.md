# v0.30 Shifted segmented relation ownership — terminal negative

Status: **research-only terminal negative**. This document grants no release credit and changes no production selection policy.

## Question

After the global joint edit-stream representation failed the hard decode-unit/locality laws and independent CDC ownership destroyed too much long-range compression context, could the same relation-aware edit idea succeed when split into multiple lawful content-derived segments?

The decisive condition was deliberately stronger than a local improvement: before paying framing/publication cost, the compressed payload itself had to beat the accepted v0.29 floor, ZIP/Deflate, and solid Zstd-19 while every segment stayed within the <=8 MiB decode-unit and <=8x locality laws. Benchmark names, paths, and frozen-pack identities were forbidden as grouping inputs.

## Referee / pre-mortem

The strongest failure prediction was that segmentation could repair legality without repairing the representation's entropy economics. Splitting one huge edit stream into lawful units necessarily restores boundaries that can destroy cross-member compression context. A representation that is already several megabytes behind solid Zstd-19 at payload level cannot be rescued by archive framing; framing is non-negative cost.

The experiment therefore had to distinguish two questions exactly:

1. Can content-only segmentation make the representation legal?
2. If legal, does its payload have enough capacity to beat the strict size frontier before framing?

## Builder / decisive instrument

Exact source commit: `54ed7116eb18d4fe5ec8d0f17f73a6f15f796c9a`

GitHub Actions run: `33446204282`

Proof job: `segmented-relation-floor` (`99667035977`)

Artifact: `v030-shifted-segmented-relation-54ed7116eb18d4fe5ec8d0f17f73a6f15f796c9a`

The run first executed the dedicated structural ratchet. Fifteen tests passed, including exact partition coverage, per-segment decode/locality law, path/name independence of grouping, and fail-closed handling of an intrinsically oversized singleton.

The exact frozen Shifted measurement then reported:

- representation admissible: **yes**
- relation-aware segments: **3**
- compressed payload total: **5,372,880 B**
- solid Zstd-19: **1,694,674 B**
- payload / Zstd-19: **3.17045x**
- deficit versus Zstd-19: **3,678,206 B**
- payload capacity positive: **no**
- terminal decision: **RETIRE_FAMILY**

Every emitted segment satisfied the <=8 MiB decode-unit and <=8x locality laws. Relation discovery and grouping were charged inside creation time. The representation used no benchmark identity and claimed no framing or release credit.

## Hostile reviewer / post-mortem

The result is useful precisely because legality succeeded. It removes the ambiguity left by the one-global-unit experiment: the failure is no longer merely that the semantic unit was too large. Even after the representation is partitioned into lawful content-derived units, its payload is more than three times the size of solid Zstd-19 before any archive framing, metadata, integrity, publication, recovery, selector, native, or Android cost is added.

The strongest surviving criticism is that the relation signal itself is still real; earlier exact CDC work found substantial repeated raw structure. What has now failed is a broader ownership model: independently compressed relation/edit units, whether globally illegal or lawfully segmented, do not preserve enough compression context to compete with the solid stream. This does **not** prove all relation-aware representations impossible. It does prove that another segmentation threshold, cluster count, or edit-unit size sweep is low-value unless it changes the ownership/context model itself.

## Domination audit

- strict target: **15/15 workloads strictly smaller and faster to create than ZIP/Deflate and solid Zstd-19**
- diagnosis: **D4 — representation/ownership red**
- minimum justified radicality: **R4**
- saturation triggers: **S1, S2, S3, S4**
- Research Priority Score of the tested hypothesis: **99**
- measured gap change: legality improved from the global stream's 73,181,641 B / 39.29x violation to three lawful units, but the legal payload remained **+3,678,206 B versus Zstd-19**
- strongest surviving self-critique: relation structure is genuine; the failed component is independent edit-unit ownership and lost long-range context, not the existence of reusable structure
- terminal decision: **RETIRE_FAMILY**
- next decisive test: an R4 representation that preserves one strong compression context while encoding bounded local relation references, with an optimistic payload lower bound before any full construction. Do not run another segment-size sweep without a new ownership law.

## Engineering consequence

Retire the segmented relation-owned edit-stream family. The next Shifted invention must change the compression-context/ownership architecture, not merely retune segmentation. Candidate directions should be rejected cheaply with exact optimistic floors whenever possible, and any survivor must remain content-agnostic and obey the existing locality, decode-unit, integrity, recovery, timing, v0.29, native, Android, and final release laws.
