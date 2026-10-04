# v0.30 EG08 tie-continuation attribution result — 2026-09-13

Status: **negative research evidence; stop-on-tie retired**

Exact measured head: `ddc2adf8bce3765667a9092700d20d47b83e5348`

Hosted run: `34763653707`

Receipt artifact: `10318929417`

Artifact digest: `sha256:1665770375b0aee2c0ba73999f1f987ea0a244cb0059c61213e68df282527257`

Scientific verdict: `EG08_TIE_CONTINUATION_CARRIES_DENSITY`

## Preregistered hypothesis

The lock in `docs/V030_EG08_TIE_CONTINUATION_ATTRIBUTION_LOCK_2026-09-13.md` asked whether the already-observed EG08 effort traces could stop at the first tie (instead of continuing through ties until the first strictly worse rung) without changing any final selected payload byte count across the nine frozen transfer surfaces.

Disproof required only one pack whose eventual EG08 strict win occurred after crossing a tie.

## Result

The counterfactual would have:

- avoided **1,631** effort attempts;
- changed the final selected payload on **599 packs**;
- lost **71,520 B** of EG08's selected density.

Therefore the hypothesis is decisively falsified. Continuing through ties is not mere proof traffic: the next effort rung often converts an equal-size intermediate result into a later strict win.

## Decision

`stop-on-tie` is retired as a Builder optimization. It must not be used to make the eligible-nine creation-CPU gate green by silently giving back the 71,520 B.

The creation-economics repair must instead remove redundant work while preserving the useful tie-crossing search. The leading mechanism classes are:

1. fuse adaptive physical-pack compression into first-pass final-pack creation so EG07 level-1 payloads are not first written and then reopened/decompressed/recompressed;
2. reuse already-computed compression state/work where the underlying API permits exact semantics;
3. derive a content-based bound that can skip provably futile later work without treating a tie itself as futile.

The first option currently has the clearest causal target because EG08's research implementation explicitly pays a complete EG07 build before the repack ladder. A safe implementation needs a narrow final-physical-pack compressor hook; globally replacing `V25.zc` is not acceptable because the same function is also used by pack-size probes, cold-stream decisions and metadata paths, which could change geometry or selection semantics.

## Score custody

This negative changes no frozen Genesis score, v0.29 identity, ONE status, locality law, integrity/recovery semantics, composed-R4 score or numeric version.
