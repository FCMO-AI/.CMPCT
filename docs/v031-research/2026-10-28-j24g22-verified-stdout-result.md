# J24G22 — authenticated stdout court: result and decision (2026-10-28 UTC)

**Decision: naive one-pass range-to-stdout is FALSIFIED as a transparent replacement for current `cmpct cat`.** A verified spool can preserve the tested stdout guarantee but exports whole-file temporary I/O and has **NO demonstrated RSS reduction**. Retain shipped behavior. This is a source-locked research result, **not a product change or release milestone**.

## Frozen prediction and exact source
Before any instrument work, [prospective preregistration](2026-10-28-j24g22-verified-stdout-prereg.md) was committed at `58159635cbb9b9ac2880f68453b327ba8cef0926`. Underlying frozen Reader is **published v0.30.0/r24**: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.

Actual [source-exact hosted court #40764023777](https://github.com/FCMO-AI/.CMPCT/actions/runs/40764023777) ran on candidate **`301c4d63d7a830cad3bfbb01ed45565157694a7a`** and passed physical-archive construction, exact source check, 27 subprocess-isolated observations (three cases × three methods × three repeats) and a detached stdlib-only referee **416 checks PASS / one forged receipt rejected**. Original artifact **12848533042**, SHA-256 **`5fa0b28d652a463ca7b34b9c3019934cc764b64f08991379e474e4788cb59cd6`**. Links and SHA bind this result to its measured source; new documentation commits do not magically transfer a product benchmark to a different Reader.

## First-party physical inputs
Real `Builder(root,workers=1,reproducible=True)` generated a 786,432-B incompressible `S_BLOB/CODEC_RAW` direct member and a 2,097,152-B `S_CDC` member. Original complete archive SHA-256 `18cee8e7127e1f38dc0d4aae3a7531889df20449122f9ae8b2590bd2bca9bd25`. A second file differs by **exactly one XOR-1 byte at physical offset 2,360,277**, wholly inside the original direct RAW payload, while index, footer, physical header, CRC field and SHA field remain identical. Mutant complete SHA-256 `7d675ba1fd36f99a161dd36e0f3544eabe6e6b1636d6ad52f367fa87756ae99a`.

An **independent external physical referee** (not importing `cmpct` or the research court) decoded the r24 primary index with system libzstd and MessagePack, proved original signed index digest, original RAW body CRC/SHA, mutated CRC/SHA mismatch, exact location of the single physical byte mutation and raw 27 receipt records. This is a bounded primary-index/frame-level audit, not an independent whole-system r24 implementation.

## Direct observed measurements (one Ubuntu runner; CPU medians, three cold workers per arm)
| Actual case | Inherited eager read | SHA-verified spool | Premature ranged output |
|---|---:|---:|---:|
| 768-KiB intact RAW: CPU | **1.1053 ms** | 1.8918 ms | 0.8221 ms |
| 2-MiB intact CDC: CPU | 8.0920 ms | **5.8090 ms** | 3.1297 ms |
| 768-KiB late-corrupt RAW: CPU | 0.6404 ms | 1.3679 ms | 0.8412 ms |
| Late-corrupt bytes emitted before failure | **0**, exception | **0**, exception | **786,432**, no exception |
| Temporary logical bytes written, RAW/CDC | 0 / 0 | **786,432 / 2,097,152** | 0 / 0 |

Every intact arm produced byte-exact identical logical SHA and length. The unsafe arm is *research-only and never writes actual user stdout*: it writes to a counting/digest sink. It eagerly emitted the entire corrupted RAW member in the negative case. The inherited eager path raised `blob integrity failure` before emitting; the spool path raised `full logical SHA-256 mismatch before emission`, also before emitting. Thus a straightforward `read_range` stdout optimization violates inherited integrity publication.

**Memory negative:** all three modes and all tested cases reported exactly **45,096 KiB** of process peak `ru_maxrss` and zero increment over the per-worker post-open floor. These small first-party cases therefore **do not demonstrate any RSS saving**; do not declare one from the presence of a spill file. The reported CPU advantage for CDC is a narrow sub-10ms experiment on 2 MiB and does not compensate automatically for explicit temporary disk writes, import/startup, cache retention or arbitrary archive families.

## BONK and counterfactual
The cheapest structural discriminator was already visible in shipped Builder: `CHUNK=256KiB`, ordinary non-sparse binary inputs **larger than 4×CHUNK** use CDC rather than a single direct RAW owner. Therefore a RAW-only spool feature, even if technically economical, does not address large *ordinary first-party* files; a simple threshold garden would be poor product leverage. The physically malformed RAW case was still needed to establish the inherited output-integrity boundary, not merely speculate.

Proven lower bound in this contract: a producer that must emit **zero output before an end-dependent whole-file SHA decision** cannot safely release an unknown prefix on a one-pass stream; it must retain/replay data, or change semantics. Our spool is one way to do that, not the only way. A two-pass approach requires credible source/descriptor stability; none is proved here.

## Strongest negative / scope
- Spool does not yet prove complete error-semantic parity on hostile BHDR CRC-only mutations; `read_range` bypasses the ordinary direct `_blob` CRC path, while the spool applies whole-member SHA. A valid SHA/invalid CRC combination could still change acceptance.
- The Reader may cache decoded CDC blobs; anonymous spool adds O(logical size) disk I/O and a second read. Zero measured RSS delta cannot be counted as a memory optimization.
- No Windows/macOS, no complete create/extract/full-product benchmark, no modified CLI, no native ABI, no full arbitrary-source generality and no v0.31 merge evidence.
- A one-runner 2-MiB CDC timing cannot claim general CPU dominance or qualify release.

## Discovery and ownership
Primary question answered: one-pass range stdout publication is unsafe; verified spool remains a bounded-cost research candidate with an unresolved product value proposition. Decision changed: do not implement naive streaming as default; do not promote spool from small positive CPU micro. No collision with existing Reader/Writer/source-custody owners. No evidence-based policy change and no edit to `docs/discovery/STATE.json` (owned separately by #574).

**Next highest-value unclaimed action:** only reopen a verified stdout design if representative large first-party CDC workloads show real incremental memory pressure and an end-to-end disk/CPU integrity tradeoff that beats the simple inherited Reader. Otherwise prioritize the already-owned high-severity extraction quota, hardlink/symlink size, sparse logical-SHA, and coherent v0.31 merge gates. The most important product claim remains unmeasured.
