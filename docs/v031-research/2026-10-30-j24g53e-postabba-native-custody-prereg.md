# J24G53e — Post-ABBA native/runtime custody discriminator (preregistration)

**Date/epoch:** 2026-10-30 UTC. **Parent:** exact #785 HEAD `37750c8602411136680371efd420462775e27cbb`. **Scope:** only instrumentation/evidence after the original A/B/B/A work; no release, product, benchmark threshold, corpus, timed-code, version or format mutation. Independent child branch; owner #785 remains unchanged.

## In play → required evidence → present evidence
**In play:** scientific attribution of the persistent red r24/ZIP parity release gate for candidate source-identical to #778 at 10 product/harness Git blobs. **Required:** same exact runner, actual candidate *and* base imported Python and package-owned native dynamic-library provenance; one after-timing physical byte digest per engine; fail-closed source and loaded-map checks. **Present:** provider ABBA runs #40963761747 and #40965146869 (two attempts) failed 3/13/6 CMPCT timing cells with zero observed size regressions; base-native.json SHA-256 `f60f0b0a5d4874044124dc215e556f76522ef0cca9a2da94cdeccef96085dacf`; no candidate native physical SHA in those provider artifacts. These different HEADs/runs do **not** constitute a matched clean A/A product speed proof.

## Primary falsifiable question
Does the exact parity runner import both source trees and *their respective* native `cmpct_core` binaries, or is one side loading a package/binary from a different checkout, user site, or deleted/replaced file? If source ownership is wrong, the timing attribution is invalid; if ownership is correct and native digest matches, native-routing mismatch becomes unlikely, **but** scheduler, cache, binary process timing, dynamic library environment and legitimate remaining performance debt remain unresolved.

## Competing explanation classes
1. **Runtime/candidate source misbinding:** wrong Python module path, `ctypes.CDLL` owner, unexpected native library path, or Linux loader mapping. An explicit post-ABBA process probe may detect it.
2. **Native build differences despite source-equal Git blobs:** binary digest mismatch across candidate/base with same Rust source; potentially build reproducibility or compile context. Record it; do not automatically call it a performance defect.
3. **Equal runtime identity but noisy/systematic execution:** scheduling/caching/phase drift. The probe cannot measure the timed process directly; a stronger per-phase/native child probe would be required if a release decision still depends on this.
4. **Genuine workload regression:** strict existing red comparator remains authoritative; instrumentation must not bypass it.

## Experimental design and noninterference
Run the **original** 7-repetition-per-phase, original corpus, original process boundaries and `tools/check_performance_regression.py` unchanged. After all four A/B/B/A phases (never before or between timed phases), execute a bounded subprocess for each engine from the same `benchmarks` cwd and respective original `PYTHONPATH`, reproducing `cmpct.builder`/`cmpct.reader` imports. Verify Python source owners by resolved path, `native_codec._core._name` agrees with `native_codec._library_path()`, Linux `/proc/self/maps` shows a resident map with matching device/inode, and Git worktree SHA matches exact comparison SHA. Hash physical loaded `.so` in streamed chunks; compare base digest to the original base-native materialization receipt. Persist JSON under `benchmark-artifacts/` that the existing always-uploaded artifact already captures. Do not require candidate/base built binary hashes to match, since compilation may be nondeterministic; report boolean and both hashes.

## Strong controls / disproof / kill
- Mutation/wrong-PYTHONPATH decoy, out-of-tree native file, deleted native mapping, mismatched base-native receipt, wrong commit SHA, missing native file, absent `/proc` mapping must fail closed in local hostile tests. If any accepted, the instrument cannot make a runtime identity claim.
- If probing changes a timed measurement boundary or modifies a frozen comparator, reject this approach.
- If post-ABBA evidence cannot bind actual timed subprocesses, explicitly classify as **after-phase provenance proxy only**, not a full runtime guarantee. A green provenance court cannot erase 3/13/6 official red evidence.
- Any main-branch, previously published lock, source codec/Builder/Reader, version, on-disk format, test threshold or frozen benchmark-file edit invalidates this scope.
- If another owner already writes exactly this slice, reconcile rather than duplicate. Current PR #785 remains owned, and #789/#783 own signed journal replay; #749 owns stage publication; #574 owns discovery state.

## Resource economics / promotion
Expected two Python imports and two native-file streaming SHA passes on the *same* runner after the timing window, and no extra benchmark matrix. The cost is diagnostic/O(loaded library bytes) with bounded RAM. CPU/RSS and proof of actual *timed* process memory are outside claim scope. Product size, create/extract, recovery, portability and security remain inherited tests; no promotion credit or inferred fix of the strict red timing gate.

## Next action after result
If exact-head provider artifact is available, record actual source/loader identities, binary hashes and official pass/fail separately. If no provider run occurred or action was administratively skipped, report unmeasured and don't claim test success. If two physical libraries unexpectedly differ, investigate deterministic build inputs in a bounded independent control. If their hashes match, prioritize scheduler/phase-context attribution or move to the safety-critical integration owner without weakening any red.
