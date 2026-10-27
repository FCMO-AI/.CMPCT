# O221 — Authenticated random-range charged result

Date: 2026-10-27 UTC. **Scientific installed Reader + out-of-tree adapter only, NOT product credit.**

## Exact evidence / receipt identity

- Preregistered at `9114674cf217dd8b8b463f4f602fa8b91b825fee` before instrument; J24C02 parent `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; unchanged Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.
- Code/test HEAD `ff597d272b6870e13fc56c7ef3879c9552d2a476`, [Actions #40473572590](https://github.com/FCMO-AI/.CMPCT/actions/runs/40473572590) **SUCCESS** (Ubuntu 24.04/Python 3.12.15); [original raw artifact #12718918667](https://github.com/FCMO-AI/.CMPCT/actions/runs/40473572590/artifacts/12718918667); ZIP SHA-256 `346758452a9bcbbd91ba2c3b071c1bfd8d769f0ba7781dc663fcf248f0dba62a`.
- Separately authored second-root original-receipt audit: **PASS**; ZIP CRC, 48 unique observations, 24 matched A/B pairs with matching archive/query/output digests, all eight independently recalculated medians, expected SHA/blob/prereg, 4 signed archives, and 7,098 reported variable-byte held-out cases. This audits the original receipt, **not** a second execution of CMPCT.

## Fully charged Reader session medians (milliseconds)

Both alternatives use the same authentic r24 archive with separate installed Reader processes, 3 repetitions per arm. Timer covers open, ordinary same-index structural admission, candidate checkpoint creation, and all Q ranges; process startup excluded and tracked separately. Source archives are tiny (477–619 bytes) because all refs point to one-byte RAW repeated content.

| Mode | Refs | Q | Baseline wall | Indexed wall | Wall speedup | CPU speedup |
|---|---:|---:|---:|---:|---:|---:|
| S_CHUNKS | 65,536 | 1 | 35.556 | 39.193 | 0.907x | 0.907x |
| S_CHUNKS | 65,536 | 64 | 247.781 | 41.796 | **5.928x** | 5.927x |
| S_CHUNKS | 262,144 | 1 | 136.599 | 149.709 | 0.912x | 0.912x |
| S_CHUNKS | 262,144 | 64 | 988.563 | 150.701 | **6.560x** | 6.560x |
| S_CDC | 65,536 | 1 | 70.779 | 74.453 | 0.951x | 0.951x |
| S_CDC | 65,536 | 64 | 248.109 | 76.293 | **3.252x** | 3.252x |
| S_CDC | 262,144 | 1 | 278.653 | 292.604 | 0.952x | 0.952x |
| S_CDC | 262,144 | 64 | 946.350 | 296.369 | **3.193x** | 3.194x |

Observed median Linux process high-water RSS **delta 0.0 MiB**; this is coarse ru_maxrss, *not* proof of zero memory or byte-level allocation parity. Complete installed Reader warm-session measurements here do not make full product/ZIP/export/release measurements.

**Preregistered scientific decision: `CHARGED_RANDOM_RANGE_HEADROOM`.** Both 262,144-ref/Q=64 modes exceed >=1.5x wall and CPU without exceeding +8MiB observed RSS, and matching exact bytes. **Every Q=1 candidate loses** (roughly 5–9% added time). Original baseline therefore wins for one-off reads.

## Negative evidence, next discriminator and custody

- Indexed performance on heterogeneous multi-codec physical data, mutable archive and journal recovery, Windows/macOS, ZIP64, official entire-product parity, and reader publication paths **unmeasured**. Do not promote as compression/runtime headline, modify evaluators, or silently make eager indexing unconditional.
- The two observed Q values could suggest crossover around 2–3 reads under a linear model, but **Q=2/3 is not observed evidence**. An independently charged Q=1/2/4/8/64 multi-size/multi-codec experiment with adverse lookup geometry is a cheaper next test than production integration. Test ordered cursor as a simpler control if relevant.
- Coordinate with existing Reader product owner [#569](https://github.com/FCMO-AI/.CMPCT/pull/569). The dominant cold-open O(N) admission debt (+25.56/+102.05ms) remains independent and unchanged. No Reader source, format, ABI, release gate or Discovery Engine policy was modified by O221.

**Outcome:** positive bounded scientific option and important one-shot negative; product improvement pending robust workload and owner integration.
