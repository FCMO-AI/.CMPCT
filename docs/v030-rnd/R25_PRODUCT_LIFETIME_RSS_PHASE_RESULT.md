# r25 product-lifetime RSS phase attribution result

Status: **ACCEPTED DIAGNOSTIC CAUSAL EVIDENCE / FORGE-CUSTODY / NO RELEASE CREDIT**

This record closes the frozen experiment in `docs/v030-rnd/R25_PRODUCT_LIFETIME_RSS_PHASE_PREREG.md`. It changes no production source, scheduling, selector, archive grammar, locality/decode-unit bound, integrity/recovery law, benchmark threshold or release state.

## Authority

- exact experiment source: `b02b4ad06d07025de6e9a0fd8ad64e283df42fd2`;
- workflow: `CMPCT v0.30 product-lifetime RSS phase attribution`;
- workflow run: `33607562272`;
- substantive job: `100174971335` (`product-lifetime-rss-phase`), completed success;
- artifact: `v030-r25-product-lifetime-rss-phase-b02b4ad06d07025de6e9a0fd8ad64e283df42fd2`;
- artifact id: `9837925068`;
- upload ZIP digest: `sha256:b8957e0656eed5a3e6c3a00ce7590e8da82a0613e4bc580a38e843f69803b59b`;
- schema: `cmpct-v030-r25-product-lifetime-rss-phase-v1`;
- repetitions: 3 fresh processes;
- experiment valid: `true`;
- release credit: `false`.

The workflow ratchet independently required exact semantic-owner identity, exact cross-repetition selected product identity, strong verification, wrapper restoration, no sampler errors, >=100 samples per repetition and sampled live-RSS coverage >=90% of process `ru_maxrss`. All passed.

## Exact product identity

All three repetitions emitted the same selected canonical product:

- selected representation: `prefixgraph`;
- format revision: `25`;
- complete bytes: **1,700,604 B**;
- physical SHA-256: `0086e74f0d772e8a2ba0b249a3c08c4b90c76f315f1bdfb33f922f63c95eb5d9`.

Measured wall times were **60.297 s, 63.057 s and 56.299 s**. These are diagnostic operation times, not a release-performance receipt.

## Live-RSS result

| repetition | operation-entry VmRSS | first candidate-entry VmRSS | sampled live peak | process `ru_maxrss` | retained-entry fraction |
|---|---:|---:|---:|---:|---:|
| 1 | 29,848 KiB | 68,404 KiB | 400,856 KiB | 400,612 KiB | 9.6184% |
| 2 | 29,796 KiB | 68,356 KiB | 400,456 KiB | 400,264 KiB | 9.6290% |
| 3 | 29,848 KiB | 68,408 KiB | 400,536 KiB | 400,140 KiB | 9.6271% |

Median frozen retained-entry fraction: **9.6271%**.

The sampled global peak phase combination was identical in all three repetitions:

`g04-build + prefixgraph-build + r25-tournament + shipping-product`

The 10 ms live sampler captured essentially the entire high-water event in every repetition: sampled/`ru_maxrss` coverage was ~100.05%, ~100.05% and ~100.10%. Slight sampled values above `ru_maxrss` are measurement-timing/kernel-accounting effects; `ru_maxrss` remains the authoritative process high-water and the live trace is used only for phase attribution.

A second, lower peak occurred near the beginning while genuine-r24 prebuild/consume overlapped both candidates: approximately **359–361 MiB**. The actual ~400 MiB global peak occurred later after that r24 overlap was no longer active.

## Frozen decision

**`RETIRES_PRE_CANDIDATE_RETAINED_STATE_PRIMARY`**

The preregistered retirement boundary was `<10%`; the observed median is **9.6271%**. Do not round this upward after observation.

For this exact Shifted product regime, substantial memory already resident before the first r25 candidate begins is therefore **not** the primary explanation for the shipping ~400 MiB peak. This extends the prior scoped negatives:

1. profile/manifest capture alone is not dominant;
2. neither exact G0-G4 nor exact PrefixGraph alone reproduces shipping peak RSS;
3. simply serializing PrefixGraph/G0-G4 did not improve process high-water RSS and worsened wall time;
4. serializing the outer genuine-r24/r25 race removed only 9.9863%, below its frozen primary-owner boundary;
5. now, pre-candidate retained product state itself is below the frozen 10% ownership boundary.

## Causal interpretation

The unresolved memory is generated **during candidate execution**. The exact live high-water occurs while both exact candidate builders are active. This does not reopen the already-failed conclusion that naive serialization is a product fix: the serialized v3 arm increased `ru_maxrss`, consistent with memory produced by the first candidate remaining resident while the second candidate allocates.

That distinction matters. The next question is no longer “which scheduler should run first?” It is:

> **what memory produced during one candidate remains live/allocator-resident while the other candidate executes, and how much of that state is semantically required for winner selection versus diagnostic/build-stat carrying cost or reclaimable temporary work?**

The product currently retains candidate artifacts and rich build-stat results until byte/locality selection is complete. A next R0 attribution should measure exit-to-next-entry live RSS and retained candidate result/stat payloads under the already frozen serialized seam, or otherwise isolate candidate-produced retained/temporary state without changing archive bytes. An intervention is justified only after a specific removable class is measured large enough to matter.

## Reopening predicate

Reopen pre-candidate retained state as a primary RSS owner only if product setup/profile semantics materially change, or a new exact live-RSS experiment shows >=20% of operation peak already resident at the first candidate entry under an equivalent shipping regime. Runner noise or baseline-subtraction reinterpretation is not sufficient.

## Strongest self-critique

This experiment locates when the peak happens, not the exact allocation class that owns it. The active-phase labels prove both candidate functions are on-stack at the high-water event; they do not distinguish G0-G4 buffers, PrefixGraph buffers, Python allocator retention, compressed output/stat objects, shared source data, or lower-level library allocations. The next experiment must make that distinction before production memory behavior is changed.
