# R38 — Regenerable-Deflate Encode Critical-Path Attribution Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent authority: terminal R37 `WAIT_ONCE_RUNTIME_OR_RSS_REGRESSION`, preserved in `R37_REGENERABLE_DEFLATE_WAIT_ONCE_BUILDER_RESULT.md`.

## Forge question

R36 localized excess observed waiting to the candidate-encoding boundary in `Builder.build`. R37 then falsified the hypothesis that repeated ordered consumer waits are the dominant cause: aggregate wait recovered only 2-4 ms while the byte-winning candidate remained 38-56 ms materially slower than release. Which concrete encode task or task family sits behind that residual critical path?

R38 is diagnosis only. It preserves the current ordered `ThreadPoolExecutor.map` semantics and instruments the function executed for each already-defined candidate. It may not alter candidate generation, representation policy, worker count, codec choices, archive grammar, thresholds, corpus, or locality accounting.

## Frozen substrate and targets

R38 inherits unchanged:

- the R32 `release-all-exact` and `no-ordinary-zstd` arms;
- the exact full `06_incremental_backups` target and isolated unchanged `snapshot_2.zip` projection used by R34-R37;
- three fresh processes per arm per target;
- public strong verification and deterministic complete-archive identity requirements.

R38 deliberately does not use R37's wait-once arm. The measured candidate is the unchanged `no-ordinary-zstd` map-control substrate whose product debt remains unresolved.

## Frozen instrumentation

For the single `ThreadPoolExecutor.map` call inside `Builder.build`, wrap only the submitted encode callable while retaining the original executor `map` implementation and ordered iterator semantics. For every encode task record:

- raw candidate SHA-256 key (`h`);
- raw bytes;
- sorted hint set;
- count of exact-DEFLATE alternatives carried by the candidate;
- task start/end monotonic timestamps relative to the first observed encode start;
- task elapsed seconds;
- resulting codec and compressed+metadata bytes.

Exactly one instrumented Builder map call must be observed per build. The wrapper may collect telemetry but may not change the callable's return value, order, worker count, or exception behavior.

## Frozen aggregation

For each target/arm:

- require three deterministic strong-verifying repetitions;
- aggregate each candidate key by median elapsed time across repetitions;
- compute median encode makespan from earliest task start to latest task end;
- compute positive candidate-minus-release median elapsed deltas for keys present in both arms;
- treat candidate-only keys as positive work with their candidate median elapsed time and release-only keys as zero candidate excess;
- rank positive excess by candidate key.

The **dominant excess owner** is the key with the largest positive delta. Report its raw bytes, hints, DEFLATE-alternative count, candidate/release medians, delta, and share of summed positive excess.

## Frozen interpretation law

Exactly one terminal decision is emitted:

1. **`CRITICAL_ENCODE_OWNER_LOCALIZED`** — the same dominant key is observed on both targets; its positive excess is >0 on full-backups and >=0.010 s on nested-only; and it accounts for >=50% of summed positive encode-task excess on nested-only.
2. **`ENCODE_FAMILY_DISTRIBUTED`** — identity/instrument completeness passes, positive encode excess exists, but no single cross-target key satisfies the localization law.
3. **`NO_ENCODE_WORK_EXCESS`** — identity/instrument completeness passes but summed positive encode-task excess is <=0 on either target, contradicting the encode-work interpretation and returning diagnosis outside the encoded tasks.
4. **`SUBSTRATE_OR_INSTRUMENT_FAILURE`** — strong verification, deterministic bytes, one-map-call instrumentation, candidate strict byte win, or inherited substrate fails.

No decision grants product or release credit.

## Next-action law

- `CRITICAL_ENCODE_OWNER_LOCALIZED`: a next Builder may target only the identified candidate's **content-derived causal family**, never its path/hash/workload identity. Before changing product behavior, derive the smallest content/representation predicate that explains why the task is expensive and show Addressable Opportunity Mass beyond the single frozen member.
- `ENCODE_FAMILY_DISTRIBUTED`: do not micro-optimize the top row. Cluster by content-derived properties (raw-size regime, hints, exact-DEFLATE availability, resulting codec) under a new freeze.
- `NO_ENCODE_WORK_EXCESS`: retire encode-task work as the current explanation and diagnose pre-encode/post-encode project phases instead.
- substrate failure: repair Custody or supersede the freeze; never rewrite this grammar.

## Strongest preregistered self-critique

Per-task wall durations under a thread pool include contention and scheduling interference; they are attribution evidence, not independent CPU-cost measurements. The cross-target same-key requirement and >=10 ms nested floor are intended to prevent a noisy slow task from being mistaken for a causal owner. Any later Builder must return to uninstrumented fresh-process product timing before promotion.
