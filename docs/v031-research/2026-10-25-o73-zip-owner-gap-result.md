# O73 — Charged physical gap-separated ZIP owner oracle: first hosted result

Date: 2026-10-25 UTC. **Research evidence only; no product, benchmark gate or release credit.** Preregistered before test implementation at `fe0682313a0fc367430302e28ae52e081aa26ace`. Base O70 PR #426 HEAD `887e419b4ccbef06ac21a7920e06f55743333664`, actual installed Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Exact result-bearing candidate HEAD `b473122e3700b2833c84e9f99032ee46f46d4692`.

## Source-bound original evidence and verdict

Actual [GitHub Actions O73 run 40182374529](https://github.com/FCMO-AI/.CMPCT/actions/runs/40182374529), 1/1 scientific test PASS, [original raw artifact #12594566892](https://github.com/FCMO-AI/.CMPCT/actions/runs/40182374529/artifacts/12594566892). Artifact ZIP SHA-256 `4b9247b3e9c25a1b25fc6a0f2652be9034a0d6d6f688ca9628af76ba71b56ed5`, raw `o73-evidence.json` SHA-256 `92e0e2392893d44949f5e0e033c2db054048caf350ae5e1eb2b12ec64278554a`. An independent offline consumer recomputed medians, arm identifiers, deterministic output SHA consistency, selected-storage kind, prospectively frozen ratios and negative-control consistency: **105/105 checks PASS**.

**Prospective O73 primary decision: `CREDIBLE_SPLIT_HEADROOM` (research only).** The exact preregistered conjunction survived all four primary requirements on 6-large/2-small: >20× physical decoded-work reduction, <2× creation wall, <=1% complete-byte debt, authentic exact read/verify/extract. The original, individual and split variants use identical physical source input.

| 6-large / 2-small, same source | Original one S_PACK | All individual VZIP | O73 large S_PACK + small VZIP |
|---|---:|---:|---:|
| Complete archive bytes | **790,524** | 792,648 | **791,193** |
| Create wall median, ms | **9.295** | 53.383 | **9.441** |
| Create CPU median, ms | **9.295** | 53.384 | **9.442** |
| Small ZIP 64-B read wall, µs | 417.789 | **37.855** | **39.534** |
| Actual decoded physical blob bytes | 789,722 | **1,148** | **1,148** |
| Selected physical storage kind | S_PACK | S_VZIP | S_VZIP |
| Full authentic verify/read/extract | PASS | PASS | PASS |

Compared with shipping: **687.911× less physically decoded work** on selected 64-B small ZIP read; about **10.57× less selected-read wall**; **+669 complete bytes (+0.0846%)** and **+0.146 ms (+1.57%) create**. Compared with all-individual oracle: **−1,455 bytes**, **5.65× faster creation**, nearly equal observed small-read wall (O73 remains ~4.4% slower than all-individual on this selected sample). **This is a creator/locality frontier gain, not full Pareto domination of shipping** because size and create regress slightly.

## Held-out structural perturbations and controls

| Corpus | Shipping archive bytes | Split archive bytes | Split create / original | Selected decoded work shipping / split | Outcome |
|---|---:|---:|---:|---:|---|
| 5 large + 3 small | 660,329 | 661,322 | 1.111× | 574.598× | Primary-style conjunction positive |
| 7 large + 1 small | 920,723 | 921,067 | 1.194× | 801.224× | Primary-style conjunction positive |
| 8 homogeneous large, **no gap** | 1,050,880 | **1,050,880** | 0.976× | **1.000×** | Exact physical archive SHA equal to shipping; no split |

The homogeneous control prevents credit for an oracle that changes unrelated files. The 5/3 and 7/1 holdouts distinguish the mechanism from an eight-file fixture-specific two-small optimization. All four corpora had six materialized builds (`shipping, split, individual, individual, split, shipping`) and eight selected read observations per policy; all observed source SHA fingerprints were stable. A 16× adjacent *physical source-size* gap is the only experimental split rule; no filename, content identity or private corpus label is read.

## Negative evidence, alternative explanations, cost debt

The experiment selected structurally easy *size-separated* synthetic ZIPs. Larger payloads are independently pseudo-random and do not test high *cross-group* redundancy, high-compression or mutation. It uses repeated objects in **one installed Python process**, so different process startups, cold page caches, RSS/allocator lifetime, OS disk IO, full extraction throughput, Windows/macOS and arbitrary filesystem cases are unmeasured. The strategy adds a separate owner, two VZIP recipes and indexes, and can cost more in memory/CPU on other corpora. The original fixed corpus favored O73 and a different generic admission rule could win or lose; no claim of universally profitable partitioning.

In particular the exact shipping archive loses **zero-byte parity** on the positive corpus because O73 adds 669 B. This is **not** a release-candidate size no-regression result; O73 only proves a valuable tradeoff. Before a product integration, compare a simpler **two S_PACK-owner** control that may avoid the tiny VZIP parse overhead, test high-redundancy hostile input, charge full memory/temp IO and seek credible generic admission with fallback. A hidden extra payload/proof byte must not be credited as free.

## Reproducibility / continuation

The preregistration, whole source-bound oracle, and Actions runner are included in this PR. Original raw 24 complete archive builds, 3 arms × 4 structural corpora × 2 repeats; per-arm read samples and SHA are in the artifact. Source build ID, positive AND negative controls survive future HEAD changes. The original O70 result remains authoritative for its original parent/input; O73 does not retroactively replace it. No production files, benchmark artifacts, release policy, Discovery Engine STATE.json, format, limits, or comparators were modified.

**Decision:** keep this as a measured promising representation/physical-ownership seed with **explicit +669-B / +0.146-ms debt** on the primary corpus. The cheapest stronger control is two S_PACK owners; only if that survives prospective costs should the project consider a bounded product admission policy.
