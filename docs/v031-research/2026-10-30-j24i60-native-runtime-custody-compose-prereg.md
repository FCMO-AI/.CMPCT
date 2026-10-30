# J24I60 — Post-ABBA native mapping provenance on source-identical full-PR parity stack

**Status: preregistered before implementation. DRAFT research/evidence-enablement; no release, merger, version, format, ABI, performance-threshold or comparator change.** Date 2026-10-30 UTC.

## Source authority and baseline
Canonical `FCMO-AI/.CMPCT` published v0.30.0/r24; v0.31 is unmerged research. Integrate only on #835 exact `09e38915b79a83964cc816d5130251b3e748121e`, whose exact parent is #832 `fe7669f7f1a07720187219200e24a972fa650f6b`. The substantive full-PR classifier is already proven; original Actions #41065848583 benchmark and failed-job retry both reported official timing **FAIL** with **identical shipping source and identical input tree**. Across the retries nested/CLI/create changed sign (+10.618% -> -7.88%), while tiny/library/create remained red. Original native materializer recorded only the **base** ELF hash `f60f0b0a5d4874044124dc215e556f76522ef0cca9a2da94cdeccef96085dacf`. No candidate-mapped ELF receipt exists for those runs.

## Primary question, prospective predictions and alternatives
Does a fresh post-ABBA subprocess with exactly the benchmark's per-engine `PYTHONPATH` and cwd map the native extension of the expected source checkout to the correct Linux device/inode, and do candidate and base have identical physical SHA-256? **Prediction H1:** source ownership is valid and both actual loaded native ELF hashes agree. **Alternative H2:** missing/wrong native mapping, dirty source or different physical ELF identifies a build/provenance mechanism; fail closed and preserve the adverse result. **Kill/narrow condition:** a valid post-ABBA equal-hash receipt can only narrow *fresh-process* native-identity uncertainty; it cannot prove timed subprocesses used those same binaries, explain timing, or change either official FAIL. Missing post-ABBA or malformed receipt => UNMEASURED; never PASS.

## No duplicated research owner
The original owner [#790](https://github.com/FCMO-AI/.CMPCT/pull/790) already built and independently hosted `tools/j24g53e_native_runtime_custody.py` and `tests/test_j24g53e_native_runtime_custody.py` with Linux executable mmap device/inode, source-Git bytes, base receipt, and ten hostile tests. Reuse **both exact Git blobs**, no new native-identity implementation. Port only its post-comparator/always-execute workflow block into the **#835** workflow, keeping all #320 classifier source bytes, original four timed phases, seven repetitions per phase, exact corpus, original unchanged gate/evaluator, summaries and artifact uploads.

## Evidence ladder and controls
1. Before mutation, confirm current HEAD, overlapping owner #790 and #835, source/parent; commit this prereg first.
2. Exact-donor blob copies; check Git SHA identity and workflow diff showing only the bounded new after-comparator block.
3. Run inherited 10-case hostile tribunal (wrong Git HEAD, dirty source, symlink escape, missing native, wrong receipt, replacement inode, source alias) locally or in exact-head hosted General Tests; check CI topology and engineering evidence.
4. Source-exact hosted ABBA, compare old baseline to new; preserve official gate result independently of native probe. Extract original uploaded JSON, candidate/base mapped device/inode, SHA, Python source identity, running HEAD and execution timestamps. Record true evidence HEAD, provider run/job ID and artifact SHA before any promotion claim.
5. If new hosted job remains pending, leave decision **PENDING**. No self-issued PASS from a green workflow summary.

## Cost and strong self-critique
Additional post-ABBA two-process probe scans two physical libraries and source files (streamed bounded-memory hashing); CPU/I/O small relative to long ABBA but historical duplicate provider compute is material. This is a narrow decision-critical provenance discriminator after repeated source-exact gate instabilities, not another blind threshold test. Previous #790 proved equal mapped ELF on a *different* PR, which is not transferable to #835's provider run. After a correct equal receipt, cross-process scheduling/caches, timed-phase actual mappings and compiled-system/build determinism remain unmeasured. Do not continue repeating this lineage if it does not change the next decision.

## Release and discovery boundary
No changes to archive bytes, full create/extract work, memory, fsmeta, hardlink identity, integrity, signed journal, recovery or portability. Linux-only `/proc/self/maps` is bounded to Ubuntu runner and no macOS/Windows claim is inferred. No `docs/discovery/STATE.json` edit: #574 owns state reconciliation and the current main cache is stale. This PR is a separately claimed donor **integration**, not ownership of the #790 research mechanism or an authority to merge/release.
