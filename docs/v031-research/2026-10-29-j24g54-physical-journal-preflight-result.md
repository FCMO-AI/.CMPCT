# J24G54 — installed signed journal/preflight parity result (physical evidence)

**Result cutoff: 2026-10-29 22:33 UTC.** **Research decision: CONFIRMED false rejection on the unmerged candidate.** Product correction: **none**. PR [#786](https://github.com/FCMO-AI/.CMPCT/pull/786), defect [#787](https://github.com/FCMO-AI/.CMPCT/issues/787). This is not a release result.

## Frozen prospective claim and ownership
Preregistration was committed **first**, at `86942804086bf70508d0594add2dd667237e88d9`, before code or result-bearing CI. Exact product parent is J24G52 / #783 `47ddedbeb844a8d59e9d142910c6705301214ce0`. Tested scientific HEAD `cacf07fc8c5f4d02966342afd480c95a2a28d667` has only new prereg, tests, independent audit, workflow. Reader blob `c82ab200bf849f844587683992f0c702cc39059a`, Validation blob `10d67553d1c8ff5399dbadc0fcfd5f3c54ea846a`, Writer blob `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11` remain inherited and source-locked. Installed Python file bytes matched each checkout file on both hosts.

The hypothesis was that valid Builder-native xattr+actual journal deletion leaves obsolete signed fsmeta ordinals in preflight validation even though Reader rekeys the effective index. **This happened in both relevant cases on both tested hosts.** The controls falsifying broad "all journal deletes fail" also passed.

## Result-bearing installed tests and physical custody
[Actions 40966404316](https://github.com/FCMO-AI/.CMPCT/actions/runs/40966404316) completed SUCCESS for Ubuntu 24.04 and macOS 14. Each host installed the exact source candidate, generated a first-party archive on its own filesystem, set native binary xattrs, verified original Builder capture and baseline preflight, performed actual `append_delete("b-delete.bin")`, checked Reader strong verify and original survivor content, strictly extracted and read back native xattr bytes, then evaluated the **same physical file** through preflight.

| Test case | Base preflight | Post-delete Reader verify/strict native extraction | Post-delete preflight | Outcome |
| --- | --- | --- | --- | --- |
| Both survivors `a-owner`, `z-survivor` have xattrs | pass | pass; 2 files & both xattrs exact | **rejects** `fsmeta xattrs file references missing object 2` | physical mismatch |
| Only late `z-survivor` has xattr | pass | pass; exact survivor xattr | **same rejection** | physical mismatch |
| Only early `a-owner` has xattr | pass | pass; exact survivor xattr | pass; files=2 | negative control |
| No xattrs | pass | pass; content exact | pass; files=2 | negative control |

**Test counts:** Ubuntu **4/4 pass**, macOS **4/4 pass**; these are **negative-reproduction** tests, not product success. Test-run wall for these four small cases: Ubuntu 0.08 s, macOS 0.19 s; this is NOT Reader throughput evidence.

**Independent physical referee:** Python `research/j24g54/independent_journal_referee.py` imports external Zstandard/MessagePack/stdlib, not CMPCT. It authenticated r24 primary and checkpoint index SHA-256, the two ordered original signed owners, unchanged physical body records, the actual latest committed delta opcode `del b-delete.bin`, and new footer SHA-256/parent pointer. Both hosts rejected **5/5** independent physical perturbations: latest footer digest, delta payload, prior checkpoint digest, primary index, and blob header. Mutations of original prefix bytes were applied consistently to both before/after inputs so that the artifact-prefix check alone could not trivially reject them.

**Body SHA-256 (both hosts, both-survivors case):**
`5e7b7f288d7c808ed3dce53c4bfd69746a0b8e2a85f325a63ee97d8327aa799a`.

Original provider artifacts:
- [Ubuntu artifact 12937557425](https://github.com/FCMO-AI/.CMPCT/actions/runs/40966404316/artifacts/12937557425) — GitHub-reported ZIP SHA-256 `fa017975c8e14fe6057804146a3e729c46977bb7478637479d890a18382dc944`.
- [macOS artifact 12937987413](https://github.com/FCMO-AI/.CMPCT/actions/runs/40966404316/artifacts/12937987413) — GitHub-reported ZIP SHA-256 `424016814e18103e2ded3d7d983808e743c59fbdd8888ddaae78626ea817f169`.

The hosted referee read the actual input files and independently asserted the receipts; these ZIP digests are provider-reported, **not** separately downloaded for another local audit.

## Causal mechanism, negative knowledge, scope
The physical initial signed `fsmeta.xattrs` row for `z-survivor.bin` was ordinal **2** before deletion. After `b-delete.bin` is removed, only ordinals 0 and 1 exist. The Reader path-bound algorithm creates its effective `[0,1]` records, whereas `validation._apply_delta` mutates `files` but retains the obsolete ordinal **2**. Therefore the independently authenticated **valid archive** fails `preflight_archive()`'s own structural ordinal check. This is a **false rejection**, not incorrect content or a proven tamper bypass.

Counterfactual: an up-front signed-ordinal-vs-path-lineage property test could have predicted this difference without two OS CI jobs, but only the physical experiment could establish that it survives actual Builder serialization, journal commit/footer, Reader decode and strict native xattr readback. Transferable lesson: where two parsers materialize the same authenticated generation through separate transformations, exercise their *effective identity semantics* on one immutable signed archive before declaring a shared integrity guarantee. A single episode does not justify changing discovery policy.

Scope: child #783 unmerged, source identity pinned. **Not tested**: official published v0.30 wheel, native Rust Reader, Windows xattr restore, UID/GID physical ownership, 64-delta checkpoint, all journal operations, full CPU/RSS, create/extract economic parity, external ZIP/Zstd comparison, power-fail recovery. The observation is not permission to weaken validation.

## Decision, concurrency and next executable engineering work
**Decision changed:** J24G52's abstract concern is now physical binary evidence, tracked by issue #787. No collision occurred with narrow preflight parity implementation; #783 owns inode guard, #773 owns journal fsmeta rekey, #778 owns composed integrity, #574 owns stale discovery state. No source code, frozen evaluator, release threshold, benchmark, version or discovery policy changed.

**Highest-leverage next target:** owners should reconcile Validator and Reader replay with a single bounded/genuinely equivalent transform that preserves strict malformed-op rejection, older-footer recovery, correct path/owner/alias semantics and parser limits. Acceptance must prove real valid signed xattrs on delete/insert/rename, delete+recreate same path, hardlink xattr conflict, checkpoints at depth 64, and hostile footer/index cases. Do not merge this test-only branch as a repair. If a promotion owner can't integrate, the issue is a concrete blocking correctness debt, not a generic request for more benchmarks.

**General CI:** specialized two-host court and engineering evidence rerun are successful; unrelated project-wide General Tests, native/fuzz and legacy frozen checks remain separate and are not reinterpreted here. Published v0.30.0/r24 main remains unchanged.
