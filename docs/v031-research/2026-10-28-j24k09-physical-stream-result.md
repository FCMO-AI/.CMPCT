# J24K09 — Physical-size proof for signed VZIP suffix coordinates

Date: 2026-10-28 UTC  
Status: **SIX SIGNED ATTACK CELLS REJECTED ON THREE HOSTS; PRODUCT PROMOTION BLOCKED BY SESSION ECONOMICS AND BROADER CI.**  
Branch/PR: [J24K09 #653](https://github.com/FCMO-AI/.CMPCT/pull/653).  
Parent: [J24K06 #642](https://github.com/FCMO-AI/.CMPCT/pull/642) @ `78bc1f552fee24970228f89ac25dbf23307b0406`.  
Frozen initial prereg: `36c5950931cef292c7cc37602e62dcf7be2f44b0`.  
**Evidence HEAD:** `459967c1f780bee1a422a4cf65007493d02ea2b3` (before subsequent J24K09b session-cost instrumentation; do not assert it passed that future instrument).  
[Three-host installed-wheel workflow #40642136892](https://github.com/FCMO-AI/.CMPCT/actions/runs/40642136892): three jobs SUCCESS.

## Product-scoped corrective mechanism
The physical stream-size witness is provided by the same already-open Reader and mmap. It reads a bounded real BHDR and compares physical header codec, decoded/compressed sizes, metadata length and record extent against the effective signed blob descriptor. ZIP STORED and mode1 consume the decoded size; canonical Deflate mode0 consumes the physical compressed size. An actual-size mismatch against the signed recipe fails before the Reader advances suffix coordinates. No skipped nonmode2 stream decompression, no new on-disk bytes. Mode2 retains its genuine recompression proof.

This **does not** establish SHA authentication of arbitrary partial content; equal-sum skeleton boundary relocation remains a separate surviving negative (#646). Source mutability after open and native parity remain separate concerns.

## Exact scientific evidence (not release credit)
The frozen signed-archive court transferred the six #645 previously wrong-byte VZIP csize +/-1 perturbations, preserving the exact physical blocks and recomputed signed primary and tail indexes. The original signed input, full-read and verify positive/negative controls remained in place. On each of Ubuntu 24.04, macOS 14 and Windows 2022:
- STORED -1/+1, retained mode1 -1/+1, canonical Deflate mode0 -1/+1 all **rejected** their otherwise wrongly positioned suffix queries.
- For three -1 cases, 75 probes each were rejected; for three +1 cases, 76 probes each were rejected: **453/453 one-byte probes rejected per host, zero wrong bytes silently returned**.
- **43/43 focused pytest PASS per host** (129/129 across three host runs), plus source-custody, installed-wheel and raw-receipt audits green.
- The independent exact-source guard inverted only the allowed two Reader/codec mutations back to the original parent bytes; validator and three frozen vector Git blobs were SHA-locked.
- Component control exposed malformed actual BHDRs, signed descriptor disagreement, invalid index/type, invalid flags/reserved, shortened record and wrong compressed-codec. Inherited J24K06 mode2/lazy-read tests remained unchanged and green.

These are **18 host reproductions of six distinct signed mutants**, not 18 independent archive designs. The binary decision is correctness of physically inconsistent preceding stream coordinates, not cryptographic integrity of partial ranges.

## Counterevidence: physical header verification has significant suffix cost
The same three hosts ran a source-equal component micro experiment with 64, 512 and 4096 preceding STORED streams, 12 raw wall/CPU samples per control per size. It is a *single-operation component result*, not a complete Reader performance benchmark. The optimistic control returns **previously available size bytes without revalidating BHDR**, and the unsafe control omits all prior stream proof; neither has the full candidate's security semantics. Their measurements establish the price of proof, not a valid product win.

| Host | Prior streams | Actual physical BHDR proof | Optimistic cached-size control | No-proof unsafe floor |
|---|---:|---:|---:|---:|
| Ubuntu | 64 | 0.09337 ms | 0.01578 ms | 0.01120 ms |
| Ubuntu | 512 | 0.73115 ms | 0.12567 ms | 0.08312 ms |
| Ubuntu | 4,096 | **5.82161 ms** | 1.05241 ms | 0.68343 ms |
| macOS | 64 | 0.06638 ms | 0.01157 ms | 0.00839 ms |
| macOS | 512 | 0.58047 ms | 0.09807 ms | 0.06989 ms |
| macOS | 4,096 | **4.49601 ms** | 0.82172 ms | 0.52641 ms |
| Windows | 64 | 0.05691 ms | 0.01010 ms | 0.00689 ms |
| Windows | 512 | 0.47174 ms | 0.07922 ms | 0.05307 ms |
| Windows | 4,096 | **3.62053 ms** | 0.64426 ms | 0.41955 ms |

The BHDR proof is ~5.5–6.0x the optimistic predecoded control and ~7.9–8.9x the explicitly unsafe control across measured sizes/hosts. These numbers do **not** imply a regression against an equally secure baseline; the baseline did not offer this guarantee. Nor can we conclude memory cost or whole-product economics from them.

## Negative inherited-helper finding
The initial implementation added a stand-alone helper decode fallback that would have broken J24K06's legitimate no-regeneration lazy selective contract. It was not retained. Append-only [J24K09a addendum](2026-10-28-j24k09a-inherited-helper-laziness-addendum.md) records the discrepancy. The public installed Reader always supplies the physical-size witness, while the bare internal no-callback helper remains lazy and has no newly claimed coordinate guarantee.

## Next decision and current debt
After observing the cost, J24K09b was preregistered to fully charge once-per-session prevalidated header sizes against per-read physical checking at 1/8/64 queries, same source and synthetic inputs, with additional memory bytes charged. At this report's initial result cut **J24K09b has no measured result**; it is an oracle, not product evidence. A cached proof cannot be promoted unless source immutability/invalidation under same-inode mutation is independently established. Existing mode2 large-prefix recompression debt, equal-total skeleton semantic ambiguity and official no-regression gates remain open.

The current stage supports continued **guarded candidate research**, not merge/release. Preserve all inherited failing historical observational tests and source-owner locks; do not change release gates to improve a scoreboard. The next executable scientific action is to audit J24K09b raw 9-cell three-host session receipts, then select bounded per-read metadata proof versus a structurally different immutable-snapshot ownership model based on complete costs and safety, not micro wins.
