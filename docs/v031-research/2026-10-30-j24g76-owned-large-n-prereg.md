# J24G76 — held-out large-N owned-decoder transfer: prospective experiment

Date: 2026-10-30 UTC. Status: **PREREGISTRATION, NO RESULTS**. Research-only child of #820 exact `c15459f70001800f3781925efc7356409eb03ffe`; no product code, format, release, benchmark threshold or evaluator modifications.

## Question, alternatives and baseline
J24G74 (#820) observed an additional 3.30–3.97x warm Reader-open speedup over the already-experimental copy-preserving path on a physical 2,048-live-member, 63-delete archive. It saved roughly 1.10MB of traced Python allocation, but has **not** demonstrated large-N scaling, realistic constructor peak RSS, or an independent held-out position pattern. Might its optimistic gain be an artifact of small indexes or front-heavy deletion?

Compare the **unaltered** inherited Reader `CMPCT`, source-exact J24G73 `FactoredCMPCT`, and source-exact J24G74 `OwnedCMPCT` on the **same physical archive bytes** per host. Include both a 8,192-start-member / 63-middle-delete case and a 32,768-start-member / 63-tail-delete case. The tail case is structurally hostile to simple deletion shortcuts; no threshold/fallback changes are permitted. Test authentic public `Builder` + 63 `append_delete` generations (all one-op), identical final bytes/complete index, strict preflight, strong verify, full exact reading and SHA-256; and 64 authenticated footers. No checkpoint in the timed chain; archive bytes unchanged by opening.

## Prospectively predicted decision
H1 material-transfer survival: in each held-out large-N family, `OwnedCMPCT` median warm complete Reader-open wall < `FactoredCMPCT` / 1.20 on **at least 2/3 operating systems**, with no worse median Python traced peak allocation on those two; all exactness, archive-integrity and recovery checks must PASS. If the candidate is slower, unstable, not admitted, or exceeds memory, **narrow/retire the claimed scalable owned-copy advantage** instead of retuning sample or selection. Every platform observation is preserved, even contradictory ones.

Also measure fresh-process peak RSS and post-close RSS (3 probes/variant/case), CPU time, archive stored bytes and source identity. RSS is diagnostic; process samples are not interchangeable with Python `tracemalloc`. Release-performance inference remains prohibited: this is warm Reader constructor-only, not full create/extract, cold disk, native Rust or ZIP/Zstd. Real Builder generation cost is recorded separately from Reader-open; it is not optimized.

## Confounders, controls, hostile checks
- Installed `cmpct` Reader, shared replay, and all three experimental algorithms must be exact source blobs inherited from #820; source SHA and commit are recorded before result.
- Balanced ABC permutations, same bytes per host, independent physical signed-footer interpreter inherited from #818, local independent raw-sample arithmetic and no fabricated re-runs. Preserve originals in Actions artifacts.
- Verify strict `preflight_archive`, SHA-256, final file set, per-file bytes and content digest; reject a mutated tail SHA and a truncated footer by recovering the identical valid predecessor across variants.
- File index naming and position selection must be deterministic: delete names near the *middle* of the index in the first case, and names near its *end* in the second. Do not use case-specific code in the replay candidate.
- Include a retained-caller alias negative and an output-only mutation test after the Reader is fully constructed; no claim of publicly immutable index objects. Any unexpected mutation of an external reference, inability to reconstruct, or changed Reader error is a negative.
- No full product benchmark credit or release gate admission from this experiment. Zero new archive bytes in Reader-only comparison is a **measurement boundary**, not zero total system cost.

## Concurrency/authority
#820 owns the experimental algorithm, #818 the prior complete Reader comparison, #808 the general mechanism, #795 the integration seam, #815/#817 signed hardlink correctness, #574 shared discovery STATE, #822 CI/promotional custody. This child changes only its own research script, workflow and eventual results. Do not change those owners, product code, shared state or release law. If exact source or cross-PR claims drift before late writes, inspect current truth and replan.

## Counterfactual discriminator
J24G74's 2,048-member win would have been cheaper to limit correctly if the first acceptance test included genuinely held-out N/position, rather than only repeated source-identical small data. This is a hypothesis about experimental design, **not an earned Discovery Engine policy change**. Retain losses without reclassifying them.
