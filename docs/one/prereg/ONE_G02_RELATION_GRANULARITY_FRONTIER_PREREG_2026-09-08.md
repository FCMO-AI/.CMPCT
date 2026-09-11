# ONE-G0.2 relation granularity frontier — preregistration and hostile review

Date: 2026-09-08
Branch authority: `research/cmpct1`
Research version: ONE-G0.2

## Mission lock

The bounded non-redundant block-relation gate has established that local add8/XOR structure can be nominated and exactly proved without unbounded hostile proof traffic. This document freezes the next question before hosted evidence: **can that relation principle be represented economically by the existing six-op ONE grammar under its existing resource limits?**

The experiment is not allowed to add a relation codec, widen `Limits.max_nodes`, add an interleave/stride opcode, weaken root integrity, or give the reader discovery work.

## Hypothesis

For independently generated parent blocks followed once by an exact non-zero add8 or XOR child, at least one relation block size from 512 to 4096 bytes will:

1. compile into only existing `surprise`, `fill`, `add8`/`xor`, and `concat` nodes;
2. remain within `max_nodes=4096` at 1 MiB;
3. reconstruct exactly through the independent reference evaluator with the same root SHA-256; and
4. encode in no more than 55% of the corresponding literal ONE wire bytes.

Both add8 and XOR must satisfy the 1 MiB density requirement.

## Frozen matrix

- logical sizes: 64 KiB, 256 KiB, 1 MiB;
- relation block sizes: 64, 128, 256, 512, 1024, 2048, 4096 bytes;
- relation families: add8 and XOR;
- total: 42 exact cells.

Each cell contains independent pseudorandom parent blocks and exactly one transformed child per parent. The relation value changes by pair so the benchmark cannot accidentally turn into exact reuse of a shared transformed child. Any duplicate aligned block invalidates the result.

## Existing-grammar lowering

Each pair is represented as:

- one parent `surprise` node;
- one `fill` node carrying the relation byte over the block;
- one existing `add8` or `xor` node over parent + fill;
- one final `concat` root referencing parent then derived child for each pair.

The candidate is rejected before encoding when either total nodes or root reference fan-in exceeds the existing 4096-node envelope.

## Hostile reviewer / disproof rules

The 64-byte 1 MiB geometry is expected to exceed the node budget. That failure is part of the experiment and may not be hidden by increasing limits. A green result must therefore demonstrate that useful relation information survives at a coarser generic Law granularity rather than canonizing the detector's 64-byte probe as a storage boundary.

Every admitted row must pass `encode_program` and the independent semantic evaluator. Wire bytes include all control and root-integrity bytes. Literal comparison uses the same experimental wire and the same limits.

Reference work/materialization ratios and native prepared-plan replay ratios are diagnostic and must be preserved even if they are poor. They cannot be removed from the artifact to make a density result look like a full-system win. Native replay timing is collected only for admissible 1 MiB rows and does not determine this representation-frontier verdict.

## Decision law

`INVALIDATE_RELATION_GRANULARITY_FRONTIER` if the 42-cell matrix is incomplete/duplicated, any aligned duplicate contaminates a source, any admissible candidate reconstructs incorrectly, or the 64-byte 1 MiB geometry is admitted despite the frozen node envelope.

`ADVANCE_RELATION_GRANULARITY_FRONTIER` only if both add8 and XOR have at least one admissible 1 MiB block size >=512 bytes with candidate/literal wire ratio <=0.55.

Otherwise: `HOLD_RELATION_GRANULARITY_FRONTIER`.

## Interpretation boundary

Advance means only that relation Law has an economical representation region inside the existing ONE grammar. It does **not** prove that the current 64-byte observer descriptors can be compiled directly, that writer discovery cost is worthwhile, that native replay beats literal copy, or that selective-read amplification is acceptable. Those become the next causal gates.

If the representation frontier advances while 64-byte geometry fails the node cap, the next writer experiment should make discovery granularity adaptive: use cheap fine probes only as evidence, then grow/merge the verified relation into coarser Law spans before emitting ONE nodes. If no coarser region achieves the wire target, the local block-relation line holds and should not earn a new reader primitive merely to rescue it.
