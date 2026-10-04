# v0.30 H-EFFORT-6 RAW-Terminal Builder Mission Lock — 2026-09-13

Status: **frozen minimal execution-optimization Builder; research candidate only; no release credit**.

## Evidence basis

Two independent hostile courts have now tested the unchanged generic predicate `level-1 admitted codec == RAW`:

- H-EFFORT-5: 80 RAW packs / 10,606,293 B, zero later-level improvements, but one applicable family -> `RAW_TERMINAL_INSUFFICIENT_TRANSFER`;
- H-EFFORT-5B: 34 RAW packs / 7,864,605 B across six distinct Mosaic hostile families, zero later-level improvements -> `RAW_TERMINAL_SECOND_COURT_TRANSFERS`.

Together: 114 RAW packs / 18,470,898 B and zero counterexamples across two independently motivated hostile suites. H-EFFORT-4's separate ten-workload design substrate also observed 222 level-1 RAW packs with zero measured later byte headroom.

The simplest surviving mechanism is therefore ready for a Builder:

> when the already-built level-1 physical pack is non-hot and its admitted codec is RAW, skip the later adaptive effort ladder entirely; otherwise execute the inherited policy unchanged.

This Builder does **not** alter RAW admission, pack geometry, effort levels, stop logic for compressed incumbents, hot-stream treatment, archive framing, reader grammar, filesystem control, recovery, integrity, or locality.

## Candidate

Create one research candidate descended directly from the frozen historical adaptive-effort Builder. Its only semantic execution delta is:

```text
if pack is not hot and current level-1 admitted codec == RAW:
    perform zero later effort attempts
else:
    run the inherited 3 -> 6 -> 12 -> 19 first-worse ladder unchanged
```

Record RAW-terminal skip count and bytes. Do not add thresholds or additional selectors.

## Direct court

Use the exact deterministic ten-workload `v030_current15_stable_corpus` substrate already used by H-EFFORT-4. Compare inherited baseline Builder and RAW-terminal Builder on the **same generated source tree** per workload.

Run three repetitions per workload per contender in alternating order sufficient to reduce order bias. Each repetition must use fresh output archives. Preserve raw per-run CPU, wall, RSS, archive SHA-256, archive bytes, strong-verify result, locality report, effort attempts, RAW-terminal skips, and physical bytes saved.

This is a research Builder court, not a core-release benchmark. The baseline is the direct inherited adaptive-effort Builder, not a moving release or competitor.

## Hard semantic gate

For every workload and repetition:

1. candidate archive bytes must be **byte-identical** to baseline archive bytes for the corresponding deterministic source (`sha256` and length equal);
2. strong verification must pass;
3. canonical source tree identity must be preserved;
4. locality/decode-unit report must be equal to baseline;
5. candidate must not execute a later effort attempt on a level-1 RAW pack;
6. candidate must execute the inherited ladder unchanged for every non-RAW, non-hot pack.

Any failure => `RAW_TERMINAL_BUILDER_INVALID`; no performance interpretation is allowed.

## Frozen performance/materiality gate

After the hard semantic gate passes, compute sums of the per-workload median `total_build_cpu_s` and `total_build_wall_s` across the ten workloads.

Classify `RAW_TERMINAL_BUILDER_MATERIAL` only if all are true:

- candidate summed median CPU is at least **5% lower** than baseline;
- candidate summed median wall is at least **5% lower** than baseline;
- candidate saves at least **0.250 s** summed median CPU in absolute terms;
- no workload with baseline median CPU >= 0.100 s regresses candidate median CPU by more than `max(5%, 0.050 s)`;
- candidate process peak RSS does not exceed baseline by more than **5%** on any workload in all three repetitions, after allowing a 4 MiB absolute noise floor.

These are preregistered research materiality gates, not future release thresholds. If timing is too noisy to adjudicate, return `RAW_TERMINAL_BUILDER_INCONCLUSIVE_TIMING` rather than moving gates.

If semantic identity passes but performance misses the materiality gate, classify `RAW_TERMINAL_BUILDER_VALID_LOW_YIELD` and preserve the negative; do not compensate by expanding the selector.

## Hostile review requirements

Before any productization claim:

- independently count candidate skipped attempts and confirm they correspond only to level-1 RAW non-hot packs;
- confirm candidate/baseline archive SHA identity, not merely equal stored byte counts;
- report workloads with zero RAW skips separately;
- expose whether total gain is concentrated in one workload;
- report CPU/wall/RSS, not only archive bytes.

## Promotion boundary

Even a material result remains research evidence. Product integration must occur at the actual authoritative creation path, preserve exact release semantics, and re-earn the repository's then-current release/performance/native/platform authority. No version bump, format change, merge unlock, or release credit is authorized here.