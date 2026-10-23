# v0.31 — POSIX advisory writer lease isolated cost O0

**Date:** 2026-10-23. **Scope:** single Linux runtime, CPython 3.13.5; ordinary temporary-file `open`/ `close` versus `open`/`flock(EX)`/`fstat`/`flock(UN)`/`close` on the same existing 4096-byte inode. **NOT a CMPCT product benchmark.** Research supplement to draft PR #295 and transaction Issue #290. Original Python measurement script SHA-256 `14bc05f07d80ba4184b7433ea43d928641df6d1119919695077d2a0353bd379c`; original JSON SHA-256 `23a58633da4d99ad37411520897ccb2268bc4774f1dd8916dc89a1ac5415881b`.

## Method

Seven alternating control/lease runs, each with 16,000 operations/arm, monotonic `time.perf_counter_ns()` surrounding each inner loop; no package import, archive parser, compression, write or fsync. Report each operation's elapsed nanoseconds, not process startup. Sample order alternates each repeat. Python loop overhead is shared but cannot isolate OS kernel cycles. The source below reproduces the isolated uncongested part:

```python
import fcntl, os, statistics, tempfile, time
with tempfile.NamedTemporaryFile() as p:
    p.write(b"x"*4096); p.flush()
    samples=[]
    for i in range(7):
        pair={}
        for arm in (("control","lease") if i%2==0 else ("lease","control")):
            t=time.perf_counter_ns()
            for _ in range(16000):
                fd=os.open(p.name,os.O_RDONLY|getattr(os,"O_CLOEXEC",0))
                if arm=="lease":
                    fcntl.flock(fd,fcntl.LOCK_EX)
                    os.fstat(fd)
                    fcntl.flock(fd,fcntl.LOCK_UN)
                os.close(fd)
            pair[arm]=(time.perf_counter_ns()-t)/16000
        samples.append(pair)
    print(samples,statistics.median(x["lease"]-x["control"] for x in samples))
```

## Raw observations (nanoseconds per operation)

| Round | Open + close | Open + flock + fstat + unlock + close | Delta |
|---:|---:|---:|---:|
| 1 | 1750.682 | 3057.038 | +1306.356 |
| 2 | 1979.528 | 3095.775 | +1116.247 |
| 3 | 1908.595 | 3153.206 | +1244.610 |
| 4 | 1845.479 | 3065.280 | +1219.802 |
| 5 | 1853.655 | 3674.453 | +1820.799 |
| 6 | 2431.654 | 3361.120 | +929.466 |
| 7 | 1956.312 | 3339.782 | +1383.470 |

Medians: control **1908.595 ns**, charged sequence **3153.206 ns**, paired delta **1244.610 ns (1.245 microseconds)** for this Linux process. This is not the cost of `CMPCT.append_update`: actual Reader, metadata processing, encoder, append/fsync and post-lease checks are outside the measurement.

## Forced contention oracle

One independent OS process acquired an exclusive advisory lock and held it; another process attempted the same inode lock with a controlled nominal 100ms hold from `multiprocessing.Event` synchronization. Waiter observed **100.541758ms** acquisition latency; both processes exited **[0, 0]**. This only establishes that lease wait reflects prior owner's hold, not any real CMPCT operation duration or throughput SLA.

## Decision / costs / limits

The uncontended POSIX primitive is cheap enough to justify further engineering, but contention must include the entire snapshot/encoding/fsync interval. **Do not claim product speed parity** from this oracle or generalize the nanoseconds to NFS/macOS/Windows or other hardware. The candidate's Windows `NotImplementedError`, advisory-only guarantee, namespace-race debt, crash/durability evidence and full same-runner product ABBA remain promotion blockers. The real scientific decision is unchanged: retain the cooperating-inode-lease candidate for exact product tests and separately pursue portable stronger ownership.

Counterfactual: the smallest informative discrimination is to compare a two-process same-footer negative (PR #289) to a full-transaction inode-lease positive (PR #295), then attack its namespace boundary; a microbenchmark cannot substitute for either correctness court. Discovery policy unchanged.
