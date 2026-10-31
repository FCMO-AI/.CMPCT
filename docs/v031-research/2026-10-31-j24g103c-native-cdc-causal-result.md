# J24G103c — bound and isolate Python-versus-native CDC cutpoint cost

**Date: 2026-10-31 UTC; scientific micro only.** Frozen *before implementation* at [`1048423bb571b55201d044f9f3801bafd019c524`](https://github.com/FCMO-AI/.CMPCT/commit/1048423bb571b55201d044f9f3801bafd019c524). This is a causal follow-up to [J24G103's hosted O0 byte result](2026-10-31-j24g103-cdc-root-shift-result.md), not a revision to its frozen outcome.

## Strongest negative motivating the test
J24G103 completed eight authentic SHA-keyed root O0 storage comparisons and passed the preregistered byte screen. On its exact hosted source `199fe4355059d82f67934992375c225a509606a8`, full Python gear-based two-root model creation was **110.40–133.43×** slower than the existing fixed-block physical model, with both including the distinct SHA payload/reference charges. This does not establish intrinsic CDC cost: the original loops over every physical byte in Python, whereas fixed chunk slicing and SHA use native code.

The relevant mature algorithm family is [Xia et al., FastCDC, USENIX ATC 2016](https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia). FastCDC demonstrates optimized CDC is practical, but this research's cutpoint rule, table, min/max and non-normalized mask are **not** identical to FastCDC; do not transfer its throughput or chunk distributions as this product's benchmarks.

## Method and locked predictor
Frozen source physical pair ZIPs: Ubuntu SHA-256 `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b`, Windows-origin `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab`; both producer SHA `129edec976efe8bb604584517de39553487fec34`. Four Builder+63 DELETE authentic A/B histories, two fixed target sizes 4096 and 16384, exactly J24G103 SHA-derived gear table and mathematical cut law.

`research/j24g103c_native_cuts.c` implements a bounded uint64 recurrence and emits offsets only (no changes to CMPCT or archive bytes). `research/j24g103c_native_micro.py` uses `ctypes` to call it, then performs the **same Python SHA-256 chunk-key and complete two-root accounting** as the original oracle. It checks full cutpoint identity and final stored bytes on source original/terminal roots plus early shift, midpoint shift, random control and **the independently discovered one-third adversarial insertion/deletion**. It collects **seven balanced raw wall and CPU observations per variant** on the same host; source provenance and full physical scan are independently pinned. `research/j24g103c_sanitizer_smoke.c` checks nine array lengths at two targets, short output capacity, invalid target and null-pointer rejection under ASan/UBSan.

**Frozen cost test:** native complete model >=5× faster than Python on every four original 4KiB-target source pairs, <=4× same-root fixed-block J24G102 model on at least three of those four. Failure is retained, not retuned.

## Local O0 observation — not exact-hosted-product proof
One local Linux runtime compiled the cutpoint kernel with `cc -O3 -shared -fPIC -std=c11 -Wall -Wextra -Werror`, and ran the same original physical SHA-matched source ZIPs:

| Source | Native/Python full-model wall speedup | Native versus fixed full-model wall |
|---|---:|---:|
| Ubuntu-origin 4096 members, 4KiB | 96.23× | 1.90× |
| Ubuntu-origin 8192 members, 4KiB | 97.29× | 1.94× |
| Windows-origin 4096 members, 4KiB | 96.32× | 2.03× |
| Windows-origin 8192 members, 4KiB | 98.09× | 1.90× |

The second 16KiB target independently achieved ~101–110× versus Python, with ~2.13–2.22× versus fixed (all four). Full SHA-keyed wire bytes and cutpoint identities matched for all eight physical comparisons. The known Ubuntu-origin 4K members/16KiB target one-third-position counterexample still produced exact identical native/Python cutpoints; **the native accelerator cannot erase the storage loss and may not change its threshold**. Local raw seven-repetition report SHA-256 `868352fb4f9fa2b7acf3a1cc213d7ca5fa2eca10c56b35cd26aacf53b533a99b`. Sanitized test on the original local C kernel: `ASAN_UBSAN_BOUNDED_CUTS_PASS 9_LENGTHS_2_TARGETS`. Separate local source C SHA `c1f5eb5b635037970db381f303a703d177b0c658406ecc5da44524928447a35a`; the repository C source contains the same recurrence but has its own Git identity. These local measurements are **not evidence of a hosted exact-HEAD result**.

## Hosted boundary and limitations
The branch's `.github/workflows/v031-j24g103-cdc-shift-o0.yml` now additionally compiles the repository's C source under a source-exact GitHub runner, runs the native parity and seven-pair court against original provider ZIPs, and executes ASan/UBSan. **Until the corresponding exact-HEAD workflow finishes, its result is PENDING**. Do not infer success from the local copy or from an earlier cached artifact.

The C micro refutes only the argument that the measured 100× Python cost is inherent to the Gear boundary model. Even at ~2× fixed work, it is not shown to win complete archived bytes/Writer/Reader/GC/durability for any generic real root-mutation workload. Its source is Linux-only C research and not reviewed as a stable portable ABI. No independent OS matrix, cold-process timing, RSS, true disk writes, selective read, crash safety or multiwriter CAS proof; no published Reader/Writer code modified.

## Decision and lowest-cost remaining product route
**`CPU_OWNER_IS_PYTHON_PER_BYTE_DISPATCH — NATIVE_O0_MICRO_SURVIVES_LOCALLY — NO_PRODUCT_PROMOTION`.** A competent native scanner may make CDC practical *as a component*, so preserve it as a bounded alternative rather than mark all CDC impossible. However, the separate posthoc two positional storage misses (1.276×), simple J24G99 rolling tail, and a much simpler same-format #823 Owned Reader route block CDC-root promotion. Do not repeat threshold/gear sweeps; reopen the family only if realistic non-append root compaction shows a generic storage/custody advantage with a complete same-semantics product A/B. No Discovery state/policy change or release/format/version bump was earned.
