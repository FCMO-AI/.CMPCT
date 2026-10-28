# J24C18 — Falsify fused native sealing before a third Reader implementation

Date: 2026-10-28 UTC. **Prospective hosted replication protocol**, written before the GitHub-hosted instrument or CI workflow. Source exact parent [#676](https://github.com/FCMO-AI/.CMPCT/pull/676) at `3b6a73f9205f40f11124cd9ff332407e52cebb93`, Reader blob `7196d8569962d86932a6aff27aed9e0b443bbb25`, C scanner `src/cmpct/_fastscan_abi3.c` from that exact source. This is a separate **SCIENCE ONLY** branch; no product, format, benchmarks, validator, version, release, or existing test edits.

## Primary scientific question

J24C17 sealed authenticated S_CHUNKS refs with `refs=tuple(storage[1])` after the existing native full proof; [two direct installed courts](https://github.com/FCMO-AI/.CMPCT/pull/676) found +13–24% wall regressions versus the original unsealed J24C13 Reader in all twelve paired scenarios. Can the native proof *also create the immutable Python tuple during its existing pass* with less wall/CPU and acceptable RSS than the stronger simpler control (the unchanged native scan followed by CPython's optimized `tuple(refs)`)? The C stable ABI's per-element `Py_INCREF`/`PyTuple_SetItem` may cost **more** than CPython's specialized bulk tuple constructor. Avoid building a whole new product branch unless a direct control defeats that concern.

## Pilot (observed before this registration; excluded from prospective evidence)

A self-contained CPython3.13 Linux exploratory component micro compared a C full per-ref size scan + Python `tuple(refs)` against a C scan that fills a tuple per element. Five distinct data shapes were NOT tested and **the C implementation omitted checkpoint marks**. For 65,536 / 262,144 / 1,048,576 heterogeneous refs, tentative fused/control wall ratios were 1.153 / 1.206 / 1.227 (higher=worse). This pilot **cannot support a claim about CMPCT Reader or a preregistered result** and is a *reason to perform a bounded stronger-control falsifier*, not proof of future results.

## Prospective hosted protocol

1. Pin one self-contained exact algorithmic **component** to #676's native full scanner: exact list/type/owner-size checks, signed logical total, and one prefix every 256 refs. Compute reference scan + bounded checkpoint tuple identically in both arms; only differ in whether a final frozen tuple is constructed by CPython `tuple(refs)` **after native proof** (control), or by per-element stable-ABI C tuple fills **inside that same proof pass** (candidate). The returned proof and frozen bytes must be identical. Avoid Python-level row traversal in one arm only.
2. Same authenticated-shaped synthetic table (not an archive), fixed deterministic refs and blob descriptors. Test 65,536 / 262,144 / 1,048,576 refs, 4 owners with unequal and zero lengths, plus 256-owner held-out shape. Randomized but fixed seed, no fixture identity in production policy. Native module built from current runner's compiler, test within fresh Python subprocesses, no imported CMPCT product module.
3. At least 9 alternated A/B repetitions per case and host (Ubuntu/macOS/Windows CPython3.11 where provider available). Each repetition measures wall and process CPU of *one full scan and freeze* with fresh objects; retain all per-run observations, source/host/python identity, exact equality/checksums, and memory HWM where supported. Record process startup separately or exclude from timed region. Preserve timing noise; do not cherry-pick a median.
4. Independent stdlib referee recomputes medians, validates control/candidate output hashes and expected counts, enforces raw record set and source custody, rejects hostile altered receipts. No claimed cross-host end-to-end Reader/packaging performance.

## Decision and kill conditions

The candidate needs >=5% sustained *full proof+freeze* wall improvement (median candidate/control <=0.95) on both 65k and 262k profiles **on every measured host**, without meaningful CPU/RSS regression (>8MiB HWM delta when measurable) or byte/proof difference. A fail on those conditions **retires this specific C-per-item fused tuple route** as a poor rehabilitation action; even a pass earns **only component-level warrant** and next requires installed source-exact Reader comparisons against #676 and original #662, J24C16 mutation exactness, Q1/Q6/Q64, Windows, memory, distribution and release floors. A failure must not loosen this bar or silently change the simpler control.

## Other framings considered

- Keep #676's existing sealed-tuple proof: proven narrow mutation protection, with measured +13–24% cost but no new implementation risk.
- Freeze before parsing/index allocation with a schema-owned immutable representation: meaningfully different representation boundary, but parser and journal mutation compatibility must be shown, and current C requires exact built-in lists.
- Per-read revalidate all mutable metadata or add Python list fingerprint: changes Q64 economics or fails adversarial same-hash/in-place changes. Not an honest low-cost seal.
- Only seal the rows with high expected query counts: query workloads are unknown at Reader open; admission heuristics must not violate exactness and cannot be tuned on fixture identity.

## Concurrency and scientific status

Independent non-product child of #676. No write to #676, #662, #672, #574, `docs/discovery/STATE.json`, frozen files or policies. Other owners may continue. This study does NOT claim security equivalence or solve mutable blob metadata (explicitly unsealed by #676). Source SHA/PR and CI run/artifact identity must be recorded when evidence arrives. The current discovery state on main is staleable and not a claim lock. After decisive evidence, preserve the raw negative, retire or narrow this exact route; reopen representation ownership only if a structurally different mechanism changes the information gained.
