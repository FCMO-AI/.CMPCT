# J24G63 — physical public Writer put/delete one-op replay court: measured result

**Measured product-source context:** public published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24, unchanged. Research head `769c4bc8d1ca20fdf58a112df96b11bd138bedcd` on [draft #805](https://github.com/FCMO-AI/.CMPCT/pull/805), directly stacked on J24G60 #800 `fb5d96cdb8855fe3e01868792e65b79d3d61661d`, with exact inherited shared replay and fail-closed journal code from #795. **No product implementation changed, no merge/release, zero product performance credit.** Original prospective protocol `aa550b7a928dc9a34d363665713379004e331270`; pre-result spread-owner amendment `0c3511f8d2f0b8dc02e4d37992919849c069bdf3` (see below).

## Primary question and actual decision

Does public Writer's one-op **put** or **del** chain have a material Reader-open penalty relative to a physically identical effective-state private full checkpoint at N=2,048 final members/d=63? Each class has a **frozen independent** >=3.0 ms absolute **AND** >=10% of chain wall threshold. The prospective claim that both classes would be material on at least two OSes is **falsified** for put; delete meets the threshold on all three.

| OS | PUT chain / checkpoint (ms) | PUT extra (ms, chain fraction) | PUT decision | DELETE chain / checkpoint (ms) | DELETE extra (ms, chain fraction) | DELETE decision |
|---|---:|---:|---|---:|---:|---|
| Ubuntu 24.04 | 7.4154 / 4.0687 | +3.3467 (45.13%) | MATERIAL | 57.1107 / 4.1842 | +52.9265 (92.67%) | MATERIAL |
| macOS 14 ARM64 | 6.0836 / 3.2817 | +2.8019 (46.06%) | **NOT_MATERIAL** | 51.2758 / 3.5173 | +47.7586 (93.14%) | MATERIAL |
| Windows 2022 | 4.8450 / 2.7821 | +2.0630 (42.58%) | **NOT_MATERIAL** | 33.6662 / 2.6534 | +31.0127 (92.12%) | MATERIAL |

These are per-host medians of eight Reader-open wall readings per variant, in four alternating ABBA/BAAB blocks; 2 operation classes × 2 size families × 4 depths × 16 samples = **256 raw samples/OS, 768 total**. Exact source/head verified; all 3 hosted jobs completed **SUCCESS**, each independent audit re-computed every raw summary and rejected 4/4 hostile receipt edits (12/12 total). A standard-library/host-libzstd second physical-referee pass was run on the original downloaded ZIPs in the activation container; ZIP SHA, raw-observation digest, all 63 committed one-op Zstd/MessagePack/SHA-256 footers, checkpoint appended-prefix identity, actual final checkpoint row-count and physical member bytes matched on all 3 OSes. This external pass is an additional audit, not a shipping-product test.

**A stronger directional control (different sizes and chain depth):** At 2,048 final members, DELETE excess grew from +1.12 / +0.94 / +0.64 ms at d1 (Ubuntu/macOS/Windows) to +14.10 / +11.00 / +8.17 ms at d16, +27.69 / +20.51 / +16.20 ms at d32, and +52.93 / +47.76 / +31.01 ms at d63. At 512 final members and d63, DELETE extra fell to +13.96 / +12.53 / +8.34 ms. This is consistent with repeated per-generation row work, but this experiment did **not** instrument replay versus footer cost by phase; #801's rename-only attribution cannot be transferred numerically to delete.

PUT d63 at n512 was only +1.33 / +0.84 / +0.96 ms; n2048 +3.35 / +2.80 / +2.06 ms. Ubuntu's +3.35ms clears the absolute threshold by only ~0.35ms; two hosts do not clear it. The predeclared two-host hypothesis **fails**, regardless of put's ~43–46% relative chain fraction.

## Whole-system charge and source custody

The public Writer built distinct physical files: PUT replaces 63 deterministic **spread-position** file names via 63 independent real `append_update` calls (64-byte changed payloads), while DELETE starts with 2,111 separate files and removes 63 through the public `append_delete` API to finish with 2,048. This is **not** a same-input put-vs-delete speed comparison. For each kind, checkpoint is only appended on a separate copy of the *same physical chain* after the last operation. Full effective index and all 2,048 logical file hashes agree; both preflight and strong verify accept.

- **PUT chain:** 301,821 bytes on all hosts. Extra private checkpoint: **13,657 B Ubuntu, 13,647 B macOS, 13,676 B Windows** (4.52–4.53% of PUT chain). Exact archive SHA and provider ZIP receipts are in original hosted JSON and ZIP.
- **DELETE chain:** 300,548 bytes on all hosts. Extra private checkpoint: **12,990 B on all hosts** (~4.32% of DELETE chain).
- No new archive bytes are predicted or awarded to a future crossgen optimization. The checkpoint saves Reader-open time only by **paying additional committed bytes**, so it is a lower-rung **charged oracle**, not an in-product zero-cost speedup. The PUT case also pays for new blob bytes in the real Writer; not excluded as a phantom saving.
- Median PUT CPU extra measured +3.347 ms Ubuntu, +2.874 ms macOS, but **Windows +0 ms recorded CPU delta reflects timer granularity** and does not demonstrate zero work. DELETE CPU extra +52.928 ms Ubuntu, +43.652 ms macOS, +31.250 ms Windows. CPU medians are not decomposed nor full process startup.
- Fresh subprocess imports happen **outside** the timer; OS disk cache was not controlled, so the name “cold open” means fresh Reader session, **not cold physical disk**. Linux VmHWM is weak evidence dominated by imports, not a portable peak-RSS or allocation profile. No full create/extract/range/CLI/noise-calibration/current published Wheel comparison has been executed here.

## Exact durable evidence and independent referee

[Hosted final code-head Actions run #41002894731](https://github.com/FCMO-AI/.CMPCT/actions/runs/41002894731), **SUCCESS on Ubuntu, macOS and Windows**. Raw `j24g63-result.json`, independent audit, 4 materialized exact r24 archives/host, source pins, `pip freeze`, source/reader/writer blob identities, logs and SHA-256 ZIP receipts:

| Host | GitHub artifact | ZIP SHA-256 | Raw JSON SHA-256 |
|---|---|---|---|
| Ubuntu | [#12953739513](https://github.com/FCMO-AI/.CMPCT/actions/runs/41002894731/artifacts/12953739513) | `9fb77b445a5be261c1e19a5ac16b98cc410869f3249ff3b4e45cafd5e97d3864` | `0aba93ea6ee8b261157b42ab5e2aee268229890a7fb4fa3b76e09e6a82cf3a80` |
| macOS | [#12953848943](https://github.com/FCMO-AI/.CMPCT/actions/runs/41002894731/artifacts/12953848943) | `154becd2e97b448ee83062f378af717f5ec3b45cca85bd6d203d33332dae0d54` | `91779569cd98ca12cafde9c4bdb0c7ca2eff44a63edb12f8bd3d24dc2a9ee133` |
| Windows | [#12954321978](https://github.com/FCMO-AI/.CMPCT/actions/runs/41002894731/artifacts/12954321978) | `930f431e523cd2cdc3bdba11b55b0ae9c730fddc44a6d40ca732c0837d21a24b` | `4aacda5e82f9f6dd094fb51874ceebba7a6fbb29a1949836e778d7965bb8c566` |

The ZIP SHA-256 was independently recomputed in the activation container and exactly matched original GitHub upload logs on all three hosts. The physically retained chain bytes happened to be identical across tested hosts per operation, but checkpoint bytes differ slightly for PUT; there is **no asserted cross-platform deterministic checkpoint guarantee**. SHA-256 here detects accidental/malicious byte differences under the declared format; it is not a digital origin signature.

## Rejected instrument / contradictions / self-critique

An initial research HEAD picked only the first 63 sorted paths, systematically making PUT's early-exit linear scan unusually cheap. **Before inspecting its timing result**, J24G63b was committed and published as a separate prospective input-strengthening amendment; only spread-owner final HEAD `769c4bc8...` earns the reported evidence. Earlier CI (including cancelled runs) remains historical and is not averaged together.

A superseded macOS [hosted run #41002643422](https://github.com/FCMO-AI/.CMPCT/actions/runs/41002643422) failed because an adversarial raw-sample mutation did **not** alter the median, slipping past the first receipt auditor's limited arithmetic checks. The follow-on instrument bound **every** raw sample through an explicit SHA-256 digest, and independent audit now rejects 4/4 forged receipt variations on every platform. This was a **real auditor defect**, not a CMPCT Reader defect; both the red run and its correction remain recorded. After a first standalone re-audit, a Windows artifact path used `\` separators while the portable archive uses `/`; the detached re-audit normalized it and all three physical ZIPs passed. This is audit-path portability, not product evidence.

**Other limitations:** no signed per-member xattrs/owner overrides, hardlink topology, crashes/truncated footer tails, concurrent writers, adversarial mutation in this run, native journal, host-cold disk, memory-allocation cost, full release parity or comparable external ZIP/Zstd semantics. The 2 classes have different initial file counts and cannot be used for a literal same-input A/B of two compression algorithms.

## Decisional handoff

- **Priority changes:** repeated public DELETE generations have a robust measured Reader-open debt across all three OSes; give an **independent deletion/mixed-op cross-generation reuse hypothesis** consideration *after* cheap causal replay/footer attribution and checking existing #346/#358 and #797. This is a stronger product-reachability target than merely tuning wide-single-generation indexing.
- **Do not treat PUT as broadly material:** only Ubuntu crossed the prospectively frozen 3ms absolute floor; retain its small measurable overhead but do not reopen its family without a distinct structural control.
- **Keep #804 isolated:** it already owns rename-only cross-generation factoring; no duplicate rename implementation. Shared replay product ownership remains #795. #574 owns Discovery STATE; unchanged.
- **Cheapest next falsifier:** source-bound delete-only replay vs footer instrumentation (or source-exact simpler no-new-index state reuse) over the **same** public 2048/d63 physical archive, then decide whether architecture can eliminate repeated work *without* adding the 12,990 checkpoint bytes or exporting RSS/recovery debt. A lower-rung win cannot authorize product release; the next product implementation needs Reader/preflight exact identity, fsmeta, hardlinks, recovery, resource bounds, full CPU/RSS, all-host ABI, historical gates and common-file full release benchmark evidence.

**Scientific result:** a strong positive for public DELETE, a scoped negative for public PUT under the original two-host hurdle, and a causal mechanism narrowed to a specific public Writer workload family. **Product implementation advanced: none. Release credit: zero.**
