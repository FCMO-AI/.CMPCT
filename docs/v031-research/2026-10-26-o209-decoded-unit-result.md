# O209 result — 1 MiB logical range is not a physical decoded-memory bound

**Date:** 2026-10-26 UTC. **Decision:** `MATERIAL_PHYSICAL_UNIT_RSS_AMPLIFICATION`. **Evidence class:** genuine installed Reader, controlled selective-read host-science; **not full ZIP64 product/release performance**.

## Frozen provenance and actual host run

- Released reference: CMPCT v0.30.0, on-disk revision 24. Active experimental Reader parent: O193 PR #521 at `392112ce859db5a7f85be593c82d1cabc1f5131f`.
- **Preregistration preceded instrument:** `0e7718217e2d69d4708beee588696be382897aec`, file `docs/v031-research/2026-10-26-o209-decoded-unit-prereg.md`. Registered `>=32 MiB` fresh-child VmHWM materiality threshold, same-logical-source A/B and negative controls before any results.
- Actual source/CI HEAD: `9ab707a45e7de09f79b427b56e832f763762bfc1`; installed Reader Git blob: `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`; court blob: `0371095ee4830b5e74793577083a147946ae9d91`.
- Exact-head [GitHub Actions run #40415689169](https://github.com/FCMO-AI/.CMPCT/actions/runs/40415689169): the source-exact O209 job completed **SUCCESS**.
- Retained [raw artifact #12694962723](https://github.com/FCMO-AI/.CMPCT/actions/runs/40415689169/artifacts/12694962723), ZIP SHA-256 `ab314d689ed0ae57fea210219aaa0f71c9e8f4cb7013bfa986c43e754fbf969b`. Its JSON was downloaded and independently parsed after the run; 18 distinct (variant, scenario, repetition) receipts, all selected-range SHA checks TRUE and full producer-only verify PASS.

## Genuine controlled archives

Both CMPCT revision-24 archives contain precisely the **same 67,108,864 logical source bytes**, one regular member `payload.bin`, the same member SHA256 `e2cb9873a8fbf8708fd5137ad2737bc1da5dfafcaff139a057b989e6c4cc16ec`, mode/mtime and a properly versioned, physically framed, separately verified original CMPCT index. Synthetic content: 1024 SHAKE256-deterministic bytes repeated.

| Product-relevant unit | Single physical Zstd S_BLOB | 64 independent Zstd S_CHUNKS |
|---|---:|---:|
| Source logical bytes | 67,108,864 | 67,108,864 |
| Native Zstd physical decoded-unit size | 67,108,864 B | 1,048,576 B |
| Original physical CMPCT archive bytes | **7,612 B** | **77,506 B** |
| Compressed blob payload bytes | 7,180 B | 72,448 B |
| Build wall, producer only | 0.123952 s | 0.183559 s |
| Full `CMPCT.verify()` and `read()` | PASS | PASS |
| One selected 1 MiB range SHA | exact equal | exact equal |

Archive byte difference is real: small single-frame storage saves 69,894 B here but exports a major range-access peak-memory cost. Thus B is a stronger locality control, **not a strictly Pareto-dominant new product layout**.

## Fresh-process measurements

Each one of three repetitions used alternating **fresh Python child processes** per variant/scenario. The producer's 64MiB input construction and full-file verification never occurred inside the measured children. Kernel `/proc/self/status` VmHWM before/after the actual Reader operation; no `tracemalloc`.

| Fresh-child scenario | Single Zstd frame: peak increment KiB (three trials) | 64 chunks: peak increment KiB (three trials) |
|---|---|---|
| Open only | 432 / 328 / 332 | 576 / 512 / 572 |
| One 1 MiB middle range | **131,380 / 131,348 / 131,392** | **2,696 / 2,520 / 2,556** |
| Three disjoint 1 MiB ranges | 132,348 / 132,384 / 132,564 | 4,712 / 4,692 / 4,716 |

One middle range medians: A **131,380 KiB**, B **2,556 KiB**, net difference **128,824 KiB = 125.8046875 MiB**. The **preregistered 32 MiB** materiality boundary was exceeded by a large margin.

One-middle-range actual median child wall: A **34.241 ms**, B **2.112 ms**, on this host/profile only. Three-range actual medians: A ~103.112 ms, B ~5.214 ms. Repeated A requests re-decode the >2MiB non-cached physical frame; B decodes a different independently bounded 1MiB blob for each selected range.

The actual production `CMPCT._blob()` calls full-sized native Zstd decompression. The package's `native_codec.decompress` creates a ctypes output buffer of **declared physical `usize`** and returns an independent `dst.raw` bytes object. Two physical-output-sized live buffers are a plausible source-level explanation for the roughly 128MiB peak increase seen on a 64MiB frame; it is an inference from inspected source, **not a native heap allocation trace**.

## Why the decision changed

**Falsified product-friendly interpretation:** `read_range(max=1MiB)` or O193's 1MiB requested ZIP64 fragments alone bound the **real decoded-memory footprint to ~1MiB**. They bound only the logical requested return slice. The true decoded unit is a physical blob; one 64MiB unit caused ~125.8MiB greater fresh-child process peak than independent 1MiB units for an identical requested logical slice.

**Confirmed within scope:** original Reader, original revision-24 wire grammar, valid full-file integrity, real Linux process memory; observed full stored-byte tradeoff. This is a scientific resource-envelope result **not a shipped ZIP64 correctness failure or crash**.

**Not established:** that ordinary CMPCT Builder would choose this extremely large single frame; general-case malicious size bounds; full 4GiB ZIP64 export peak, extraction, Windows/macOS resource behavior, cold-device I/O, other codecs, per-unit streaming feasibility, release-scoreboard wins or a free codec optimisation. One host and highly repetitive synthetic content are material generality limits.

## Strongest critique / cheapest follow-on

A fix that simply imposes 1MiB physical frames would spend an extra **69,894 bytes** on this one highly redundant 64MiB source, so it cannot be promoted as a free win. A generic product solution must bound physical decode-unit memory, retain safe exact data fallback, and compare layout/seek locality versus complete archive bytes and create/extract CPU/RSS on adversarial held-out sources. Alternative approaches: exact source-owned streaming/partial decode with fully charged checksums, bounded format-aware physical ownership, or independently bounded range-aligned frames selected only when overall product economics justify. Hostile input requires explicit preflight/resource ceilings; never let per-frame requests drive unbounded process memory.

**Counterfactual lesson:** inspecting `read_range -> _blob -> native_codec.decompress` would have flagged the logical/physical distinction earlier; only fresh-child VmHWM resolves actual materiality. Preserve prior O195 low-yield sparse extent indexing decision rather than retesting it. No discovery-policy amendment earned from this one scientific result.

No changes to Reader, Builder, on-disk format, native ABI, evaluator, historical benchmark, frozen thresholds or release law. Parent #521 retains implementation ownership; PR #548 remains draft, merge/release unearned.

## Handoff

- **Evidence now settled** for this bounded host/frame question. Research O209 changed decision: 1MiB logical request does **not** guarantee 1MiB decoded-memory use.
- **Pending:** full source-exact generic CI checks for documentation-final HEAD, general model/physical-unit admission, held-out source families, ZIP64 whole-system memory, portability, update/recovery adversarial handling.
- **Highest-value independent next step:** owner-facing resource-envelope design alternative or a bounded held-out large-frame case, not another 64MiB same-pattern repeat nor parallel Reader implementation.
