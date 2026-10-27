# O224 — Phase-isolated open-memory attribution on genuine signed r24 indexes

Date: 2026-10-27 UTC. **Prospective scientific preregistration committed before measurement implementation or hosted outcomes.** No product, release, native ABI, format or policy changes.

## Authority, inherited evidence and ownership

CMPCT released main `80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0, on-disk revision 24. Unmerged composed Reader owner J24C02 [#569](https://github.com/FCMO-AI/.CMPCT/pull/569) is `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, with `src/cmpct/reader.py` blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. O223 [#587](https://github.com/FCMO-AI/.CMPCT/pull/587), head `9a92c2846dbe1a8dddf6c7224b8f84cb7cfda5cf`, found a ~453–497 MiB process HWM at 262,144 physical references **already during open-only**, falsifying its former 'futures drive that HWM' hypothesis. O219 [#578](https://github.com/FCMO-AI/.CMPCT/pull/578) measured same-wire parse+validation *time* but not exact Reader phase memory. This work only measures memory ownership and will not duplicate either Reader code or native fast-path ownership.

## Locked scientific question and baseline

On the same authenticated revision-24 bytes as O223, which phase actually owns the *incremental* high-water Resident Set Size: zstd decompression, MessagePack unpacking, file-table canonicalization, strict `_validate_storage`, or later mmap/open housekeeping? Can a **science-only omission of strict validation** on already independently authenticated valid fixtures substantially change the peak? This omission is an unsafe **counterfactual** and shall never be claimed as a product improvement, applied to hostile input, or merged into the Reader.

Strong control: unmodified original Reader on identical wire, and a no-validation counterfactual in a separate child. Additional uninstrumented child controls check instrumentation's RSS impact. The existing O223 open-only baseline is inherited evidence, not a new claim. Stage snapshots use Linux `/proc/self/status` VmRSS/VmHWM and `/proc/self/smaps_rollup` Rss/Private_Clean/Private_Dirty/Pss; `tracemalloc` is optional and always reported as separate measurement rather than conflating Python heap with total RSS. Independent child processes avoid stale high-water marks. The same source-installed Reader is verified byte-for-byte against checked-out `reader.py`. Each archive's SHA-256 and expected logical bytes are unchanged. Only Ubuntu 24.04/Python 3.12 scope is claimed.

## Prospective experiment design

Two structures `S_CHUNKS`/`S_CDC` × two layouts repeated/eight owners × `N=4,096,65,536,262,144` × `baseline/no_validation` × three fresh processes = **72 primary observations**, plus phase instrumentation controls. Instrumented Reader events: before open, after physical index decompress, after MessagePack parse, start/end of storage validator, immediately after full open and close. If decompression uses the footer instead of `zd`, explicitly mark that boundary missing rather than inventing an attribution. Keep stage monotonic process VmHWM separate from instantaneous RSS and measure absolute values, increments and tracemalloc current/peak when available. No direct parser/validator structural mutation other than the separately labelled unsafe counterfactual.

## Decision rules (before seeing hosted data)

For all four 262,144-ref profiles, compare the uninstrumented baseline's fresh-child final VmHWM with instrumented original: if instrumentation raises HWM by >15% in any profile, declare stage sizing **measurement-perturbed** and do not assign a dominant phase from the instrumented run. Otherwise define total increment = final VmHWM - before-open VmHWM; if one *recorded* stage accounts for >=60% of total incremental HWM in all four profiles and contributes >=64 MiB in each, label that stage `DOMINANT_PHASE_SCOPED`. If not, label `MIXED_OR_UNRESOLVED`. A missing stage boundary or non-monotonic HWM sequence invalidates phase allocation for that sample; it does not justify replacing raw samples. In uninstrumented paired valid-fixture runs, a >=64 MiB reduction in no-validation median HWM in all four profiles licenses only `VALIDATOR_COUNTERFACTUAL_HEADROOM`; else `VALIDATOR_HWM_NOT_PROVEN`.

The independent auditor must verify counts, source SHA, exact archive hashes, expected control outputs, successful parser/Reader opens, response identity, stage ordering, all raw trial values and medians. Preserve every negative and measurement limitation. This is neither a memory resource-limit proof nor a product release gate.

## BONK alternatives and falsifiers

- Simply removing `ThreadPoolExecutor.map`: already falsified as explanation of O223 peak HWM.
- Another native validator/loop: O216/O218/O219 established scoped speed and incomplete product economics, not this RSS owner.
- Rewriting wire/index representation: too expensive before phase attribution; use strongest simple control.
- `tracemalloc` alone: omits native allocator and memory mappings; compare with kernel RSS and fresh-process controls instead.
- Heap snapshots can themselves cause RSS amplification; the 15% perturbation gate prevents declaring self-induced measurements as product defects.
- Same-input archive bytes, authenticated index, strict validation and source installed identity must remain intact for all baseline product claims.

## Scientific exit and coordination

This research branch stacks on O223 #587 but changes no Reader/validator. Notify owner #569 and O223 #587 of a decisive result, with exact workflow run, source SHA, raw artefact and limits. Do not modify the Discovery Engine's `STATE.json` (current stale cache already has separate reconciliation owner #574) unless material decision-changing source-truth requires reconciliation and the relevant owner approves. Keep positive/negative data append-only, no threshold changes, no merge/release. Follow with whichever single causal owner this court actually identifies, not another speculative policy tweak.
