# O229 preregistration — bounded prefix chunker admission (scientific, not product)

**Date:** 2026-10-27 UTC. **Owner:** `agent/phased3-v031-o229-chunker-prefix-admission-20261027`. **Source base:** released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24. This preregistration is written **before** the new instrument, any O229 hosted measurements or outcome.

## Problem / baseline / causal prior

Authentic O228c [run 40534143700](https://github.com/FCMO-AI/.CMPCT/actions/runs/40534143700) with unchanged compiled native CDC and fallback on identical 16-MiB sources measured **opposite-sign complete physical archive effects**: shifted 16,782,978→2,084,044 B (native beneficial), one-period 1,049,818→2,098,336 B (native harmful). O228d reversed construction order and replicated all four whole-archive SHA-256 results exactly [run 40536440994](https://github.com/FCMO-AI/.CMPCT/actions/runs/40536440994). Index-only virtual-run research failed authentic Builder transfer (O228b/c). This fork concerns **physical chunk ownership**, not the rejected virtual-reference grammar or the Reader owned by PR #569. Existing optional native `native/cmpct_cdc.c` can change physical output; this does not authorize enabling it universally. Issue #606 independently owns extreme-size_t CDC risk.

Can a **bounded 4-MiB prefix** sampled from a 16-MiB file predict a valuable native/fallback **whole-file** ownership choice without constructing both full archives? Test the *stronger and simpler* alternatives: always current fixed fallback, always optional native CDC, and a **gifted** best-of-both complete archive oracle (charged bytes, not credited as deployable selection).

## Prospective protocol

All comparisons use unchanged actual released Builder/Reader, `workers=1`, `reproducible=True`, compiled unchanged optional CDC helper confirmed loaded. A strategy uses the exact same generated 16-MiB bytes and file metadata. Modes are enforced by `cmpct.codec._cdc` selection; record actual chunk-length hashes and helper/source identity. Build and verify genuine revision-24 CMPCT archives, complete logical SHA-256 and fixed selective ranges; account for complete archive bytes and physical `data_bytes` and `index_bytes`.

**Frozen admission policy:** build two genuine *prefix-only* 4-MiB archives (native, fallback) on the exact first 4 MiB, then choose native for the full 16-MiB file **only** if `native_prefix_archive_bytes <= 0.80 * fallback_prefix_archive_bytes`; otherwise choose fixed fallback. No tuning, oracle access to full results, or profile-specific route. A 4-MiB prefix restarts chunker state and could be misleading: that is the primary plausible alternative to test. Include *all* prefix sampling creation CPU/wall and RSS in the admitted strategy; never attribute the gifted full-build choice's uncharged information to it.

Frozen diagnostic/training-reference sources: O228b's deterministic `zero`, `one-period`, `two-period`, `shifted`, `structured`, `independent`. **Decision evaluated on separate held-out sources:** alternate-seed periodic (768-KiB repeat); alternate-seed two-period (768-KiB alternating); alternate-seed shifted (768-KiB repeat with periodic inserted drift); boundary-insertion repeat (1-MiB random motif with deterministic 8-KiB insertions); mixed periodic and independent blocks; alternate-seed independent random; **late-shift hostile** (4-MiB independent prefix followed by repeat+drift). These definitions must be implemented exactly before seeing O229 output.

Use **three independent child processes per profile per strategy** for full-fixed, full-native, and admitted-prefix+chosen-full, recording raw repeated wall/CPU and own-process Linux VmHWM, and ensure deterministic complete archive SHA identity per same profile+mode. The child mode must refuse to run if CDC helper unavailable; no silent fixed fallback is acceptable.

## Pre-result decision and kill conditions

Compute held-out **complete-archive** byte regret against the gifted smaller full archive per source, weighted gap closure against always-fixed, and median per-profile charged create wall and CPU against always-fixed. The admission hypothesis passes only if all of:
1. >=75% of the held-out aggregate gifted *byte* headroom relative to always-fixed is captured (provided the gifted gap is >0);
2. no held-out profile pays >25% archive bytes versus its gifted-best alternative;
3. held-out pooled total median charged creation wall and CPU <=1.50x always-fixed, and no held-out strategy has >10 MiB own-process peak VmHWM cost versus same-source fixed;
4. zero semantic mismatches, corruption accepts, source/loader ambiguity or different actual input bytes.

If (1)/(2) fails: `PREFIX_PREDICTOR_FALSIFIED`. If bytes pass but time/RSS fails: `BYTE_HEADROOM_EXECUTION_DEBT`. Only full pass: `BOUNDED_CHUNKER_ADMISSION_SEED`, still research/oracle evidence **not product credit**. No rewrites of criteria after observing hosted results. Inability to load native helper or reconstruct exact source is `INSTRUMENT_INVALID` and must be repaired without claiming a scientific negative.

Counterfactual discriminator if negative: whether a cheap prefix is representative of *later* chunk ownership; first-prefix stationary statistics may be unable to recognize late drift, making any prefix-only policy intrinsically risky. Do not respond with threshold gardening. Assess a materially different full-stream lightweight predictor, stronger bound or retirement. PARETOBONK the competing product priorities before any further family research.

## Safety/compatibility/concurrency

No format revision, file-grammar, Reader, Builder, validator, version, frozen comparator, benchmark or release mutation. Use research-only files and a standalone workflow, isolated in this branch; PR #600 owns original O228 line and PR #569 owns Reader composition. Existing O228 evidence is inherited, not replaced. Open PRs/branch status were inspected before preregistration; no existing O229/prefix admission implementation was found. `docs/discovery/STATE.json` is stale and separately owned by PR #574; do not overwrite it. Preserve original run observations regardless of pass/fail; exact commit and workflow identity must be recorded. Failing this cheap honest rung prohibits full-product integration credit.
