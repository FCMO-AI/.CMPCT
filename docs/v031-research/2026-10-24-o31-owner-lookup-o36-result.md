# O36 — Exact-hit canonical owner lookup research result

**Status:** `RESEARCH_POSITIVE / OWNER_HANDOFF / NOT_PRODUCT_CODE`. Date 2026-10-24 UTC. Do not merge/release directly from this scientific oracle; released v0.30.0/r24 and all v0.31 product, format, ABI, release and comparator gates remain unchanged.

## Precise source and question
Original O31 product source [PR #385](https://github.com/FCMO-AI/.CMPCT/pull/385): `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader Git blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`. Independent O33 [PR #387](https://github.com/FCMO-AI/.CMPCT/pull/387) before O36 measured a genuine cold constructor debt: O28 9.083ms versus O31 12.091ms for 4,096 hardlinks (+3.008ms/+33.1%). O36 preregistration first landed at `a3bf85831d3bc7bf823cf04888d0b309b7d4c687`, before writing any instrument or oracle patch. The raw O33 source bound instrument blob `8aabcc100843475068031e39a8a4cfb74edfddac` was inherited unchanged.

**One question:** Can a Reader replaying an SHA-committed hardlink graph reuse a *previously canonically admitted exact raw owner name* instead of reparsing that same target for each alias, while preserving the full parser fallback and all original adversarial semantics?

## Method / provenance
The [O36 source-bound hosted court](https://github.com/FCMO-AI/.CMPCT/actions/runs/40141754876) ran to **SUCCESS** on experimentally executable HEAD `60645723d9d09d5149d9635559a720d5ec7f2a7c`. It verifies O31's original Reader blob and O33's unmodified generator blob. A separate *detached temporary worktree* of O31 was modified by one exact guarded textual substitution and subjected to a one-path Git diff assertion. **No `src/cmpct/` changes were committed to O36 or O31.** Worktree Reader/native package provenance was checked, then **25 unchanged inherited O25/O27/O28/O31/signed-tree tests passed on Ubuntu 24.04**, including real hostile cycle/path/destination and canonical-backslash positives. This is a focused Ubuntu court, not a three-platform installed-wheel product certification.

The original O33 fixture builder emitted six authentic SHA-index-committed physical revision-24 archives; complete preflight, Reader exact read/range/SHA/verify was checked outside the timing intervals. O36 compared unchanged O31 vs a **disposable only** two-branch Reader expression on the exact same archives, with **8 independent Python subprocesses per source per archive, ABBA/BAAB**, yielding 96 independent process observations. CPU, constructor wall, full process wall, imports, post-constructor RSS, high-water RSS and all raw results are preserved in [artifact 12579032283](https://github.com/FCMO-AI/.CMPCT/actions/runs/40141754876/artifacts/12579032283).

Source-bound experimental full JSON receipt SHA-256: `6b27ce272a8edf82d91d92e4ca30c7ab3fb11d5132b1b4a84c4a06bae8696e05`.

## Direct fresh-process same-runner medians

| Authenticated topology | Count | O31 constructor ms | Exact-hit oracle constructor ms | Recovered ms | Relative speedup |
|---|---:|---:|---:|---:|---:|
| Regular, no links | 512 | 2.374 | 2.390 | -0.015 | 0.994× |
| Direct hardlink fanout | 512 | 3.099 | 2.698 | +0.401 | 1.148× |
| Hardlink chain | 512 | 3.046 | 2.674 | +0.372 | 1.139× |
| Regular, no links | 4,096 | 7.490 | 7.585 | -0.094 | 0.988× |
| **Direct hardlink fanout** | **4,096** | **12.867** | **9.927** | **+2.940** | **1.296×** |
| Hardlink chain | 4,096 | 12.518 | 9.777 | +2.741 | 1.280× |

For 4,096 direct links: **constructor CPU 12.984ms → 10.041ms**, complete subprocess **85.566ms → 82.557ms**; post-constructor RSS **26,556 KiB → 26,498 KiB**; high-water increment **2,968 KiB → 2,934 KiB**. The no-link 4,096 control grew only 0.094ms and does **not** cross either part of the prospective regression test. These are same-runner O36 measurements, not the historical O33 runner's absolute timings.

## Prospective outcome and falsification
O36 preregistered **at least 2.0ms recovered in 4,096-link fanout**, no material plain-4096 slowdown simultaneously ≥10% AND ≥3ms, with unchanged inherited hostile controls. All those conditions passed in this single hosted experimental comparison. **Decision: `WORTH_PRODUCT_OWNER_REVIEW_NOT_RELEASE`**. It is material causal evidence that repeated parsing of *already admitted target names* explains much of the O33 indexed-name CPU debt. The 512-link benefit is only ~0.4ms; this is not a universal startup speedup claim.

If a later actual product branch under owner #385 cannot reproduce ≥2ms of gain while passing its full cross-platform installed, adversarial, byte parity and recovery gates, retire or narrow the shortcut without weakening those gates.

## Exact conditional mechanism
Existing O31 first canonical-validates **all stored logical row names** and rejects canonical duplicates before processing links. Therefore when a signed target string is already *exactly* a key in the admitted `self.by`, its canonical lexical validity and unique identity are already established. The disposable source tries:
```python
target_name = link[0]
if target_name in self.by:
    node = target_name
else:
    try:
        target_key, _ = canonical_logical_path(target_name)
    except ValueError as exc:
        raise IOError(f'unsafe hardlink target: {node!r}: {exc}') from exc
    node = canonical_names.get(target_key, target_name)
```
All nonexact spellings, including accepted mixed backslash separators, continue through the **unchanged** O31 path-policy function. Original invalid-target and cycle refusal are preserved in the focused court. The complete patch itself is uploaded as `disposable-prototype.patch` in the artifact, not committed to `src/cmpct`.

## Strongest negative / limits / counterfactual
This is a Linux worktree **research prototype**, not a merged Reader, not an installed wheel from the changed source, and not an independent byte-level external conformance vector. Eight fresh Python interpreters per condition do not flush host filesystem caches. The fixture corpus intentionally shares one RAW physical owner and varies authenticated logical graph geometry, not wide codecs or huge multi-blob archive I/O. Unmeasured: other hardware, Windows and macOS performance, full archive create/size, filesystem update/recovery, all malformed Wire/MessagePack possibilities, source mutation races, native ABI and whole-tree extraction economics. The pre-existing original O33 evidence remains intact, not replaced.

Infrastructure evidence negatives: the first hosted O36 court [40141517022](https://github.com/FCMO-AI/.CMPCT/actions/runs/40141517022) failed before any prototype/test/benchmark at a YAML multiline Python string-indentation mismatch (expected owner snippet occurred 0 times). A syntax-preserving YAML-indent repair at `60645723d9d09d5149d9635559a720d5ec7f2a7c` made the exact guarded match occur once; no source or evaluator criteria changed. Engineering Evidence initially found missing PR headings and was corrected in PR metadata only; subsequent exact-head dossier court [40141780244](https://github.com/FCMO-AI/.CMPCT/actions/runs/40141780244) passed. Both infra negatives remain visible.

**Counterfactual transferable lesson:** one prospective exact-name hit against *already authenticated immutable row identity* may eliminate redundant parsing and its CPU cost without a second canonical index. Earlier source inspection plus a direct original/product A/B would have identified this owner sooner than generic cache redesign or broad benchmark gardening; this is one case, so no global discovery-policy change is earned.

## Handoff / next executable action
Give the **sole O31 product owner #385** the exact disposable patch + raw receipt. If the owner adopts, land the minimal conditional path on a fresh reconciled O31 codebase (not in this PR), validate all original O25/O27/O28/O31 hostile tests on three OS, installed-clean-wheel O35 source custody, full General/Native/Fuzz/recovery and unmodified official r24 ZIP parity; repeat exact O36 ABBA on that *final actual product HEAD* and inspect memory/CPU/no-link controls. Do not merge or release from a scientific seed. Preserve O34's unrelated compact-r24 full-matrix negative separately under its owner.

All result details derive from hosted action output and uploaded raw artifact; no local artificial microbenchmark, historical claim transfer or new compressor claim.
