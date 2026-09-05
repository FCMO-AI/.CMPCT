# ONE-G0.2 — edge-pulse historical replay transfer

**Status:** generator-distinct semantic transfer passed; advances to native cost falsifier  
**Exact source:** `cc21c29e39913903c3d9450c8033cf5de43a2e25`  
**Workflow:** `33946566275`  
**Job:** `101253623260`  
**Artifact:** `9963512662`  
**Artifact digest:** `sha256:4fe423b9a7d37f04251696b05b3dc5df86a6e88e261e0a81592b2422c7c11201`  
**Experiment:** `ONE-G0.2`

## Mission lock

The complete compact starvation rescue reversed the old large-input timing debt, but remained 2.965x slower than the promoted selector on the 8,193-byte hard transfer row. Previous cold/late rescue had already been rejected because activating only after starvation discarded the historical rightmost-min state and lost 35/35 independently generated hard opportunities.

The reopening predicate explicitly allowed bounded replay if the historical information and total cost were charged. Edge-pulse rescue therefore retains the bounded history and reconstructs the rightmost-min candidate only at two content-derived boundaries of a starvation episode: activation and episode exit/EOF. It does not maintain the exact minimizer queue continuously between those edges.

Frozen disproof required the same generator-independent transfer contract used by the earlier late-rescue falsifier: the first 12 4,096-byte pseudorandom bases in seeds `[0,4095]` with zero qualifying sparse Gear anchors, insertion lengths 1, 8 and 31, and **100% preservation of full-minimizer opportunity on every hard row**. Any hard-row loss rejected edge-pulse rescue as a complete small-case replacement.

## Result

Artifact decision: `edge_pulse_transfer_survives`.

There were **35 hard-rescue rows** and **zero losses**. Every hard row retained the full-minimizer opportunity exactly. Typical rows:

- input: 8,193 / 8,200 / 8,223 B;
- fixed opportunity: 0 B;
- sparse Gear opportunity: 0 B;
- full minimizer opportunity: **4,096 B**;
- edge-pulse opportunity: **4,096 B**;
- pulses: **2**;
- replayed positions: **8,192**;
- exact verification reads when opportunity existed: **128 B**;
- extension proof reads: **8,064 B**.

One generated seed/insertion combination (`seed=106`, insertion=8) was not a hard row because the full minimizer itself had 0 B opportunity; the experiment correctly did not count it as a rescue success or loss.

## Causal interpretation

The earlier 35/35 cold-rescue failure did **not** mean continuous minimizer maintenance is necessary. It meant that the useful candidate depends on historical state that must survive until starvation becomes visible. Once that state is recoverable through bounded history, two event-edge reconstructions are sufficient for all 35 tested shifted/starved transfer rows.

This is concept compression over the rescue path: the encoder need not preserve a continuously evolving reader-visible or discovery-visible minimizer mechanism merely to recover this class of shifted relation. It can preserve the bounded historical sufficient material and reconstruct only when the causal starvation episode demands it.

## Hostile review / claim boundary

This result is semantic transfer only. It does not prove the native implementation is faster. Two 4,096-position replays still mean 8,192 reconstructed states on an ~8 KiB input, so the small-case CPU bill could remain too high even after eliminating per-position queue maintenance.

It also does not show broad opportunity equivalence to the full minimizer outside the selected starvation transfer family. Edge-pulse is therefore a **seed**, not a replacement for the promoted 8 KiB selector or full-minimizer discovery knowledge.

No reader/wire, stored-byte, product-speed, v0.29/v0.30 comparator, release, access, integrity, recovery or portability authority is created.

## Next decisive experiment

Implement the edge-pulse recurrence as a native microkernel with only the 4,096-byte history + Gear table state, validate emitted pulse positions against an independent recurrence, and charge elapsed time against both the promoted selector and complete compact rescue on random, already-compressed, repeated, shifted and hard-transfer inputs.

The next native gate should require material closure of the 8,193-byte timing debt and no large-input regression. If native edge-pulse is cheap, move immediately to broader generator-distinct opportunity transfer; if it is still expensive, retire this scheduling shape rather than tuning the 4,096 semantic constants.
