# J24C17 installed sealed-reference result — research only

Date: 2026-10-28 UTC. **Exact measured product HEAD** `b5ec70ea6d30f401679b81db313bf88c90096fde`, a child of #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`. Prospective preregistration `95af85b3851ce1235c5036e885e699eb4cb60fc8` preceded source patch `922cc5276fb7415755ad63c04893af005b97f2d4`. Draft [PR #676](https://github.com/FCMO-AI/.CMPCT/pull/676); no merge, release, on-disk format or release-test alteration.

## Decision

**Narrow J24C16 wrong-byte regression contained on genuine installed native Readers on Ubuntu 24.04, macOS 14 and Windows 2022.** The former mutable native-indexed S_CHUNKS list is replaced by a tuple during construction, with a private original row/storage/size/reference/proof identity binding. For the exact 512-ref signed J24C16 geometry, `read_range(257,1)` returns the authenticated `b'A'`; in-place mutation of the tuple raises TypeError, and publicly rebinding storage/size/path results in IOError rather than the previously demonstrated silent `b'B'`. An external replacement of `_chunk_range_marks` does not affect reads. Preexisting strict fallback is unchanged in the selected source-bound tests.

This is **engineering research evidence, NOT a product/security guarantee**. It does not close untrusted on-disk archive hardening, arbitrary mutation of publicly exposed blob tables, concurrent races, arbitrary Python monkeypatches, whole-source FD races or full recovery/extraction.

## Source-exact hosted evidence

[GitHub Actions J24C17 #40690376678](https://github.com/FCMO-AI/.CMPCT/actions/runs/40690376678) ended **SUCCESS 4/4** jobs on exact HEAD `b5ec70ea`. Each ABI3 platform built a genuine noneditable CPython3.11 package wheel, confirmed installed `site-packages/cmpct/reader.py` and both native scanner exports, ran the new signed mutation/fallback tests plus unchanged inherited J24C13/J24C08/O215/RAW Deflate controls and then executed the original J24C13 fresh-process same-installed-wheel ABBA + independent referee:

| Host | Targeted tests | Original J24C13 ABBA | Native-only/fused Q6 speedup at 65k and 262k, fixed/heterogeneous |
| --- | --- | --- | --- |
| Ubuntu 24.04 / CPython 3.11 | 52 passed, 1 skipped, 11 subtests | 120 real processes, original referee PASS | 4.65–6.23x |
| macOS 14 / CPython 3.11 | 52 passed, 1 skipped, 11 subtests | 120 real processes, original referee PASS | 6.12–9.02x |
| Windows 2022 / CPython 3.11 | 52 passed, 1 skipped, 11 subtests | 120 real processes, original referee PASS | 6.73–8.28x |
| Ubuntu 24.04 / CPython 3.10 | 33 passed, 11 subtests, confirmed ABI3 unavailable | No A/B performed | Strict Python fallback PASS |

Total targeted passed = 189 (plus 33 subtests across four hosts? Actual per-host subtests: 11 each, total 44). Native A/B = 360 independent subprocess measurements from original J24C13 harness, with untouched original negative/positive scientific judge. Referee reported `J24C13_SOURCE_EXACT_RECEIPT_AUDIT_PASS_RESEARCH_ONLY` on all native hosts. It reported no preregistered **material** Q1 loss versus native-original by its joint relative+absolute criterion, but Q1 early generally **got slower**; macOS fixed-65k Q1 early fused ~2.605ms versus native ~1.342ms (nearly 1.94x time). Avoid describing this as Q1 improvement.

Original GitHub artifact IDs / provider SHA-256 digests:

- Ubuntu `12816976950`, `sha256:73f3c996c2b9d32f4436cb767a7aba3f68df0c40e89737f68c8ba02a3dfb8de7`.
- macOS `12816916496`, `sha256:c964a8d7bdb3d0a05af48cf9f68ee2b4f9ee373d865ae57f5461a4bb60d7f8e6`.
- Windows `12817770170`, `sha256:4796ccfc71a817166cdc485f5d876a5bf27546ca2780e3a20cd1726c2f29f134`.
- Python 3.10 `12816622659`, `sha256:fedc18147ce5aedb0ba1999ba36388be2c9f31ba67127da555e771e89d394b52`.

Log stdout independently reports the per-case medians and the original referee verdict; this record is a cross-host **log/receipt reconciliation**, not an independent third-root physical ZIP audit. Artifact download and independent physical digest verification remain future work when required.

## Memory, CPU and persistent ownership

The selfsame original J24C13 runner compares `native-original` (no checkpoints) with `fused` (now sealed). macOS process peak RSS increment over native-only was ~0.016–2.531 MiB across 20 cases, under the 8 MiB original cutoff; Ubuntu's child-process process-HWM metric yielded 0 MiB delta on those cases, **not a proof of zero transient allocation or memory ownership cost**. Windows reported `null` for RSS; this is genuinely unmeasured.

A lower-tier CPython 3.13 Linux source-free `tuple(refs)` micro-oracle with five repeats (not installed CMPCT evidence) found: 262,144 refs copied in ~2.56 ms and transient +2.0 MiB traced peak with no retained external alias; external retained list alias causes a permanent second ~2.0 MiB tuple allocation; at 1,048,576 refs transient +8.0 MiB. Local timings were noisy and cannot be extrapolated to hosted CPython3.11. Thus the candidate saves **ordinary ongoing duplicate ownership only when no outside alias exists**; open/Q1 transient CPU and peak-RSS debt remain.

## Strongest negative / scope boundary

This is not a same-source direct isolated comparison to original unsealed #662: original J24C13 ABBA compares native-only versus the new sealed candidate, not the old fused #662. It is not a published Reader v0.30.0 A/B. Hence even though retained high-Q speedups are promising, we **cannot claim** the immutable-ref fix has zero added Q1 cost, fully preserved old Q64 performance, or earned any release gate. J24C15 #669's published-floor early Q1 loss, including +5.186ms on a slower runner, remains hard open debt. The parent #662 generic CI previously had ten failed inherited cases (six optional-native environment mode assumptions and four historical attribution/fingerprint assertions), which are not waived by targeted green tests.

Importantly the public Reader's `self.blobs` and other decoded metadata remain mutable. The candidate protects **only the ref tuple and its associated signed proof and row binding**, not all derived state. A malicious in-process caller may also mutate private attributes or invoke arbitrary methods. This is a narrow fail-closed contract for normal indexed reference-list rebinding, not an immutable Reader API.

## Next executable highest-value action

Obtain an **exact same-host, same-input original #662 vs sealed #676** installed-Reader cold-open and Q1/Q6/Q64/RSS cost court; bring the genuinely released v0.30.0 control too, with existing #669 heterogeneous/RAW-Zstd and large owner regimes. Then either (a) productize with an explicit immutable-index API contract and independent native Rust reader/portability/recovery gates, or (b) revert/narrow if verified Q1 compatibility/cost losses overwhelm Q6/Q64. Unresolved blob-table ownership deserves a separate bounded, explicitly preregistered mechanism/falsifier rather than general security claims.

No discovery policy or `STATE.json` mutation; #574 owns stale-state reconciliation. Existing #672 replication remains the negative parent evidence and must not be overwritten.
