# O50 — Joint Builder correctness court: Windows hardlinks × unsupported special entries

**Date:** 2026-10-25 UTC. **Classification:** hosted product-correctness candidate, not released product. **Decision:** scoped O47 × O48 source composition **SUPPORTED on clean-installed Python 3.11 across Ubuntu/macOS/Windows**, with POSIX-only test limitations. Do not merge or award release credit until inherited gates/owner review.

## Authority and source custody

Canonical development at experiment start: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Source-parent O47 PR #401 `29d9688ae6bff6d1eccc27f019893866abe5b5c3`, original Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`. O48 PR #402 at `55c9309d9c94bc29d258c2595ea69279cf7c1b63`, O48 test blob `d4a22da7d634a5dd6a1e1fb132ed1ceae2249ab6`. O50 preregistration commit `29761e3c2282bfdbc361c2de750a481eda71cf2b` predates product/test changes. Independent draft PR #405 intentionally stacked on #401.

Composed actual Builder source Git blob `21a9ec696df13961c25301654feb607a7e161a4c`. Source diff relative to O47: **five lines added, one line removed** in `src/cmpct/builder.py`, matching O48's fail-closed unsupported-entry type dispatch; Win32 `os.stat` physical-identity logic remains untouched. No Reader/Writer/native/format/benchmark changes. Original O47 test source blob `6c00ae49eea075957453d6d7238d988add6eedee` and O48 original test blob remain unchanged.

## Exact-source hosted results

**Result-bearing scientific workflow:** [run 40158321271](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158321271), source HEAD `0bd8ccc1709cc7899c28eaaa6fde6d2944529b22`, composed Builder blob `21a9ec696df13961c25301654feb607a7e161a4c`. The three jobs use genuine `pip install .` `cmpct.builder` / `cmpct.reader` outside the checkout tree, confirmed by their actual job logs.

| Host | Real original/new tests collected | Pass | Explicit skips | Failure/error |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 / Python 3.11 | 11 | 11 | 0 | 0 |
| macOS 14 / Python 3.11 | 11 | 11 | 0 | 0 |
| Windows 2025 / Python 3.11 | 11 | 6 | 5 POSIX-only | 0 |

The originals exercise Windows source-to-destination *physical* hardlink identity and equal-content independent files, and POSIX FIFO + bound AF_UNIX special refusal, ordinary deterministic tree, and CLI archive preservation. O50 additionally builds a mixed-source link+FIFO tree: refuses incomplete creation/no overwrite and reconstructs exact physical aliases after removing the FIFO. The independent **O47 pinned original-source Builder** is reconstructed from its exact Git file SHA and executed against the composed installed Builder on two held-out supported trees. Complete original and candidate archive byte streams match on each same-input/same-runner fixture; extracted members are strongly verified with r24 Reader. A further same-input A/B control establishes original O47 Builder **accepts and silently omits a FIFO**, while the composed candidate **raises and preserves a preexisting archive**. The control is real executable code, not a mock or inferred code path. This is an improvement in source admission truth, not added special-file encoding.

## Scientific negatives and instrumentation corrections

- First O50 [run 40157973488](https://github.com/FCMO-AI/.CMPCT/actions/runs/40157973488): on macOS 8 original/new initial tests actually passed but CI script misread absent counters on the `<testsuites>` root; workflow red. Fixed by aggregating actual child `<testsuite>` counters, never removing failed assertions.
- Second O50 [run 40158133205](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158133205): eight original/new non-parent tests passed on Ubuntu and macOS; two source-exact O47 parent tests failed before running parent Builder because the dynamically loaded module was missing `sys.modules` registration needed by CPython `dataclasses` with postponed annotations. Registered the isolated module before evaluating the exact unmodified parent source, preserving comparison assertions.
- Inherited O47 standalone workflow required its original Builder blob and naturally failed that SHA check on the composed source; **branch-local pin updated to the new exact SHA**, retaining its two original tests on all three hosts. This is a provenance update for a changed source, not weakening an evaluator.
- CI topology found the O50 workflow lacked mandatory `# ci-lane: fast`; branch-only workflow comment was added after result-bearing run. No test/product source changed.
- The scientific result is bounded: 11 collected tests / host, including Windows 5 explicit POSIX skips; not a complete installed-package/native/ABI/fuzz/release/cold-create proof.

## Product cost and non-claims

No new compression, stored-byte gain, decoded-work reduction, RSS, wall/CPU or portability-performance win is claimed. O47 adds an `os.stat` per Win32 regular file; O48 adds an unsupported-type branch. Fully measured r24/ZIP release parity (same exact source/corpus, zero deterministic size regression, original 5%+3ms timed guard), packaging breadth, memory, native and hostile archive gates remain binding. Administrative r24/ZIP workflow SUCCESS with its deep `performance` job SKIPPED is **NO RELEASE PERFORMANCE CREDIT**. Neither supported OS behavior nor output semantic scope may be broadened to FIFO/socket archive reconstruction, network shares, ReFS, source mutation atomicity or cross-host identical bytes.

## Counterfactual and discovery status

A direct pre-implementation diff comparison identified the only shared conflict point, so a bounded real composition plus original test reuse was lower-cost and higher-value than inventing another serializer or running a new representation study. Real held-out complete-byte parity and genuine 3-host physical samefile controls are the decision-changing evidence; docs alone are not. No concurrency collision was identified; parent #401 and #402 branches are unchanged. No discovery-engine normative policy or STATE mutation was earned.

## Remaining owner handoff / next decision

Offer exact source + CI proof to #401 and #402 owners. Reconcile their changes under legitimate integration ownership only after the full O50 final-head general/native/fuzz/policy/workflow/comparator corpus evidence. O50 remains **DRAFT / NO MERGE / NO RELEASE / FORMAT r24 / version v0.30.0**. The release comparison and Win32 syscall cost are still unmeasured.
