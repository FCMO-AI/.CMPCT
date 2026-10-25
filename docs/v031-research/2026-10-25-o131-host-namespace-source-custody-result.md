# O131 — Host namespace admission × open-source archive custody: result

Date: 2026-10-25 UTC
Status: POSITIVE SCOPED COMPOSITION; INHERITED MACOS NEGATIVE OPEN; NOT RELEASE EVIDENCE
Preregistration: `docs/v031-research/2026-10-25-o131-host-namespace-and-source-custody-union-prereg.md` @ commit `d98c93d6ecdb85694b9231950f0c6120b9240e27`
PR: https://github.com/FCMO-AI/.CMPCT/pull/479 (draft; stacked on #472)
Result-bearing exact source HEAD: `cd6c0b06b580c47d3bc3092e90694c7daece0ea0`
Reader source blob: `5ce013f80c0220c7e7771041c60740a7111fff8a`; path policy exact #336 blob `91fc335eea8fb18c3899511f416c8abe96c48f80`.
Release: v0.30.0 / format r24 unchanged.

## Mechanism and controls

Source-exact #336 host namespace admission and Win32 symlink checks were incorporated into #472's Reader whose static per-destination source archive inode and output hardlink/symlink guard remain present. Four #336 test files are byte-identical to their original Git blobs; #472 O124 twelve-cell oracle and nine parent regression assertions remain unchanged.

An initial genuine installed three-host run at `5eaf70292d98f56e2235231ea1a8d7a0e4889c86` **failed** on all hosts: 1 Linux/2 Windows/4 macOS originally positive artificial Reader shell fixtures constructed via `CMPCT.__new__` without an opened source `self.f`. Calling unconditional `fstat(self.f.fileno())` raised `AttributeError` inside inherited filename/path tests. This was a genuine *composition compatibility defect*, not evidence of an actual archive source mutation. Corrected by explicitly guarding the inode comparison only when the Reader has an actual open `self.f`; normal `CMPCT.__init__` always sets this source. The original namespace tests are unchanged. This narrows the guarantee: source-inode protection applies to real opened Readers, not fabricated zero-source test shells.

## Direct hosted evidence — exact source HEAD

[O131 tri-platform run 40246773178](https://github.com/FCMO-AI/.CMPCT/actions/runs/40246773178): **3 / 3 jobs SUCCESS**, installed packaged CMPCT, exact Git-blob identity, genuine host filesystem for the two new independent O131 tests, and four byte-identical inherited #336 test files.

| Host | Original portable/APFS/union tests + two O131 source/case controls | Original Win32 owner tests | Job |
| --- | --- | --- | --- |
| Ubuntu | 15 passed, 10 skipped | 27 passed, 11 skipped | SUCCESS |
| Windows | 17 passed, 8 skipped | 37 passed, 1 skipped | SUCCESS |
| macOS | 22 passed, 3 skipped | 26 passed, 11 skipped; **1 documented host-domain deselection** | SUCCESS |

Total actually executed **144 passed** (15+27+17+37+22+26), **44 skipped**, one Mac host-domain deselection inherited from #336. No test failure in O131 tri-platform. The Mac deselected original test assumes Linux-style `Case`/`case` positive spelling, which is incompatible with the conservative Mac admission policy. Native Mac alias rejection tests were executed.

[O124 inherited-source scientific run 40246773131](https://github.com/FCMO-AI/.CMPCT/actions/runs/40246773131): Ubuntu SUCCESS, **9 unchanged inherited tests PASS** and **12-cell three-engine oracle PASS**. macOS scientific **12-cell source-inode oracle PASS**, but full job **FAIL** because 1 of 9 unchanged parent cases, the `sparse` fixture, produced a different storage mode than its preregistered direct-truncate assertion. macOS: 8 PASS / 1 FAIL original tests. This reproduces the same inherited failure observed on #472 [run 40239479273](https://github.com/FCMO-AI/.CMPCT/actions/runs/40239479273), without weakening any test or modifying source semantics. Do **not** count O124 as full green on Mac.

[Engineering Evidence 40246882355](https://github.com/FCMO-AI/.CMPCT/actions/runs/40246882355): SUCCESS at result-bearing HEAD after completing normative PR dossier markers. First iterations failed missing mandatory section names and `quality-ratchet`, preserved as administrative negatives.

## Decision / self-critique

Four static guard mechanisms coexist on one source-exact installed Reader under the evaluated three hosts; genuine archive source-inode self-alias cases also pass their focused court on both POSIX hosts. This is new combined product-candidate evidence, **not a merged product fix**. O131 does not claim concurrency-resistant directory-tree confinement; the existing per-leaf checks are TOCTOU-raceable. Mac original storage-mode fixture is red. Remaining evidence debt: general tests on final head, native/full fuzz, Windows source archive inode adversarial court, Unicode/8.3/reparse behavior, deep path performance, output metadata, full r24/ZIP candidate parity and coherent release gates. No data-reduction, compression, runtime or format wins have been measured. A green administrative ZIP-performance workflow whose comparison job was SKIPPED grants no product evidence.

**Next executable:** resolve/classify macOS sparse-mode fixture with actual physical `st_blocks` and Builder admission before changing any fixture; preserve test original. Then coordinate with #336/#472 owners to integrate exact guarded Reader under more comprehensive destination/publication safety and run true full product release parity. Do not create another alias preflight variant.

No `docs/discovery/STATE.json` mutation: PR #440 owns its updates. No earned general discovery-policy change.
