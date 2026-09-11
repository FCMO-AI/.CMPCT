# ONE-G0.2 native sampled multi-Law carrying cost — preregistration

**Status:** frozen before hosted result.  
**Parent negative:** exact source `86ce1618ef2433f26c568ebc951d11d5b954e4ac`, run `34302722535`, `HOLD_NATIVE_MULTI_LAW_CARRY`.

## Mission lock / hypothesis

The full native multi-Law observer is semantically useful but its per-byte add8/XOR histogram updates cost too much: exact hosted evidence reported median candidate/baseline wall and CPU ratios about 1.345x, above the frozen 1.25x carrying-cost gate.

Hypothesis: relation nomination can retain the full observer's decisions while updating relation histograms on only one quarter of positions. The sampling law is deterministic: positions `p & 3 == 0`. Run/reuse observation and the lag ring remain one-pass and unchanged.

This is not random subsampling. It uses a conservative support bound. The full gate nominates a nonzero relation at >=7/8 support. If at most 1/8 of all positions violate that relation, then even if every violating position is concentrated onto a 1/4 sample grid, at least half of sampled positions still carry the true relation:

`(1/4 - 1/8) / (1/4) = 1/2`.

Therefore the sampled gate nominates the best **nonzero** add8/XOR bin at >=1/2 sampled support. Zero remains excluded because it belongs to Fill/reuse evidence. Exact downstream proof remains mandatory.

## Causal comparison

Three rotating paired arms use one C translation unit and identical Python->ctypes source-copy / FFI boundaries:

1. baseline native run+reuse observer;
2. previously tested full native run+reuse+add8+xor observer;
3. sampled native observer, identical except add8/xor histograms update at 1/4 of positions and use the conservative 1/2 nomination threshold.

Compilation/loader cost is outside timing because a product native observer would ship built. Source bytes are still scanned exactly once. No downstream Law synthesis is included; this gate isolates carrying cost.

## Frozen matrix

64 KiB / 256 KiB / 1 MiB × the existing eight multi-Law families plus:

- `add8_phase_poison`: a true 7/8-support add8 relation whose entire 1/8 exception budget lies on sampled positions;
- `xor_phase_poison`: the analogous lag-64 XOR relation.

30 cells, 21 rotating repetitions.

## Advance law

`ADVANCE_NATIVE_MULTI_LAW_SAMPLED_CARRY` only if all hold:

- exact unique 30-cell matrix;
- full and sampled decisions equal the promoted Python semantic oracle on every row;
- baseline run/reuse decisions/support/table occupancy equal both richer arms;
- sampled source scan remains exactly 1.0x input;
- sampled/baseline median wall <=1.20x and median CPU <=1.20x;
- no sampled row >1.35x baseline on wall or CPU;
- on the four relation-bearing families (`add8_ramp`, `xor_chain`, and both phase-poison controls), median sampled/full wall <=0.90x and CPU <=0.90x;
- every 1 MiB sampled row >=250 MiB/s in both wall and CPU accounting.

Any semantic mismatch invalidates. A performance miss is HOLD; thresholds do not move.

## What success would mean

Only that sparse deterministic relation evidence is a credible native carrying strategy. It would not prove general relation discovery, final writer economics, density transfer, selective access, or Genesis superiority. The next gate would integrate nomination with exact span growth and charge bytes eliminated per CPU second.
