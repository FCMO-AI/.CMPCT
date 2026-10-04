# R34 regenerable-Deflate same-run phase attribution result

Status: **ACCEPTED DIAGNOSTIC RESULT — PHASE_OWNER_LOCALIZED**

Normative freeze: `docs/v030-rnd/R34_REGENERABLE_DEFLATE_SAME_RUN_PHASE_ATTRIBUTION_PREREG.md`.

This record consumes the first result-bearing execution of the frozen R34 instrument. The preregistration remains immutable. R34 is diagnostic-only and grants no v0.30 release credit.

## Exact evidence identity

- evidence source: `11e5ae2a4d7eaa23458260aa96af6548f4cba505`
- GitHub Actions run: `33840569358`
- result job: `100921939032`
- artifact id: `9924836130`
- artifact name: `v030-r34-same-run-phase-attribution-11e5ae2a4d7eaa23458260aa96af6548f4cba505`
- artifact digest: `sha256:0209887a068b40d3f4acf5c0505bfe43e265aa60f4cbdbcf6a482087217f572f`
- result schema: `cmpct-v030-r34-regenerable-deflate-same-run-phase-attribution-v1`
- frozen parent R32 substrate: `0b1f3cd653f0e2489964b93cdd19fa8324adda2e`
- superseded R33 result head: `b2e7ff4cdf5e1dfd7b75d37c1c9e9304b8fc1331`
- environment: CPython 3.11.16, Linux GitHub-hosted ubuntu24 image `20260831.293.1`, zlib compile/runtime 1.3, Python zstandard 0.25.0

## Frozen identity law

**PASS.** `same_run_identity_ok=true`.

Within the result-bearing run, each target/arm was deterministic across all three fresh-process repetitions. Strong verification/tree reconstruction passed. `full-search` and `no-ordinary-zstd` were byte-identical on both targets, re-proving that the removed ordinary-Zstd work was output-dead in this execution environment. The candidate remained strictly smaller than `release-all-exact` on both targets.

### Full Backups

- `release-all-exact`: **8,088,617 B**, SHA-256 `219e9609a0f036e596520b3ea73f7149107c809ebefeec2d3e1cc93b9a3c3d7c`, median wall **0.538504413 s**
- `no-ordinary-zstd`: **8,056,197 B**, SHA-256 `127108ca14521e7ccdfe378dc00101a5428708e55dd35e0d5428646355bb05bb`, median wall **0.568245724 s**
- byte saving: **32,420 B**
- residual wall delta: **+0.029741311 s / +5.52295%**

### Nested-only `snapshot_2.zip`

- `release-all-exact`: **2,231,160 B**, SHA-256 `7b4d7ddbc1ec69b28c9f88a0b3097cea372ed035dfcab613d35553c65be91f90`, median wall **0.333475831 s**
- `no-ordinary-zstd`: **2,197,414 B**, SHA-256 `cd1e4535456f0e7a2c3f4286f3c59fc545ce2e5c79406c4776e9e961a6c5ac79`, median wall **0.386981786 s**
- byte saving: **33,746 B**
- residual wall delta: **+0.053505955 s / +16.04493%**

The byte/runtime tradeoff therefore survives R34: the output-dead-Zstd elision preserves substantial byte improvement, but ordinary product promotion remains blocked by measurable create-time debt.

## Frozen phase-owner decision

Terminal decision: **`PHASE_OWNER_LOCALIZED`**.

Exactly one profiler signature crossed the preregistered transferable-owner floor:

`~:0:<method 'acquire' of '_thread.lock' objects>`

Exclusive/internal-time delta for `no-ordinary-zstd` versus `release-all-exact`:

- Full Backups: **+0.045106405 s** with **+116 calls**
- nested-only: **+0.060874940 s** with **+294 calls**

This clears the frozen law requiring >=10 ms nested-only internal-time delta and positive Full Backups transfer for the same signature.

A useful causal bound follows from the measurement: on Full Backups, the localized lock-acquisition excess (**45.106 ms**) is larger than the observed total residual wall debt (**29.741 ms**). On nested-only, the lock-acquisition excess (**60.875 ms**) likewise exceeds the observed wall debt (**53.506 ms**). This does **not** prove that deleting all lock acquisition would realize those times—the profiler phases overlap through compensation elsewhere—but it does prove that the residual is not merely diffuse codec noise at this resolution. A single synchronization-related phase has enough measured magnitude to explain the outstanding debt.

## Forge interpretation

R34 authorizes a **lowest-sufficient Forge intervention against the synchronization/lock-acquisition owner**, followed by a fresh Builder under unchanged R32 product semantics. It does not authorize workload-name routing, relaxed timing thresholds, changed representation bytes, changed locality law, or release promotion.

The next Builder must distinguish two possibilities before changing canonical product code:

1. **avoidable synchronization architecture:** the output-dead-Zstd arm changes candidate scheduling/future ownership such that work which no longer contributes bytes still causes extra thread coordination or wait/queue transitions; in this case remove or restructure that synchronization while preserving exact candidate/archive identity;
2. **intrinsic scheduling consequence:** the lock delta is a symptom of useful remaining parallel work rather than redundant coordination; in this case profiler-guided lock surgery is not sufficient and this intervention family must be retired or escalated with new causal evidence.

The strongest self-critique is that cProfile's built-in lock signature does not identify the Python caller/queue owner. R34 localizes the *phase class* and establishes transferable magnitude; it does not yet identify a safe mutation point. Editing `threading`, executor width, or product parallelism directly from this receipt would outrun the evidence.

Therefore the next decisive experiment should be a superseding, preregistered Forge Builder that preserves the exact R32 arms/targets and instruments caller-level synchronization ownership (for example executor/future/queue waits) before applying the minimum mutation that can remove only the demonstrated redundant synchronization. Promotion requires exact bytes/reconstruction/locality plus closure of the material runtime regression under the existing >5% **and** >3 ms rule.

## Scoped negative / positive constraint

Positive constraint:

> Under the frozen R32 representation and R34 same-run substrate, residual create-time debt transfers through `_thread.lock.acquire` at >=45 ms on Full Backups and >=60 ms on the nested source; a lowest-sufficient synchronization-owner intervention is evidence-justified.

Negative constraint:

> R34 does not justify generic removal of locks, disabling parallelism, changing worker count, or tuning a corpus-specific threshold. The Python caller of the built-in lock must be resolved causally before product mutation.

## Product/release effect

None yet. This result is Forge diagnostic evidence only. v0.30 remains merge/tag/version/publish locked until exact-candidate release authority is independently satisfied.
