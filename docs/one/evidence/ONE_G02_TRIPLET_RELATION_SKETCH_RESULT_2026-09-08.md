# ONE-G0.2 triplet block relation sketch result — 2026-09-08

**Decision:** `ADVANCE_TRIPLET_RELATION_SKETCH`  
**Exact source:** `72293a19001c6e10f1a63342736a38c6973e3231`  
**Run:** `34310588470`  
**Job:** `102336255448`  
**Artifact:** `10088208172`  
**Artifact digest:** `sha256:0b4d1f05ca90998e7e2bbd5025e289731eb9c39be57bbf2d9856d020945c81e5`

## Exact evidence truth

The exact-head workflow completed successfully. Exact checkout/frozen-law binding passed, all decision-law tests passed, and the frozen 24-cell falsifier itself passed. Therefore every frozen promotion condition in `ONE_G02_TRIPLET_RELATION_SKETCH_PREREG_2026-09-08.md` was satisfied:

- exact unique 24-cell matrix;
- exact family-oracle decisions on all rows;
- identical baseline/candidate run+reuse evidence;
- exactly 1.0x charged forward source scan;
- median candidate/baseline wall <=1.20x and CPU <=1.20x;
- no row >1.35x wall or CPU;
- every 1 MiB row >=250 MiB/s on both wall and CPU accounting.

The artifact remains the row-level timing authority. This receipt does not invent row values unavailable from the current connector surface.

## What advanced

A relation nomination substrate can reuse the existing 64-byte reuse-fingerprint cadence without a second per-byte relation state machine. Each completed block contributes only three content-derived probes. A local relation vote exists only when all three agree on the same non-zero value, and a relation is nominated only when that same value wins across >=7/8 eligible blocks.

This preserves the required coarse add8/XOR positives and rejects the random/compressed/false-pattern controls, including the add8->XOR cross-family alias that invalidated fixed positional 1/4 sampling.

No stored ONE representation changed. These are writer-internal nominations only; exact verification remains mandatory before any Law is stored.

## Negative predecessor

The preceding eight-probe block sketch at source `14b3dbe9b3a1b2ffcd7c051df9815ed27d4fb184` did not advance. Its exact binding and decision-law tests passed, the frozen 24-cell falsifier failed, and artifact `10088074187` (`sha256:63689340c885b6752257a47f4473b95ce281ceac657304dfd005f6ad9afb5bc8`) was retained. The exact artifact remains authoritative for its row-level decision; the current connector could not decode the ZIP payload. The implementation had substantially heavier per-block bookkeeping (eight probes plus local vote histograms), which motivated this separately preregistered triplet rehabilitation rather than any threshold relaxation.

## Non-claims and next gate

`ADVANCE_TRIPLET_RELATION_SKETCH` is not a compression promotion by itself. It establishes a credible cheap relation-nomination substrate on the current mechanism matrix. The next decisive experiment must connect:

`fused run/reuse observer -> triplet block relation nomination -> exact maximal span growth -> generic ONE Program`

and charge false nominations, exact proof bytes, writer wall/CPU, retained state/peak memory, node/control bytes, final wire bytes, and bits eliminated per extra CPU second. Transfer must include sparse/late relations, arbitrary phase changes, wrong-relation near misses, incompressible/random, already-compressed/media-like and temporal/versioned cases. A nomination that cannot pay for its exact proof and final bytes saved must not survive simply because this substrate is cheap.
