# ONE-G0.2 — epoch-min starvation transfer

**Status:** generator-distinct semantic transfer passed; advances to native cost falsifier  
**Exact source:** `9082f64fde6960783a6346bf4ffcadd2e4e2989c`  
**Workflow:** `33946923624`  
**Job:** `101254605637`  
**Artifact:** `9963634238`  
**Artifact digest:** `sha256:b6c7cbf6a0e99853dcd1af409e7a4d0e107191426cc12030c3b94d5cccf0d512`  
**Experiment:** `ONE-G0.2`

## Mission lock

Two earlier rescue implementations preserved the shifted/starved relation but exported unacceptable compute debt: exact edge replay rebuilt 4,096 Gear states per edge, while a continuously maintained 64-position hierarchy roughly doubled large-input elapsed. This Builder tested whether the hard transfer actually requires an exact sliding minimizer or only a stable rightmost minimum over consecutive starvation epochs.

The candidate keeps one scalar rightmost minimum before activation. At the fixed 4,096-position starvation activation it emits that minimum and resets. While active it emits/resets every 4,096 eligible positions and emits the final partial epoch at exit/EOF. It has no queue, byte-history replay or block hierarchy.

Frozen disproof reused the exact generator-distinct cohort: the first 12 4,096-byte seed bases in `[0,4095]` with zero qualifying sparse Gear anchors, with insertion lengths 1, 8 and 31. Any row where the mature full minimizer owned opportunity beyond fixed+sparse cheap observers had to preserve **100%** of that opportunity.

## Result

Artifact decision: `epoch_min_transfer_survives`.

There were **35 hard-rescue rows and zero losses**. On every hard row:

- fixed opportunity: 0 B;
- sparse Gear opportunity: 0 B;
- mature full-minimizer opportunity: **4,096 B**;
- epoch-min opportunity: **4,096 B**;
- pulses: **2**;
- verification reads: **128 B**;
- extension proof reads: **8,064 B**.

The same `seed=106, insertion=8` control where the full minimizer itself had 0 B opportunity also produced 0 B under epoch-min and was correctly excluded from the 35 hard rows.

## Causal interpretation

For this independently generated shifted/starvation family, the information needed to recover the relation is materially simpler than a sliding 4,096-position minimizer. The useful source and target nominations survive when each starvation epoch contributes only its scalar rightmost minimum.

This explains why cold rescue failed 35/35 while scalar epoch-min succeeds 35/35: cold rescue discarded the historical source epoch before starvation became observable; epoch-min retains a tiny sufficient statistic from that history without retaining the whole window or exact queue.

The result is therefore not a threshold win. It changes the causal model of what discovery state appears necessary for this high-value shifted relation.

## Hostile review / claim boundary

This is semantic transfer evidence only. A scalar compare/update on every eligible byte still has an always-paid CPU cost and must be measured natively. The 35-row cohort is deliberately independent of the candidate result but is still a targeted starvation family, not broad Addressable Opportunity Mass evidence.

No reader/wire, stored-byte, product-speed, v0.29/v0.30 comparator, release, access, integrity, recovery or portability authority is created.

The mature promoted selector remains authoritative until native cost and broader opportunity transfer both pass.

## Next decisive test

Run the frozen native epoch-min A/B against the promoted 8 KiB selector. If native cost passes, immediately test the epoch candidate on the full existing minimizer marginal-yield corpus and additional unfiltered shifted/versioned cohorts. The key question is then whether the scalar epoch candidate captures the mature minimizer's rare positive marginal opportunity without introducing false opportunity debt elsewhere.
