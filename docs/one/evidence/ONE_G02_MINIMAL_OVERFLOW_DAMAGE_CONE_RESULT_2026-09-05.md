# ONE-G0.2 — minimal-overflow damaged-relation cone result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **ADVANCE generic damaged-relation Law expression**

## Evidence identity

- branch head under test: `6c5f4b14fffd9407eb7971724d190d178a2ac571`
- PR merge SHA executed by Actions: `af3da918c613f8ff83c6f6b83a3c9a8de9220185`
- workflow run: `33980676778`
- job: `101345210895`
- artifact: `9973657317`
- artifact SHA-256: `e3e5f954c8a15a0e4f01683d12ab8c2438fb57e6bafd962b71c07215857d97d5`
- ONE semantic/hostile suite: `83 passed in 0.66s`
- benchmark process exit was preserved by `set -o pipefail`; the frozen benchmark exited zero.

## Main result

The compiler leaves generic `concat` flat whenever the existing 4,096-reference envelope permits it. Only the exact overflow required by the hard cap is grouped, and among equivalent minimum-count windows the shortest reconstructed-byte window is chosen, minimizing added materialization by construction.

All 14 frozen damaged-relation rows encoded, decoded and reconstructed byte-exactly. Every density/resource gate passed without raising any reader limit or adding an operation.

Aggregate storage:

- literal two-version wire: `2,082,446 B`;
- candidate generic ONE wire: `1,246,761 B`;
- candidate/literal: **`0.598700278x`**;
- bytes eliminated: `835,685 B`.

Thus the damaged relation structure eliminates about 40.13% of the complete two-version wire on this frozen matrix while remaining ordinary ONE `surprise + ranged Ref + concat`.

## Resource result

For every row:

- candidate wire was smaller than literal;
- control/integrity debt stayed below 25% of bytes eliminated;
- reader work stayed below `1.75x` literal;
- materialization stayed below `1.25x` literal;
- node count stayed inside both the row gate and the unchanged 4,096-node envelope;
- concat fanout stayed at or below the unchanged 4,096 hard cap;
- hierarchy depth stayed at or below 2 on the observed matrix, against frozen max 4.

Most rows required **no hierarchy at all**. The only frozen row exceeding the flat concat limit was the 256 KiB `fragmented_every96` case:

- leaf relation parts: `5,464`;
- minimum grouped overflow parts: `1,369`;
- minimum-byte grouped window: `65,585 B`;
- root max fanout: exactly `4,096`;
- cone depth: `2`;
- candidate nodes: `2,735`;
- candidate wire: `297,494 B` versus `524,409 B` literal = **`0.567293849x`**;
- materialization: **`1.130304337x`** literal;
- reader work: **`1.251799266x`** literal;
- control debt / bytes eliminated: **`0.143212216x`**.

That row is especially important because the earlier eager 64-way hierarchy failed at roughly `2.005x` materialization and `1.835x` reader work. Minimal spill preserved essentially the same density while bringing both resource costs comfortably below the preregistered limits.

Representative non-hierarchical rows:

- 4 KiB quarter damage: wire `0.637863x`, materialization `1.124634x`, work `1.208211x`;
- 4 KiB fragmented/96: wire `0.565050x`, materialization `1.005371x`, work `1.168457x`;
- 64 KiB fragmented/96: wire `0.565968x`, materialization `1.005219x`, work `1.168406x`;
- 128 KiB fragmented/96: wire `0.566854x`, materialization `1.005215x`, work `1.168405x`;
- 256 KiB quarter damage: wire `0.630761x`, materialization `1.124514x`, work `1.208171x`.

## Creation-cost warning

Reference-Python construction + wire encoding remains expensive and is **not promoted as product-speed evidence**. Candidate/literal build+encode ratios ranged from roughly `9.1x` to `65.4x` in this matrix. The 256 KiB fragmented case was about `65.43x` literal construction time.

The representation has therefore passed; the current Python Builder has not.

The next decisive work is to fuse damaged-relation segmentation and generic segment-plan emission into the native/observation path, measuring bytes eliminated per CPU time and memory traffic. Native work must preserve this exact representation/resource envelope rather than replacing it with a relation-specific reader mechanism.

## Scientific interpretation

Three experiments now separate the causes cleanly:

1. flat concat failed the hard fanout cap;
2. 64-way universal hierarchy solved fanout and density but paid unnecessary intermediate materialization;
3. minimal-overflow hierarchy solves only the mathematically forced spill and passes all frozen storage/reader-resource gates.

The useful principle is general: **hierarchy should be opportunity-gated by semantic resource necessity, not applied uniformly.** This is consistent with ONE's broader sparse-opportunity law.

## Claim boundary

This advances representation viability for known adjacent damaged relations only. It does not establish automatic pair discovery, native creation speed, canonical format promotion, or superiority to frozen v0.29/deferred v0.30. No new reader-visible opcode was introduced.
