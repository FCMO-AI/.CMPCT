# ONE-G0.2 — quaternary descriptor-authentication compute A/B — 2026-09-05

## Mission lock

The exact quaternary structural A/B advanced arity 4 because the 80-byte basis-leaf point remained strictly smaller than independent literals on every frozen family row and preserved the unchanged `<=1.20x` median authenticated 4 KiB touch law. That result did not establish execution efficiency.

This frozen A/B asked whether the shallower quaternary descriptor tree also reduces enough authentication work to avoid exporting its persisted-byte gain into build/verification CPU.

Binary and quaternary candidates use the exact already-frozen descriptor semantics and implementations. Inputs come from the same ONE-G0.2 version-family generator and are held identical. The experiment records deterministic SHA-256 invocation/input-byte accounting plus repeated same-process CPython/hashlib wall time with warmup, alternating order, batched inner loops and medians.

Frozen V=8 advancement gate required all of:

1. exact verification for both candidates on every generated case;
2. fewer deterministic quaternary hash invocations for both build and selective verification;
3. median V=8 quaternary build and verification ratios each `<=1.05x` binary;
4. at least one of those V=8 ratios `<=0.90x` binary.

No timing threshold was changed after execution.

## Exact execution identity

- experimental version: `ONE-G0.2`
- result-bearing source: `1050b3c89b12aea3108711c3baf5f3cc026230ed`
- workflow run: `33954484417`
- result-bearing job: `101275180697`
- artifact: `9965902567`
- artifact ZIP SHA-256: `fd04410ea59412e915e63c3133019ffc498dc28bbda10eb1223f02a44ccb4620`
- ONE semantic boundary: **76/76 passed**
- exact failures: **0**
- workflow/job conclusion: **success**
- experiment decision: **`quaternary_compute_not_proven`**

## Result

| versions | binary / q4 build SHA calls | binary / q4 verify SHA calls | median q4 build ratio | median q4 verify ratio |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 11 / 9 | 4 / 3 | **0.897559x** | **0.979235x** |
| 8 | 23 / 19 | 5 / 4 | **0.952902x** | **1.158554x** |

At V=4, quaternary is a clean reference-path improvement: about **10.24% faster build** and **2.08% faster verification** at the median while using fewer hash calls.

At V=8, the result splits:

- build remains about **4.71% faster** at the median;
- deterministic build SHA calls fall **23 -> 19** (`-17.39%`);
- deterministic selected-verification SHA calls fall **5 -> 4** (`-20%`);
- but reference verification becomes about **15.86% slower** at the median.

The V=8 verification loss is not one noisy row. Every one of the six frozen rows loses:

- 64 KiB base 0: `1.149666x`;
- 64 KiB base 1: `1.163795x`;
- 64 KiB base 2: `1.166440x`;
- 256 KiB base 0: `1.153313x`;
- 256 KiB base 1: `1.163930x`;
- 256 KiB base 2: `1.147773x`.

The corresponding V=8 build ratios are all favorable, `0.946363x` through `0.964719x`.

The deterministic cryptographic work also moves in the favorable direction. Representative V=8 rows use:

- binary build parent work: **7 parent hashes / 560 parent-hash input bytes**;
- quaternary build parent work: **3 parent hashes / 383 parent-hash input bytes**.

For one 64 KiB V=8 family with 524 Surprise bytes, complete modeled build hashing is **1,788 B / 23 calls** binary versus **1,611 B / 19 calls** quaternary. Median selected verification is about **365 B / 5 calls** binary versus **359 B / 4 calls** quaternary.

## Causal interpretation

The frozen speed gate fails, so quaternary descriptor authentication is **not** promoted as a reference execution-speed win.

However, the failure does not point to excess cryptographic work: V=8 quaternary performs fewer SHA calls and feeds slightly fewer bytes to SHA while still running slower in CPython verification. The measured debt therefore sits outside the cryptographic-work floor, in the current reference verification machinery: wider sibling tuples, per-level list construction/filling, geometry validation and Python object/control overhead are the leading owners.

That distinction matters. The prior structural result remains valid:

- V=8 persisted descriptor hashes: **448 B binary -> 320 B quaternary**;
- 80-byte basis leaf worst-family complete stored fraction: **0.90183258x independent literals**;
- worst-row median authenticated 4 KiB touch: **1.18603516x**.

The correct response is therefore rehabilitation of the exported execution debt, not tuning arity or weakening the access gate.

## Hostile review / next falsifier

A Python micro-optimization alone would not establish product efficiency. The strongest next discriminator is an exact native binary-vs-quaternary descriptor-authentication A/B using the same domain-separated hashes and independently checked roots. If native V=8 verification becomes neutral/faster, the current loss is primarily interpreter/proof-object overhead. If native V=8 still loses materially, the quaternary tree has a real execution-architecture debt despite lower SHA work and must be redesigned or explicitly traded against its density benefit.

No arity search is reopened by this result. The existing fixed-partition fanout family remains retired; this experiment concerns the already-evidenced generic descriptor-auth representation boundary.

## Claim boundary

Deterministic authentication work plus hosted CPython/hashlib reference timing only. No native-product throughput, full archive creation, peak memory, canonical wire-format mutation, v0.29/v0.30 supremacy, portability or release authority is claimed.
