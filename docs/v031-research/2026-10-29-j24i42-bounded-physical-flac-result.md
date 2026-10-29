# J24I42 — Bounded original-CMPCT FLAC stream: hosted physical result

**Date:** 2026-10-29 UTC. **Classification:** decisive research/architecture mechanism evidence **ONLY**, not product implementation, complete strong-verifier security equivalence or release credit. **Source pre-registration:** `364de43e0148fa26e0d833c25fc049e9ee2f7f8f` (before Rust, physical parser and CI). **Base:** #776 `0047e45e92793ca58a50251847e3cf1adb9c6d90`. Native/Builder/FLAC source blobs remain pinned and unchanged.

## Actual hosted evidence and custody

- Exact result-bearing source HEAD: `3c24e50f851433f80fe69b118d952a17b5ceeaf9`.
- Specialized [GitHub Actions J24I42 run #40960971898](https://github.com/FCMO-AI/.CMPCT/actions/runs/40960971898): Ubuntu 24.04 **SUCCESS**, including real Rust release compilation, independent authenticated Builder physical audit, bounded original-file range verification, 4 hostile negatives, 64 observations and result parser.
- [Physical specimen/evidence artifact #12936011803](https://github.com/FCMO-AI/.CMPCT/actions/runs/40960971898/artifacts/12936011803): 92,983,236 bytes; GitHub's uploaded ZIP SHA256 `e96e8018d07a4011965bbe3b9cea8a652146f88ac5051907a5527a80925a4c4a`. Artifact retention 30 days. To avoid loss when that expires, all 64 raw timing/read/RSS observations, source/run identities and independently recalculated medians are committed in [research/j24i42/hosted_raw_recalculation.json](../../research/j24i42/hosted_raw_recalculation.json). The large physical files remain a time-bounded hosted artifact; reproducible original generator and independent auditor are source-pinned.
- Original complete physical archive SHAs: 8 MiB `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7`; 32 MiB `cf4a826209b3ffff0af86c765db28068386c8f95e6c1405ee29099113b88baa9`. Original encoded direct-FLAC bytes were exactly 3,982,561 and 15,878,863 respectively.
- The result JSON directly emitted by CI and the independently recalculated medians from the job's actual individual output lines agreed exactly. The first CI job's SUCCESS is an executed positive scientific result, not proof of integration into the published product.

## Observed mechanism: one original archive FD, no detached FLAC in the timed path

The self-checksummed r24 archive was built by the unmodified first-party Builder. Existing detached independent audit verified the physical primary/tail index, footer, logical WAV identity and encoded FLAC. The new independent source reader derived encoded byte bounds and cross-checked **the same physical FLAC bytes** against the previously extracted standalone control. The Rust bounded original-file virtual reader refused off-range seeks/reads and decoded the PCM directly from the original `.cmpct` file; it never opened the detached FLAC copy in the measured path.

It fed exact PCM16 and original WAV prefix/suffix in 64 KiB blocks to incremental SHA256 and CRC32. Each authentic source passed with the declared logical size/digest/CRC. The new virtual-boundary tests returned EOF precisely at the encoded payload boundary, not inside the following original CMPCT tail index. This verifies one narrower implementation seam; the full Reader's parser and archive-level integrity contract have not been transplanted.

## Same-runner raw measured economics

Ubuntu 24.04, Rust release; same files, same inherited native source, ABBA/BAAB, 16 observations per mode and size (64 total). Times exclude process construction and common preliminary archive opening. `rchar` is process characters read, not disk blocks; median `VmHWM` is Linux process peak memory. The new candidate carries strictly weaker parser/authentication duties and therefore comparisons are **architectural oracle cost ratios, not product throughput claims**.

| Builder WAV logical PCM | Existing native complete verification | Bounded original-file PCM digest | Native / bounded |
| --- | ---: | ---: | ---: |
| 8 MiB + 44 B, median wall | 84.845719 ms | 35.5310365 ms | **2.387933x** |
| 32 MiB + 44 B, median wall | 804.110902 ms | 146.6052515 ms | **5.484871x** |
| 8 MiB, median rchar | 7,965,521 B | 3,982,715.5 B | **2.000023x** |
| 32 MiB, median rchar | 79,395,069 B | 15,879,019 B | **4.999998x** |
| 8 MiB, median VmHWM | 23,096 KiB | 2,978 KiB | **20,118 KiB difference** |
| 32 MiB, median VmHWM | 59,284 KiB | 2,966 KiB | **56,318 KiB difference** |

For 32 MiB the bounded physical payload reader actually returned **15,878,863 B**, exactly one complete FLAC encoded stream on the median measured iteration. This excludes metadata/header audit work, whose cost is handled separately and must be charged when making a full product candidate. The 93 MB artifact is a real evidence carrying cost, not a product input/output byte saving.

## Adversarial controls

Four actual Rust hostile trials passed (two Builder sizes times two changes):

1. Original archive byte range truncated by 64 encoded bytes **while the rest of the original file and tail index remained on disk**: both cases rejected by Claxon as an unexpected encoded EOF. The virtual range cannot opportunistically read those physically present missing bytes.
2. A disposable original physical archive copy with the first `fLaC` magic byte XORed once, with every other archive byte unchanged: both cases rejected as invalid FLAC stream header. No claim that the resulting self-checksummed archive was newly origin-authenticated.

No false accepts were observed in these four cases. Other malformed streams, metadata mutation, concurrent source replacement and adversarial long seek patterns remain unmeasured.

## Decision and counterfactual

**H1 accepted in its narrow research scope:** a file-backed Claxon decoder can consume source-exact FLAC directly within a bounded original r24 archive region, reconstruct exact WAV content, reject these malformed spans and eliminate the previous experimental FLAC-copy prerequisite. **Do not promote product economics or safety parity from this observation.**

The earlier J24I39 detached-file oracle was a useful cheap feasibility rung but could not establish physical-source viability. Adding a small bounded view and independent span audit was the prospectively recognizable next discriminator; no general Discovery policy change is justified by one positive example. Also avoid re-testing the private FLAC STREAMINFO MD5 semantic difference already decided in #779.

## Risk and integration obligations

- No complete original-file authentication in the same Rust routine: index, CMA4 framing/metadata, physical CRC, SHA, and hardened parser semantics must be composed at one source-FD ownership boundary with no race.
- No proof of complete consumption/validity of *all* future FLAC encodings, long metadata, path/reference tampering, dictionary/sparse/chunk/pack interop or multi-host native ABI.
- No universal memory ceiling merely because output staging is 64 KiB; bound decoder frame state, metadata and memory explicitly.
- No complete create/extract, cold-open, archive bytes, materialization, dependency, cache, cross-platform or external ZIP/Zstd parity measurement.
- The 32 MiB wall ratio partly includes the baseline's five repeated decompressions, whereas the oracle only hashes logical bytes. A strict product replacement will have additional parse/authentication work. The baseline is allowed to win if that extra work dominates.
- The current parent #765 owns native source. Integrate only through the owner and rerun actual unchanged general/native/hostile/frozen/release gates before promotion.

## Next highest-value executable action

Propose to #765 a private one-FD, span-limited FLAC streaming verifier using this source-proven mechanism, but first bind index/header/FLAC metadata/physical CRC to source ownership and prove full malformed-input rejection with bounded RSS on Ubuntu/macOS/Windows and exact both-candidate/source controls. Keep latest-head CI administrative statuses separate from actual result-bearing source HEAD and preserve incompatible reds. No `docs/discovery/STATE.json` mutation unless a durable decision-changing frontier update is warranted by current canonical truth.
