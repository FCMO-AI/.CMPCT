# J24G13 — prospectively preregistered untraced Reader CPU/RSS falsifier

Date: 2026-10-28 UTC. Parent is draft research PR #671 at exact head `2a56e83a55bdd60a0b9de86e7d09bec2ca4d664d`; its inherited product Reader comes from draft #668 with Git blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. The current released product remains v0.30.0 / revision 24. **Research only, no Reader, format, benchmark or release mutation.**

## One falsifiable primary question

Does the guarded parse/discard ancestry model retain its observed memory benefit and its reported CPU direction when `tracemalloc` is completely **off** for the timed product operation? The prior [J24G12 #671](https://github.com/FCMO-AI/.CMPCT/pull/671) found an ~88% lower *traced* allocation peak for 4,096 SHA-valid chained orphan footers, and ~34% more CPU for 512 legitimate delta generations, but measured CPU while the allocation tracer was active. Allocation instrumentation is a potential causal confound.

## Prospective experiment and comparators

Use the **same exact Git-installed Reader** as #671 and import its unchanged research subclasses (eager reference, guarded discard, unsafe-skip negative control only when relevant). Compare **eager versus guarded** on one identical first-party Builder+Writer archive per condition. Cases, fixed before evidence: genuine Writer rename; 512 legitimate SHA-authentic noop deltas; 4,096 linked orphan deltas; 4,096 flat independent orphans. Preserve prior signed-malformed MessagePack negative as a semantic gate: eager/guarded must both error.

Each case receives four independent child-process repetitions for each arm in each *tracer-on* and *tracer-off* mode on Ubuntu 24.04 / Python 3.11, randomized only by predeclared deterministic alternating order. The child process loads the installed CMPCT before starting the timer. Measurement boundaries include Reader open, full/range read and verify; exclude import/process startup. Record raw wall and process CPU nanoseconds plus child `ru_maxrss` (Linux KiB), OS and code SHA, counts outside the timed scope (or no monkeypatch counts in timed path). All product cells share one physical archive SHA and expected last valid checkpoint. Independently recalculate medians, same-archive equality and relative effects from raw rows.

**Primary discriminator:** compare guard/eager CPU ratio with tracer off against the previously traced direction on valid-512, orphan-4096 and independent-4096. If tracer-off valid overhead is still >25% and >0.05 ms absolute, always-guarded is still a clear product reject. If overhead collapses, revisit the CPU conclusion but still require a true product architecture and multi-host performance. A separate within-run tracer-on arm identifies whether memory instrumentation changes the ordering. Regardless, preserving exact selection, bytes, range, verify and malformed error is a hard gate; no statistical result can excuse a failure.

## Costs, limitations and kill conditions

Report peak RSS only as total fresh-child maximum, **not incremental process allocation or complete bounded memory**. The fake signed tail is a hostility/representation instrument, not natural prevalence or whole-product evidence. No source mutation race claim. A guarded win under this setup cannot authorize merge/release; unchanged full r24 floor, startup, source/copy custody, Windows/macOS and physical input semantics still need confirmation. A result contradicted by source identity, archive SHA, error semantics, or control measurement is marked invalid, not salvaged.

## Concurrency and BONK

Before entry, open PR search found #671 as the current ancestry-lifetime owner, #668 as packed-negative-proof owner, #669 as a disjoint native range owner, and #670/#673 as a disjoint A14 representation family. No J24G13/untraced active PR was found. This is an **independent follow-up measurement** on top of #671, not a duplicate implementation, and no existing owner branches, frozen evaluators, CI policy or discovery state will be modified. Strong simpler control is original eager Reader and the oracle rung is fresh-child untraced CPU/RSS. Decisive outcome may narrow an inherited research claim; it is not itself a product performance claim.

Next independent path if traced timing is confirmed misleading: pair a minimal adaptive ownership oracle against eager without sacrificing malformed MessagePack policy; otherwise prioritize the other active product frontier instead of perpetuating this family.
