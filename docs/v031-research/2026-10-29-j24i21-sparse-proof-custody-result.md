# J24I21 — original-hosted result: owner-proof cache fails mutable-wire custody

**Decision:** `NAIVE_CACHE_MUTABLE_CUSTODY_FALSIFIED`. Evidence class: **scientific/oracle only**, no product implementation and no release credit. Collected 2026-10-29 UTC.

## Source and preregistration custody

- Parent #620 at `7ca3951d48b4ebabf07f740b551b009ce78a3e34` (verified Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`); shipped main `80c358f8824ec1b20d349c92ed94c898090969b0` unchanged.
- Preregistration `ad6ebbbe5462c7be93d434fed494b8cb15cee2c9` precedes test `94af95ce417893b03e749627aebf04d61a638405`.
- First result-bearing head `6c93c48e4258daa7a36524cc522c25b927348adc`, [GitHub Actions #40840909766](https://github.com/FCMO-AI/.CMPCT/actions/runs/40840909766): specialized Ubuntu job **SUCCESS**; inherited signed sparse-hardlink verification **12 passed**.
- [Original unmodified Actions artifact #12882742357](https://github.com/FCMO-AI/.CMPCT/actions/runs/40840909766/artifacts/12882742357) has ZIP SHA-256 `5e0cd040a23bb947b72b8d66f06aac40d457097d9877efc0e382bb189fef76c3`. Exact archive/test/source receipt is inside; archive ZIP CRC passed independent inspection. Not a rebuilt/cleaned artifact.

## Measured genuine sparse hardlink economy (same-source fresh processes, A/B/B/A)

| Logical owner | Genuine aliases | Physical CMPCT | Original verify wall (ms) | Naive cache oracle wall (ms) | Actual streamed SHA calls A/B |
|---:|---:|---:|---|---|---|
| 2 MiB | 1 | 1,154 B | 3.611 / 3.566 | 1.927 / 1.895 | 2 / 1 |
| 64 MiB | 32 | 1,312 B | 1093.561 / 1098.296 | 34.079 / 34.489 | 33 / 1 |

Real Builder produced **S_SPARSE regular owner** plus physically shared `os.link()` aliases; the originating host allocated 8,192 bytes to the physical sparse regular file before archive creation. All four trials per case imported exactly the same Reader source, independently checked the same input SHA-256 before and after and returned valid verification counts without mutation. The 64MiB source SHA-256 was `b1cccabc71ae27c32c4aa5b40289686cc1e4b782d0a4b7a11789c1105b4ba512`; 2MiB source SHA-256 was `a6c0663ab58aabe7406405fcd8641c6dd8d55f343a343cd0ad8f5b16457b8f35`. The approximate 32x CPU/wall opportunity is **an unsafe detached oracle**, not a proposed product speedup. CPU and RSS per-process raw records live in the original artifact; no full gate / platform performance claims.

## Decisive hostile physical observation

After the first successful owner SHA verification, two independent physical copies of the **same** original 64MiB source each underwent a controlled one-byte payload mutation:

- Before SHA-256 (both): `b1cccabc71ae27c32c4aa5b40289686cc1e4b782d0a4b7a11789c1105b4ba512`.
- After SHA-256 (both): `3cd5933c52f115e269bde371917954075fc753a8047a0c710d5f89ee65f21eab`.
- Independent bytewise audit: **exactly one byte differs**, at absolute archive offset **638**, inside physical Zstd blob payload span **[638,656)**. Authenticated primary index region and footer are byte-identical. No arbitrary index/footer mutation.
- **Unmodified #620 Reader REJECTED** at its next sparse hardlink verification with `RuntimeError: Zstd decompress: malformed codec input`.
- **Naive proof-cache oracle ACCEPTED** all aliases without reaccessing the now-mutated physical record, returning a successful verification count.

Therefore reuse of the original owner's previous SHA proof is **not semantically equivalent** to repeated verification when the source can mutate during a verify pass. This is a bounded observation-frequency failure (the actor already has file-write access), **not remote exploitability**, a universal TOCTOU proof, or a problem newly introduced in shipping CMPCT. #620 consciously avoids this unsafe optimization.

## Independent physical audit and counterfactual

An auditor with only Python `zipfile`, `struct`, `msgpack` and OS `libzstd` (no CMPCT import) examined the original downloaded ZIP: authentic r24 header, decompressed SHA-authenticated primary indexes, one sparse owner and exactly 1/32 hardlink rows, bytewise identical A/B sources, unique one-byte tamper at compressed payload start, unchanged authenticated index/footer, and matching tamper/source digests. All matched the hosted receipts. This audit is physical/custody corroboration; kernel RSS and CPU were measured only by the hosted execution and were **not** independently repeated.

The cheap prospective discriminator was visible in #620's existing code comment: each alias calls `_verify_sparse_streamed` and does **not** cache success. Before engineering memoization, test **a single physical mutation between verification calls**. That disproof would have averted a larger unsafe product patch. The transferable lesson is local to source-ownership-sensitive proofs, not evidence to edit Discovery Engine policy.

## Decision / next nonduplicative frontier

**Retire** naive verified-content SHA memoization for mutable sources, irrespective of apparent 64MiB performance upside. Keep terminal graph-resolution memoization. A credible rehabilitation would need a physically immutable snapshot or descriptor/ownership guarantee whose trust and cost are proven, with complete file/temp-I/O, CPU, RSS, metadata integrity, snapshots/races, recovery, portability and selective-work accounting. #620 and #738 retain product ownership; #741 retains stage-custody work; do not patch their sources here. #574 owns staleable shared Discovery state. No collision, no merged code, no release.

The falsifier itself is not a promotion court; complete official product gates, Windows/macOS, other codecs and unrelated Reader failures remain unmeasured.
