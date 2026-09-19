# v0.30 Shifted latent patch-pack R4 negative

Status: **terminal negative for the single-latent-basis + single shared delta-context family**.

This note records research evidence only. It grants no release credit and changes no canonical archive semantics, release threshold, benchmark corpus, or production selector.

## Exact evidence

Source commit: `e1ebf06acd9bc5331361220d419ede76a2176097`

Workflow: `CMPCT v0.30 Shifted latent patch-pack R4 floor`

Run: `33450039280`

Job: `99679316216`

Frozen Shifted tree: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`

The experiment preserved the content-derived latent basis and exact depth-1 reconstruction, but replaced eighteen independently compressed delta programs with one bounded shared Zstd-19 patch context. The shared patch context is legal under the existing decode-unit/locality laws and reconstructs the exact tree.

Measured result:

- latent logical bytes: `1,859,567`
- latent stored bytes: `1,676,542`
- shared raw patch bytes: `72,089`
- shared stored patch bytes: `29,399`
- complete research artifact: `1,706,975 B`
- solid Zstd-19: `1,694,672 B`
- ZIP/Deflate-9: `30,283,112 B`
- complete gap to Zstd-19: **`+12,303 B`**
- payload-only gap to Zstd-19: **`+11,269 B`**
- candidate creation: about `11.708 s`
- Zstd-19 creation: about `0.758 s`
- ZIP creation: about `0.830 s`
- max decoded unit: `1,862,620 B`
- max member read amplification: about `2.037x`
- exact tree verification: PASS

The later v3 instrumentation corrects candidate timing custody by excluding the independent-frame counterfactual from candidate creation time. That accounting repair cannot change the terminal size fact above: even the complete shared-context artifact is larger than exact solid Zstd-19.

## Domination audit

- strict target: 15/15 workloads strictly smaller **and** faster to create than both ZIP/Deflate and solid Zstd-19; ties fail
- diagnosis: `D4` representation / physical-layout floor
- radicality: `R4`
- inherited saturation: `S1`, `S3`, `S4`
- RPS: `98`
- measured gap change: shared patch context recovers fragmentation cost but leaves the complete artifact `12,303 B` above Zstd-19 and remains roughly fifteen times slower to create
- strongest surviving self-critique: the latent basis itself is genuinely strong (`1,676,542 B`, below Zstd-19); the failure is the information/ownership cost needed to reconstruct all members, not absence of cross-version structure
- terminal decision: **`RETIRE_FAMILY`**

## What is retired

Do not spend primary R&D budget on:

- changing the patch Zstd level;
- splitting the same delta programs into a different count of frames;
- another independent-vs-shared-frame sweep;
- metadata shaving around the same latent + `delta_encode` representation;
- faster implementation of the same representation as the route to strict domination.

Those changes cannot invalidate the measured size floor without new causal evidence.

## Next admissible Shifted frontier

The next R4 family must reduce the reconstruction information itself, not merely compress the same delta programs differently. A strong first test is a content-agnostic **bounded-drift sequential edit representation**:

1. choose one complete base by content-only rule;
2. represent each sibling as long sequential copy runs plus sparse bounded replacement/insert/delete runs;
3. pack all edit programs into one bounded context;
4. preserve depth-1 reconstruction, <=8 MiB decode units, <=8x member-read amplification, exact SHA/tree identity, and complete creation-time accounting;
5. retire the family immediately if its optimistic payload floor cannot beat exact solid Zstd-19.

This test is materially different from the retired rolling-block delta family: it attacks control/instruction entropy by exploiting long exact sequential runs after bounded drift rather than repackaging the same delta payloads.
