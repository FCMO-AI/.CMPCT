# O216 — exception-only fixed-chunk reference validator: preregistered falsifier

**Date:** 2026-10-27 UTC. **Type:** research-only, no Reader/product/format changes.  
**Starting source:** J24C02 #569 exact `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; S_CHUNKS validation implementation `src/cmpct/validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`. Released v0.30.0/r24 unchanged.

## Observed product debt
Source-exact J24C02b on Ubuntu found a valid authenticated index with 65,536 or 262,144 repeated fixed-chunk references incurs, respectively, +25.56 ms / 27.25x and +102.05 ms / 28.51x cold-open cost versus identical #567 Reader without S_CHUNKS early admission. O215's narrow incorrect selective read is repaired in #569, but that cost blocks promotion. Its owner retains implementation; this branch **does not** write to #569/#568 or propose bypassing structural validation.

## One primary falsifiable question
Is most added cold-open cost from generating a Python label and invoking `_ref` on **every valid chunk reference** rather than from the unavoidable reference traversal itself, and can an exception-only equivalent validation kernel meaningfully rehabilitate the #569 product debt?

### Hypothesis
For ordinary serialized r24 int refs, branch on fast type/range checks and call the **unchanged** `_ref(value,count,f'file ... chunk {ci}')` only when the ref fails. Keep the same total-of-referenced-blob-sizes check, array/list shape requirement, and exception for invalid types, booleans, negative/out-of-range refs, repeated refs and invalid declared sizes. Equivalent output on every tested hostile input is a hard gate. **No shortcut for repeated IDs; no threshold, sampling, approximate proof or new decoder semantics.**

### Strongest controls
A: original `_validate_storage` from exact #569 validator; B: fast-path substitute injected at runtime only for S_CHUNKS; all other storage tags delegate to the original. Run both on **identical** authenticated root-versioned r24 archives constructed once using existing O215 builder-independent `_make_archive`. Interleave ABBA within one Python host with full Reader open/close after import warmup, preserving raw repetitions and CPU/wall. Include 1, 4,096, 65,536, 262,144 repeated refs and held-out diverse valid refs if cheaply available. Run source-exact hostile tests for invalid/bool/negative/out-of-range references and declared total mismatch; import the unchanged original O215/O212/O214 test suite as a control.

### Materiality / decisions fixed before observation
1. **Safety gate:** any difference in acceptance/rejection or exception semantics for root-versioned positive/hostile cases kills the candidate.
2. **Mechanism supported:** >=2x cost-kernel improvement at 65,536 and 262,144 with matched valid serialized inputs. This is a micro/mechanism claim only.
3. **Whole Reader viability:** even if mechanism wins, the existing material-debt threshold still applies. If B remains >2x vs unguarded parent **and** >5 ms at 65,536 or >20 ms at 262,144, label `LOCAL_FASTPATH_INSUFFICIENT_FOR_PROMOTION` and do not recommend integration as the complete repair. A positive whole-Reader gain requires direct measurements, never extrapolation from a kernel.
4. No full release credit without full portability, recovery, native, file-custody, 4GiB ZIP64 and valid historical gates.

### Alternative explanations and anti-local-optimum
Costs may instead arise from entire-index traversal, Python per-ref type checks, mmap/index decode, large repeated index materialization or full hash checks; moving validation to first-use would avoid open-time work but **weakens early malformed-index rejection**, so it is not a free equivalent control. Since one unvisited reference could be invalid, a strict all-reference proof has worst-case Omega(N) reference-inspection cost without an authenticated independent summary or changed representation. If exception-only branching remains material debt, stop threshold gardening and investigate *representation or native-batch admission / proof ownership* rather than optimizing the same loop indefinitely.

## Concurrency, evidence, and limitations
Existing owner #569 is responsible for four-way composition; #568 owns original O215 correction. This is independent **mechanism and full-Reader replication** on a separate branch, not a competing Reader implementation. Preserve original negative evidence; record raw receipts/host source identity, including losses. `docs/discovery/STATE.json` is a staleable cache, not modified without decision-changing new truth. No releases or merges, and no rewriting frozen benchmarks.
