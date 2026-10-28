# J24I02 preregistration — Signed-budget/fingerprint × failed Reader-open ownership

**Frozen before source or test transplantation.** Date: 2026-10-28 UTC. Scope: an integration/Forge convergence court, not a new primitive, release, format, policy or performance threshold.

## Authority and exact baselines

- Immediate parent: #699 `4de43609046ceaba93902e6680af3b4059aee49f`, Reader blob `20f6e257a07a61a4c1aebe23ae23e4109d6c41c8`. This exact composed B06 signed-negative-budget + v0.31 prospective fingerprint source has 9/9 completed-success PR workflows: [tests #40758840447](https://github.com/FCMO-AI/.CMPCT/actions/runs/40758840447), 810 passes; [real r24/ZIP parity #40758840163](https://github.com/FCMO-AI/.CMPCT/actions/runs/40758840163), PASS/zero confirmed regressions; [three-host B06 #40758840498](https://github.com/FCMO-AI/.CMPCT/actions/runs/40758840498), 16 tests per host. A green result does not override remaining signed hardlink/symlink/sparse quota counterexamples.
- Independent proved single-mechanism owner: #283 `7ac0376ffed9530d1ba3617b8b7d7400b418b62c`, Reader blob `2ba573b5dcf349327c70cf05b6462e8ee933fba3`, original focused test Git blob `7e75fffaa4e7337463390299edbd18ef3bb7fe7b`. [Hosted same-runner source-exact court #40019609015](https://github.com/FCMO-AI/.CMPCT/actions/runs/40019609015): original constructor leaked file while exception traceback remained alive; candidate closed fd/mmap and passed four focused cases. Other unions of that same mechanism (#285/#321) exist, but neither #699 signed-budget+fingerprint branch nor its exact source has the constructor protection.
- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24. v0.31 parent is unmerged.

## One primary question / predicted result

Can the **exact, already-tested constructor** from #283 be copied into #699, with all Reader bytes **outside `__init__` unchanged**, preserving #699's signed-budget and prospective-source-fingerprint CI while synchronously closing fds/maps on malformed-header, mmap failure and canonical-path collision?

**Prediction:** original #283 tests pass 4/4 on this union without weakening archive semantics; all #699 tests and hosted r24/ZIP zero-byte/performance gates remain green. No measurable byte or runtime improvement is claimed. Merely an exception-safety, resource-owner composition. No redesign of cleanup, no change to Reader's normal read/extract/verify code.

## Alternatives / BONK

1. Implement independent cleanup logic: rejected as duplicate ownership research when #283 already provides source-exact candidate+tests.
2. Import all of #283 Reader: rejected because doing so would **erase** #699 signed quota guard and potentially its prospective custody.
3. Add an eager full `preflight_archive()` to normal open: rejected as a different contract and avoidable full-index work.
4. **Selected:** copy only #283 `__init__` and its original no-GC test file, then add a zero-cost source-custody comparison in a hosted test. This integration differs materially from #285/#321 because its parent contains B06/fingerprint instead of the raw-digest or duplicate-map families.

## Precise falsifiers and evidence rungs

- Before transplant: check #699 original Reader substring outside `__init__` and preserve its Git blob identity; record #283 exact constructor string and test SHA. Compare new source outside `__init__` after transplant. Any difference is an immediate failure.
- After transplant: run original four #283 tests **on a wheel installed from the new exact HEAD**, not by copying functions; check for live-Exception ownership and an independently frozen r24 golden.
- Host actual general tests, native/fuzz/custody/version and **real** r24/ZIP parity; an aggregate green with skipped performance is not enough to certify the parity gate. No narrower isolated-owner results substitute for union exact-head evidence.
- Reject/narrow if retained-traceback fd/map leak persists, B06 guard/valid extraction changes, any new general failure appears, or a confirmed size/time regression exceeds inherited hard gates.
- Keep the same source/content semantics and do not alter frozen criteria, legacy release lock or fingerprint test evaluator.

## Safety and release boundary

This does not fix [signed hardlink #693](https://github.com/FCMO-AI/.CMPCT/pull/693), [symlink #697](https://github.com/FCMO-AI/.CMPCT/pull/697), or [sparse extent #701](https://github.com/FCMO-AI/.CMPCT/issues/701) budget undercount. The new PR stays DRAFT/NO MERGE even with green checks. Cross-kind effective geometry, inode custody and safe extraction are independently owned by #609/#615/#569/#573/#690 and others. Do not overwrite those owners.

## Opposing interpretation and kill condition

The constructor change could accidentally move or drop #699's B06 guard, or the test could pass due to garbage collection. Source-only-outside-constructor equality and original `retained traceback` handle spies are required to reject these false explanations. Cleanup handling itself is proven on #283's old source; whether it composes with #699 remains **unmeasured until the new exact-head CI runs**.

## Decision documentation

Keep positive and negative receipts in this PR. Do not edit `docs/discovery/STATE.json` or normative policy for this narrow integration, and do not promote based solely on test counts.
