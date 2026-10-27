# J24S03 — native C-zlib CRC operator court result

Date: 2026-10-27 UTC. **Research-only, zero CMPCT product/source/format changes.** This result is not a release, Reader, ZIP64, cross-platform, or filesystem-safety claim. [PR #554](https://github.com/FCMO-AI/.CMPCT/pull/554) is stacked on the immutable J24S02 #547 negative source.

## Prospective question, scope, and frozen gate

Frozen BEFORE candidate implementation: [J24S03 preregistration](2026-10-27-j24s03-native-crc-prereg.md), commit `cee257eefd241d7e9a09918b1b4845bd707e3fea`. J24S02 #547 had falsified uncached Python GF2 zero CRC on mixed sparse (~0.54x same-run conventional zlib). Native zlib `crc32_combine_gen`/`crc32_combine_op` is a distinct mechanism. To continue **oracle-only**, require at least 5% complete encoder wall improvement on each 256-MiB all-zero and mixed sparse family (at least one DEFLATE level in each), no >2% regression on both levels of 256-MiB structurally irregular and 64-MiB ordinary nonhole controls, and exact SHA256/CRC32/DEFLATE identity with independent reconstruction.

## Source-exact hosted evidence

- [GitHub Actions PR exact-head run 40428736797](https://github.com/FCMO-AI/.CMPCT/actions/runs/40428736797) — **SUCCESS**.
- Real evaluated Git HEAD: `4610c1bfe257497a7e58c95cd681a6725fbd88ae` (the **result-bearing** HEAD, before this report commit).
- Evaluated instrument: `research/j24s03_native_crc_operator_oracle.py`, Git blob `c52c9db16f3b3594db0e21c6dd1fbb65a327fd8c`.
- Frozen prereg blob `28e9ea6f596e82eaeb64c634dac42d2e000b0897`.
- [Raw interleaved observations, three source fingerprints, artifact 12701525394](https://github.com/FCMO-AI/.CMPCT/actions/runs/40428736797/artifacts/12701525394); uploaded artifact ZIP SHA256 `94c63f82644a23805337311c8a09cb0fed7fbd5abe1daafb78912deffe32b1f6`.
- Ubuntu 24.04, CPython 3.12.15, host's zlib, three interleaved cold candidate/baseline repeats for levels 1 and 6; native C ABI is accessed with `ctypes`, with actual per-encode operator construction charged. 168 native/zlib adversarial checks passed (unaligned lengths, large runs, distinct nonzero initial CRC, independent nonzero suffix).
- All four arms per input case preserved **exact full logical SHA-256, complete CRC32, raw-DEFLATE wire hash/length and independent bounded raw inflate**. No entropy/content identity conditional admission was involved: test inputs were structural descriptors.

## Full-work offline raw-DEFLATE encoder wall medians (seconds)

| Family, logical input | Level | Native incremental zlib | Native cached operator | Cached speedup | Native uncached speedup |
|---|---:|---:|---:|---:|---:|
| all known zeros, 256 MiB | 1 | 0.168746 | 0.132186 | **1.277×** | 1.281× |
| all known zeros, 256 MiB | 6 | 0.170453 | 0.135443 | **1.258×** | 1.272× |
| mixed known holes + 4-KiB data, 256 MiB | 1 | 0.173170 | 0.136670 | **1.267×** | 1.277× |
| mixed known holes + 4-KiB data, 256 MiB | 6 | 0.173446 | 0.138866 | **1.249×** | 1.266× |
| irregular 256 distinct known zero-run lengths, 256 MiB | 1 | 0.474582 | 0.436652 | **1.087×** | 1.092× |
| irregular 256 distinct known zero-run lengths, 256 MiB | 6 | 0.753881 | 0.728803 | **1.034×** | 1.006× |
| ordinary no-hole, 64 MiB | 1 | 1.209150 | 1.173213 | **1.031×** | 1.021× |
| ordinary no-hole, 64 MiB | 6 | 1.250515 | 1.239290 | **1.009×** | 0.995× |

**Prospective terminal:** `CONTINUE_ORACLE_ONLY`. All-zero and mixed each exceed 5%, irregular does not regress by 2%, and nohole has byte-identical direct fallback. No deterministic size improvement can be credited: every arm emitted the **same DEFLATE bytes** within each family. Historical J24S02 execution timings came from another run and must **not** be treated as same-run speed comparisons.

## Most important negative / self-critique

**Caching is not established as the cause of the win.** On all-zero and both mixed levels, the C-native *uncached* arm is marginally faster than cached. On level-1 irregular, uncached is also faster; only level-6 irregular visibly favors caching, and noise cannot be ruled out from three trials. The main shift is moving polynomial computation into the mature native zlib implementation rather than rebuilding Python GF2 matrices. Therefore, do not mandate an operator cache on the evidence of this experiment. The experimental cache was limited to 256 lengths, with bounded fallback; actual cache overflow (257+ unique lengths) is **not yet a hosted adversarial case**. Reuse is potentially unnecessary maintenance tax.

The nohole case is algorithmically the same across variants: apparent 1.0–3.1% speed difference is *noise-compatible*, not earned product acceleration. No same-process memory comparison can prove RSS; no peak RSS/temporary I/O, isolated cold process startup, physical ZIP64 archive, whole-system SHA trust under source mutation, staged publication, update/index cost, or other platform was measured. SHA256 was fully charged; the lower bound of SHA work remains. Only checksum calculation changed.

## Counterfactual discriminator and convergence path

J24S02 profiling showed the Python matrix work to be expensive. One small native zlib `combine_gen/op` oracle with adversarial unaligned holes would have isolated the implementation owner before the large J24S02 court. This is a **prospective reusable diagnostic lesson**, not authority to mutate discovery policy from one record.

If a product owner subsequently tests native CRC composition on the genuine O193/J24S01 ZIP64 Reader path, compare **native uncached** first (stronger, simpler control), then bounded cache only if justified. Require same file/input/hash semantics, first-use dynamic library availability/platform fallback, complete archive bytes, CPU/wall, RSS, temporary I/O, and independence from checksum/source/publish races. A native helper with decoder-wide permanent dependency or unbounded caching may outweigh any savings. Do not promote on the offline oracle alone.

## Decision, ownership, and release

- **Research question:** native C operator path can reduce complete offline sparse encoding CPU/wall under exact SHA/CRC/DEFLATE semantics — confirmed on Ubuntu in the tested families.
- **Distinct cache hypothesis:** caching itself beats simple uncached native composition — **not demonstrated; simpler uncached control wins most cases**.
- **Decision-changing:** YES, reopens the C-native family while keeping Python GF2 negative retired; does not justify integration.
- **Discovery policy:** unchanged; `docs/discovery/STATE.json` unchanged because central project state is current-owner/stale-cache managed.
- **Collision:** no PR for a pre-existing native zlib CRC operator candidate was found at initial claim check; parent #547 was deliberately read and left untouched.
- **Product authority:** r24 unchanged, v0.30.0 remains released, no merge/release/performance credit.

Next highest-value inexpensive unclaimed discriminator is a bounded 257+-distinct-length cache-eviction hostile (if considering caching at all), followed by **real Reader ZIP64 full-work economics versus native-uncached control**. A repeated zero-run cache study without product opportunity is lower priority than outstanding extraction-publication authenticity and ZIP64 productization.

## Newly identified product-path boundary: O193 uses the standard ZIP writer

A subsequent **read-only source inspection** of current O193 [PR #521 Reader](https://github.com/FCMO-AI/.CMPCT/blob/agent/phased3-v031-o193-zip64-streamed-fallback-20261026/src/cmpct/reader.py#L525-L588), Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`, revealed a crucial ownership mismatch. Its ZIP64 fallback streams bounded `read_range` output to Python `zipfile.ZipFile.open(zi,'w')`. The standard-library `zipfile._ZipWriteFile.write` computes its own `crc32(data, running_crc)` and then calls its own compressor. CMPCT cannot speed that **unchanged** writer simply by precomputing a separate native CRC: doing so would duplicate work rather than remove it. The J24S03 win requires an output writer/representation with legitimate custody over CRC generation and framing (e.g. a separately validated exact-stream ZIP path), not a drop-in `crc32` call in O193's current stdlib writer.

**This narrows product priority:** do not implement a CRC operator cache in the current ZIP64 fallback. First test whether J24S01's known-zero raw-DEFLATE fragments can be admitted into a complete ZIP64 member writer under bounded integrity, recovery, encoded-byte and portability law, or whether the product's existing stdlib compression path is already the stronger simpler owner. No standard-library evaluator should be monkey-patched or weakened to manufacture the oracle win. This static source analysis is a product-design constraint, **not** an executed product benchmark. O193's own authoring and concurrent PR ownership remain intact.
