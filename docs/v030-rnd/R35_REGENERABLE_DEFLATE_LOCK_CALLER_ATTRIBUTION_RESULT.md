# R35 — Regenerable-Deflate Lock-Caller Attribution Result

Status: **TERMINAL — LOCK_CALLER_LOCALIZED**

Frozen preregistration: `docs/v030-rnd/R35_REGENERABLE_DEFLATE_LOCK_CALLER_ATTRIBUTION_PREREG.md`.
Frozen instrument: `benchmarks/v030_r35_regenerable_deflate_lock_caller_attribution.py`.

This is diagnostic Forge evidence only. It grants no product or release credit and does not authorize editing Python's threading runtime. Its purpose is to narrow the residual R32/R34 runtime debt to the lowest project-owned scheduling boundary that causes the observed waits.

## Execution authority

- workflow run: `33845550023`
- result-bearing job: `100936925238`
- exact evidence head: `29f83a6eb75896aeda183149b6211bd0a73c65e1`
- parent accepted R32 substrate head: `0b1f3cd653f0e2489964b93cdd19fa8324adda2e`
- parent accepted R34 result head: `7c1bbaf272ac286180c6876d996c18d3d04b9748`
- immutable artifact: `9926485563`
- artifact ZIP SHA-256: `97b48e626f5601bab6eeab0ca63aa00657e62199d80414dcc59c94e2c17a28a0`
- exact-head checkout: **PASS**
- frozen R32 substrate binding: **PASS**
- frozen R34 result binding: **PASS**
- frozen R35 preregistration/instrument binding: **PASS**
- decision-law guard: **PASS**
- workflow topology self-check: **PASS**

## Frozen terminal decision

`LOCK_CALLER_LOCALIZED`

The only caller satisfying the preregistered cross-target localization law is:

`threading.py:295:wait`

| Target | release lock time attributed to `wait` | no-Zstd lock time attributed to `wait` | excess | excess calls |
|---|---:|---:|---:|---:|
| Full Incremental Backups | 100.226086 ms | 151.124278 ms | **+50.898192 ms** | **+112** |
| Isolated `snapshot_2.zip` | 2.541962 ms | 64.086837 ms | **+61.544875 ms** | **+214** |

Other observed lock callers remain far below the frozen 10 ms nested localization floor. In particular, `_wait_for_tstate_lock`, `_acquire_restore`, `_is_owned`, and tempfile lock callers contribute only sub-millisecond or tens-of-microseconds deltas.

## Byte/runtime identity

All repetitions strongly verified, all arms were deterministic within this run, and the byte-winning `full-search` and `no-ordinary-zstd` arms were exactly byte-identical on each target.

### Full Incremental Backups

| Arm | Complete bytes | Archive SHA-256 | Median profiled wall time |
|---|---:|---|---:|
| `release-all-exact` | 8,088,621 | `99dc7e3451137944cfea0073db5d5dd27240963a2262b4a8873e9532384eff5d` | 0.557462 s |
| `full-search` | 8,056,221 | `6659da4be9fb570c0d3f289dba080b374459b5d54b31f5eb8018bb303e67ef5d` | 0.648166 s |
| `no-ordinary-zstd` | 8,056,221 | `6659da4be9fb570c0d3f289dba080b374459b5d54b31f5eb8018bb303e67ef5d` | 0.592517 s |

The no-Zstd byte-winning candidate saves **32,400 B** versus release, but remains **+35.056 ms / +6.29%** slower under the profiled R35 boundary. That is still a material runtime regression under the existing >5% AND >3 ms law.

### Isolated `snapshot_2.zip`

| Arm | Complete bytes | Archive SHA-256 | Median profiled wall time |
|---|---:|---|---:|
| `release-all-exact` | 2,231,160 | `7fd58ec739b673bd500c3196a7fc4f266c3c9070a4bd97b918fd9c6968d11507` | 0.335760 s |
| `full-search` | 2,197,416 | `972f88410cd9558a9a39bb2ce9a9df3854b4fd9ed0792eb86dc61d1e9f63b492` | 0.446423 s |
| `no-ordinary-zstd` | 2,197,416 | `972f88410cd9558a9a39bb2ce9a9df3854b4fd9ed0792eb86dc61d1e9f63b492` | 0.392597 s |

The candidate saves **33,744 B** versus release, but remains **+56.837 ms / +16.93%** slower under the profiled R35 boundary. This is also materially red.

## Causal interpretation

R34 established that `_thread.lock.acquire` owns most of the residual same-run debt. R35 now localizes that lock time to `threading.Condition.wait` rather than to tempfile locks, thread teardown, or diffuse lock activity.

This is not evidence that the Python standard library is defective, nor does it authorize generic worker-count or lock tuning. `Condition.wait` is a synchronization sink: the project-level owner is whichever CMPCT build/scheduling operation creates the additional waits. The next intervention must therefore trace the extra wait events back to the project-owned submission/completion boundary and alter only that lowest sufficient scheduling pattern if the byte-winning work can be preserved.

The most plausible mechanism class is excess task synchronization caused by the specialized candidate path changing the amount/shape of work submitted or awaited, but R35 does not identify the originating CMPCT frame. Treating this inference as proven would repeat the speculative-optimization error R32 was designed to avoid.

## Scoped negative constraints

Within the frozen R32–R35 regime:

1. residual runtime debt is not diffuse across lock callers;
2. tempfile locking and thread teardown are not sufficient owners;
3. the transferable excess is localized at `threading.Condition.wait`;
4. editing Python threading internals, changing worker count generically, or tuning arbitrary lock behavior is not justified by this result;
5. the next lawful question is which project-owned scheduler/submission/completion caller causes the extra Condition waits while preserving the exact byte-winning archive.

Reopening any retired generic lock/threading family requires new evidence that the standard-library primitive itself, rather than CMPCT's scheduling pattern, is causally responsible.

## Strongest surviving self-critique

R35 attributes the lock primitive to a standard-library caller, not yet to a CMPCT source frame. It therefore narrows the causal cone but does not identify the mutation site.

There is also a small cross-run archive-identity drift relative to earlier R32/R34 historical measurements even though the frozen same-run identity law passed: R35 produced 8,056,221 B for the full byte-winning arm and 2,197,416 B for the nested arm. Earlier accepted runs reported slightly different complete sizes. The preregistered R35 law intentionally requires deterministic same-run arm identity rather than historical cross-run byte equality, so the terminal decision remains valid under its frozen grammar; however, this drift is a custody/environment warning. A next Builder must bind its dependencies/execution substrate tightly and must compare its control/candidate within the same fresh-run boundary. No historical byte total should be silently substituted for the new control.

## Forge decision

- diagnosis: **D2/D3 synchronization debt localized to a generic wait sink, project caller still unresolved**;
- lowest next intervention: **R0 caller-of-caller / scheduling-boundary attribution**, not generic concurrency tuning and not product mutation;
- explicit decision: **`TRACE_PROJECT_WAIT_OWNER_BEFORE_MUTATION`**.

A superseding R36 diagnostic should attribute the extra `threading.Condition.wait` events to the project-owned submit/map/as-completed/result/wait boundary, preserve the exact R35 same-run byte and verification laws, and end with a bounded project-frame owner or a scoped negative result. Only then may a lowest-sufficient Builder mutate scheduling behavior.
