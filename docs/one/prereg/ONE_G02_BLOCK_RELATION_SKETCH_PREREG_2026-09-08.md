# ONE-G0.2 block-cadence relation sketch preregistration

**Status:** frozen before hosted result.  
**Experimental version:** ONE-G0.2  
**Primary branch:** `research/cmpct1`.

## Mission lock

The per-byte native multi-Law observer preserved useful relation information but cost ~1.34x the run+reuse baseline. Fixed 1/4 positional sampling reduced some work but introduced an add8->XOR alias and still cost ~1.39x baseline. The next admissible reopening class must avoid both a second per-byte relation state machine and a fixed positional sampling lattice.

## Hypothesis

Relation evidence can piggyback on the already-required aligned 64-byte fingerprint cadence. At each completed block, eight lane positions derived from the block fingerprint nominate a local non-zero first-difference value and a local non-zero lag-64 XOR value. Only relations whose same value wins across at least 7/8 eligible blocks are nominated.

This should preserve the promoted eight-family structural decisions while making relation work proportional to blocks rather than bytes and avoiding the previous fixed-grid alias.

## Causal comparison

Baseline: the frozen native run+reuse observer from `one_g02_native_multi_law_carry.py`.

Candidate: identical run/reuse loop plus block-finalization relation sketches. It has no per-byte add8 histogram, no per-byte XOR histogram and no lag ring. It performs eight content-derived probes per completed 64-byte block; XOR probes read the corresponding lane of the previous aligned block.

Both arms pay the same Python->ctypes input copy, native call boundary and run/reuse fingerprint work. Native library compilation is outside timing because a product reader/writer would ship compiled.

## Frozen matrix

64 KiB, 256 KiB and 1 MiB x the existing eight structural families: `long_runs`, `exact_repeat`, `add8_ramp`, `xor_chain`, `mixed_structured`, `random`, `compressed_like`, `false_pattern`. 21 paired repetitions with alternating arm order.

The candidate decision set must equal the independent family oracle exactly on all 24 rows. Baseline run/reuse evidence must remain identical. Source scan accounting remains exactly 1.0x input.

## Frozen promotion law

Advance only if all conditions hold:

- exact unique 24-cell matrix;
- semantic equality on all rows;
- baseline/candidate run+reuse equality on all rows;
- source scan exactly 1.0x input;
- median candidate/baseline wall <=1.20x and CPU <=1.20x;
- no row exceeds 1.35x wall or CPU;
- every 1 MiB row reaches >=250 MiB/s on wall and CPU accounting.

Semantic disagreement is `INVALIDATE_BLOCK_RELATION_SKETCH`. Correct semantics with a compute miss is `HOLD_BLOCK_RELATION_SKETCH`. Thresholds and matrix must not be changed after hosted evidence.

## Non-claims

Even ADVANCE proves only that block-cadence relation nomination is a credible cheap substrate. It does not prove complete resemblance discovery, exact downstream relation proof cost, final bytes eliminated per CPU second, selective access, authentication, or Genesis supersession. Exact Law proof remains mandatory before storage.
