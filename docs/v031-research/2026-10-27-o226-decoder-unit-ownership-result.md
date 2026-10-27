# O226 — 3 MiB decoded-unit ownership transfer result

**Date:** 2026-10-27 UTC. **Decision:** `BOUNDED_SERIAL_TRANSFER` (**RESEARCH ONLY**, NOT product promotion). Immutable preregistration first: `ec882b0fc0ddf5e204d008f46ca5585be33ed6d2`; instrument `408d78f6bcc40f35e5e3f826f61e88ff1e41704c`, auditor `5d37e88568fe8ef881d2a185904d3e26a51c94f1`. Source exact test HEAD: `8cce28d99ceede565da8b38ac98185fb31a11509`.

## Hosted original evidence and independent audit

[GitHub Actions run #40499036449](https://github.com/FCMO-AI/.CMPCT/actions/runs/40499036449) **SUCCESS**; original artifact [#12731832946](https://github.com/FCMO-AI/.CMPCT/actions/runs/40499036449/artifacts/12731832946), SHA-256 `80c39af8e488080037743023c2be5b007e11b88ce0ad72f5ea85b083d96a691b`; immutable JSON evidence SHA-256 `4f70bebc1842bce56a1fc1429c6874f4e56e15de16a517df19338eaa5fbf6881`. Independent ZIP/provider SHA and CRC, original receipt regrouping/median recomputation, source/header identity, 108 distinct child PIDs, six positive SHA and six referenced CRC negative controls: **PASS**. Raw repeated measurements and logs live in artifact; GitHub workflow marks auditor success. This does not authenticate every historical v0.30 benchmark.

## Exact mechanism and controls

Published CMPCT v0.30.0, on-disk r24 unchanged. Authenticated same-wire r24 archives with 12 physically distinct 3 MiB owners, once (36 MiB logical) or twice (72 MiB logical), Zstd level-7 or Deflate level-6, high entropy or patterned compressible. Both fixed chunks and CDC, three independent fresh-process trials/arm, same installed J24C02 `Reader` parent `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, Reader Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. 3 alternatives: original eager executor, simplest serial, bounded64 executor, with full Reader open/read/close time and own Linux VmHWM. Source `_blob` caches only decoded units <=2 MiB, so these owners are not retained; the once/twice comparison isolates reuse without relying on a Python cache. Wrong SHA and hostile referenced physical CRC are rejection conditions.

## All original measured medians (Ubuntu 24.04 / Python 3.12)

**Wall milliseconds of entire session (open + full logical read + executor shutdown); lower is better.** Ratio is eager/serial; >1 means serial is faster. RSS delta is own-process **serial minus eager** VmHWM in MiB, negative means serial is lower.

| Family | Storage | Eager ms | Serial ms | Eager/serial | Bounded64 ms | Serial minus eager VmHWM MiB |
|---|---|---:|---:|---:|---:|---:|
| zstd_entropy_once | fixed | 90.490 | 80.039 | 1.131× | 94.243 | -27.07 |
| zstd_entropy_once | cdc | 91.714 | 80.799 | 1.135× | 92.110 | -27.09 |
| deflate_entropy_once | fixed | 92.119 | 81.685 | 1.128× | 91.752 | -27.12 |
| deflate_entropy_once | cdc | 93.773 | 80.652 | 1.163× | 92.347 | -27.13 |
| zstd_entropy_twice | fixed | 161.594 | 157.117 | 1.028× | 166.971 | -27.17 |
| zstd_entropy_twice | cdc | 160.849 | 154.290 | 1.043× | 162.339 | -27.01 |
| deflate_entropy_twice | fixed | 166.799 | 155.925 | 1.070× | 165.955 | -27.40 |
| deflate_entropy_twice | cdc | 164.329 | 154.308 | 1.065× | 166.451 | -27.25 |
| zstd_pattern_twice | fixed | 140.809 | 143.911 | 0.978× | 142.376 | -9.22 |
| zstd_pattern_twice | cdc | 143.492 | 146.099 | 0.982× | 142.336 | -9.19 |
| deflate_pattern_twice | fixed | 145.475 | 148.590 | 0.979× | 148.241 | -12.35 |
| deflate_pattern_twice | cdc | 146.675 | 145.358 | 1.009× | 147.249 | -12.33 |

Median data supports `BOUNDED_SERIAL_TRANSFER`: `any_full_veto=false`; `strong_parallel=false`; bounded64 dominates neither incumbent and serial simultaneously in any of twelve profiles.

## Strongest negative, causal interpretation and disproof

The result **does not prove universal serial product improvement**. In the patterned/reused Zstd fixed and CDC controls, serial was ~1.8–2.2% *slower* than eager, while comfortably within prospective 10% tolerance; independent host variance might explain a small advantage or loss. Cached low-latency O225 fixtures (<=256 KiB) are not substituted for this new 3 MiB regime. On high-entropy once profiles serial generally wins >10% with roughly 27 MiB lower own peak memory. The stronger `EAGER_PARALLEL_COUNTEREXAMPLE` criterion did not trigger. But high-entropy random compressed inputs largely price *copies/memory traffic* rather than truly expensive decompression; Deflate's `_inflate_lock` serializes its shared libdeflate decoder, so worker-count speedups there have a structural ceiling. No general inference to threads handling other codecs, dictionary execution, real I/O, platform/GIL combinations or binary performance follows.

The experiment was preregistered to falsify a broad policy with any >10% full-session regression or +8 MiB memory; neither happened. If additional nearby scheduling proposals do not address a materially different bottleneck, the family should stop. The next product decision belongs to Reader owner #569, not this independent science.

## Costs and release gate

No product source, format revision, ABI, codec default, Reader cache/validator, benchmark, comparator, release artifact, `docs/discovery/STATE.json`, numeric version, site or license change. No same-input official create/extract release parity or Windows/macOS/ZIP64/hostile mutable-source/recovery proof. Valid CRC/sha and exact bytes are necessary but do not confer product promotion. One Ubuntu host, 3 raw repeated subprocess observations per arm per profile and synthetic payloads are the scientific boundary. Stronger whole-product consistency and portability remain unearned.

## Next owner action

Offer J24C02 #569 the serial control as a low-complexity candidate with exact negative and memory evidence, requiring independent integrated prospective A/B, cross-platform codecs/owners, full extraction and corruption custody, cold-open admission economics and official benchmark before any merge or release. **No merge/release of O226 proposed.**
