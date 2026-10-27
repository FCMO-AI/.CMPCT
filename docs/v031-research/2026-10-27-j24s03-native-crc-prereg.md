# J24S03 — preregistered native zlib CRC zero-run operator court

Date: 2026-10-27 UTC (2026-10-26 Mexico City). Source parent: J24S02 negative PR #547 at `4ee91f80285451ce472897d58d4bb77f479394cb`. **This file is committed before result-bearing candidate implementation and execution.** Research-only, no CMPCT Reader, builder, format, release, or frozen comparator changes.

## Question and costly inherited observation
J24S01 #525 verified a strict same-content sparse-hole raw-DEFLATE oracle, still charging SHA-256 and CRC32 of complete logical data. J24S02 #547 falsified uncached Python GF(2) zero CRC algebra: 0.54x conventional speed on mixed sparse, versus 1.26x on all-zero. Its profiling implicated thousands of repeatedly built Python matrices. The **materially different** mechanism here is zlib's *native reusable length operator* (`crc32_combine_gen`, `crc32_combine_op`), not another Python matrix or threshold tweak.

## Falsifiable prospective hypothesis
On the same J24S01/J24S02 synthetic 256-MiB all-zero and mixed sparse 256-MiB families, a cold-initialized per-encode native operator cache will produce >=5% complete encoder wall reduction versus **incremental native zlib.crc32 control** on at least one DEFLATE level (1 or 6) *in each family*, while <=2% slower on 64-MiB no-hole for both levels. Also evaluate one structurally heterogeneous irregular-length sparse family with many distinct zero-run lengths. Promote an oracle-only research continuation only if this third family does **not** regress beyond 2% on both levels. Never count a favorable microbench as a product win. Full SHA-256 of every logical byte remains required, and raw-DEFLATE bytes must be identical across arms.

## Courts and controls, frozen in advance
- Real zlib C interface through `ctypes`, only if the library exports both native symbols; otherwise report unavailable and terminate as infrastructure capability, not a loss. Validate function ABI on small exact adversarial checks before trusting timing.
- Baseline `chunk`: J24S02's incremental `zlib.crc32(bytes, running)` over every known-zero span.
- Stronger simple control `bulk`: ordinary native CRC on zero runs using a *per-encode allocated* 8-MiB buffer; explicit memory cost.
- Candidate `native_cache`: detect consecutive known-zero spans, compute their exact CRC from verified 64-KiB seed doubling (native `crc32_combine`), memoize by **run length** bounded to <=256 entries, then native combine operator. Charge every cold op/zero-CRC creation inside the timed encoder. Cache overflow must fall back to baseline, not unbounded growth.
- Mechanism negative control `native_uncached`: same C ABI per hole-run with all operator generation charged but without reusing operator cache. This tests whether caching (rather than just native implementation) matters.
- Outside timed encoder but per-source verification: bounded independent raw-DEFLATE decoder recomputes all SHA256, CRC32 and logical lengths, including zero regions. No weaker checksum oracle.
- Same deterministic input spans and data for all modes, interleaved order reversed on alternate repeats, >=3 runs per mode/level/family, raw per-run times, CPU, bytes, digest, cache count, operator generations, allocated memory accounting, library identity, result source SHA and process timestamp.
- Heterogeneous family: 256 MiB logical, deterministic variable holes of many lengths and bounded 4-KiB data slices, no identity-by-filename policy, same suffix rules and SHA/CRC verification. Any candidate that only wins perfectly aligned all-zero spans must be limited or rejected.

## Disproof and scope
Fail if any input SHA, exact CRC, complete raw-DEFLATE stream bytes, independent decode, length or hostile length test differ, regardless of performance. Reject general optimization if mixed fails >=5% win or irregular overhead >2%, if no-hole >2% slowdown, or if operator-memory bound cannot be enforced. Equal speed means no claimed improvement. Experimental Linux only is not cross-platform proof. CPU/RSS/process startup (if not separately measured), filesystem I/O, complete CMPCT ZIP64 Reader, sparse admission, modified concurrent source, recovery and release promotion remain unmeasured until their exact separate courts.

## Counterfactual discriminator
Compare C-native operator generation versus cached generation at identical full-work semantics. If both win, matrix rebuild *in Python* was the causal ownership problem and caching may be unnecessary; if only cache wins, reusable native operator is the causal leverage. If neither wins, abandon CRC-run algebra as a current sparse product optimization and prioritize more material ZIP64 or authenticity debt. No post-result relaxation; preserving a negative is success.
