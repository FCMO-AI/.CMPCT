# ONE-G0.2 — bounded damaged-relation cone result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **HOLD bounded 64-way cone**

## Evidence identity

- branch head under test: `66aa78ddc0bc78cac81c55f159b3307e036dad44`
- PR merge SHA executed by Actions: `a5db94f5733f87b2a6bcd1661f19a1c7860b6d3c`
- workflow run: `33980532206`
- job: `101344831708`
- artifact: `9973618981`
- artifact SHA-256: `eff187bd8a7326f5105f430e274e2d3854eb20a4be6dbb365a3f4db403429882`
- ONE semantic/hostile suite: `83 passed in 0.73s`
- benchmark process exit was correctly preserved by `set -o pipefail`: exit 1 because frozen gates failed.

## Main result

Deriving local concat fanout as `isqrt(4096)=64` repaired the flat-concat hard-cap failure without raising any reader limit. All 14 rows encoded, decoded and reconstructed byte-exactly; max generated fanout was 64; cone depth was at most 3; total nodes remained below the unchanged 4,096-node envelope.

Density was strong:

- literal aggregate wire: `2,082,446 B`;
- candidate aggregate wire: `1,248,486 B`;
- candidate/literal aggregate: **`0.599528631x`**;
- aggregate bytes eliminated: `833,960 B`.

Every row stored fewer bytes than literal. Incremental control debt stayed below the frozen 25% share on every row; the worst observed fragmented case was about 14.72% at 256 KiB.

## Why the gate still failed

The hierarchy materializes intermediate concat outputs. That caused the frozen materialization gate (`<=1.25x` literal) to fail on every `fragmented_every96` row and on quarter-damaged rows once hierarchy became necessary.

Representative materialization ratios:

- 4 KiB quarter damage: `1.12463x` — pass;
- 4 KiB fragmented/96: `1.50537x` — fail;
- 32 KiB quarter damage: `1.62453x` — fail;
- 128 KiB fragmented/96: `1.50521x` — fail;
- 256 KiB fragmented/96: **`2.00521x`** — fail.

Reader work remained below the frozen `1.75x` limit on all rows except the 256 KiB fragmented case, which reached **`1.83507x`**. That same row was otherwise resource-valid: 2,822 nodes, max fanout 64, cone depth 3, and candidate wire ratio `0.568785x`.

The reference-Python construction cost was also very high (diagnostic only): damaged candidates ranged from roughly 12x to 76x literal build+encode time. This confirms that any eventual product path needs fused/native construction; it does not override the representation/resource hold.

## Causal interpretation

The hard-cap problem is solved, but the square-root fanout law is too eager: it hierarchizes rows that already fit under the 4,096-reference limit, and for large fragmented rows it materializes entire intermediate levels. The dominant remaining debt is **unnecessary intermediate output**, not stored-byte density or control overhead.

The next Builder should use a minimal-overflow cone: retain direct refs up to the existing hard cap and introduce hierarchy only for the smallest suffix/overflow needed to make the parent valid. This is not threshold fitting; it is the minimum added hierarchy implied by the hard cap. The reader cap remains unchanged.

## Claim boundary

This result proves that damaged relation structure can achieve strong generic ONE density while respecting bounded fanout, but the tested 64-way hierarchy does not meet the frozen reader-resource gates. It is not promoted. No v0.29/v0.30 superiority claim follows.
