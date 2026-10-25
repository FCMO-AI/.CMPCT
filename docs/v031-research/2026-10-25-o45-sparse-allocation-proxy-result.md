# O45 / O45b — Genuine r24 Builder sparse allocation and held-out Linux tmpfs

**Date:** 2026-10-25 UTC  
**Disposition:** source-exact filesystem-specific **positive** on tmpfs; original hosted filesystem **negative for the narrow `st_blocks`/hole divergence**. **Scientific evidence only; no product/release/promotion claim.**  
**Owner PR:** [#399](https://github.com/FCMO-AI/.CMPCT/pull/399), stacked on O42 [#396](https://github.com/FCMO-AI/.CMPCT/pull/396).

## Prospective custody and immutable source

- Original preregistration `a0448536000907abca8b7f9a4b8f88280eaa7c4c`, before instrument.
- Source-exact original O45 scientific CI [run 40154913865](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154913865), HEAD `d0b48904f94792f12dfb04807be55511c6013454`, artifact **12583658630**, ZIP SHA-256 `68580c4321cfbfe2ea8694689ade71863445f334bead12dfd57a55649755090e`: **SUCCESS**, independent JSON audit PASS; negative narrow host claim preserved.
- Held-out O45b preregistration `1318b3234fa68ea481bd49759121e6004b8540ff`, *after observing the negative*, before running the `/dev/shm` perturbation.
- Source-exact held-out scientific CI [run 40155119186](https://github.com/FCMO-AI/.CMPCT/actions/runs/40155119186), HEAD **`42a6c310326a6b813d8896db5e8d3f06dbe5234c`**, artifact **12584037857**, ZIP SHA-256 **`6cc240b8f5fe2cd32be52673fd3ec890e3acba3a821bfd57363371e0617d8447`**: **SUCCESS**. Both original and held-out independent JSON audit steps PASS.
- Exact immutable source blobs in both runs: `src/cmpct/builder.py` **`663ef0922992b1fbb8f19e6eea88d55c10a56044`**; `src/cmpct/codec.py` **`29526db4203723d83523fc95d074c346b63d7587`**; O42 `tools/v031_release_corpus_semantic_witness.py` **`65711cf8644f4eb1863499262ae8bfd787010d2e`**. Parent O42 HEAD `757577eed13bf277e003c4d3c694cc9e4f67d2c3`.

No product or format source, frozen corpus, official release-gate evaluator/threshold, historical benchmark or official timing boundary was changed. The result-document commit is **not** independently credited as a new exact-head scientific run.

## Question and causal model

Can the Builder's `st_blocks * 512 >= 0.75 * logical_size` shortcut reject an otherwise suitable `S_SPARSE` representation even when Linux `SEEK_DATA` still reports the original sparse hole topology? That prefilter executes *before* `SEEK_DATA/SEEK_HOLE`, so it could be a false-negative when allocated-but-unwritten physical blocks are counted by `st_blocks` and skipped by `SEEK_DATA`.

A single `payload.bin` has exactly **8,388,608 logical bytes**, a pseudorandom terminal 4,096-byte extent and all other bytes zero. Five sequential states of the **same inode** were built with the unchanged Builder (one worker, reproducible encoding), then strongly verified and read/extracted with the unchanged Reader: sparse, unchanged repeat, `posix_fallocate` preallocation, physically written dense zeroes, sparse restored. Checks independently committed to path, inode/device, mode, mtime, complete logical SHA-256, O42 semantic digest and three actual Reader operations. Frozen historical inputs were not regenerated.

## Original GitHub Actions Linux filesystem: correctly negative narrow prediction

| File state | Allocated bytes (`st_blocks*512`) | First `SEEK_DATA` | Actual r24 storage | Complete archive bytes |
|---|---:|---:|---|---:|
| Sparse | 4,096 | 8,384,512 | `S_SPARSE` | **5,090** |
| Sparse repeat | 4,096 | 8,384,512 | `S_SPARSE` | **5,090** |
| After `posix_fallocate` | 8,388,608 | **0** | `S_CDC` | **5,249** |
| After writing all zero bytes | 8,388,608 | 0 | `S_CDC` | **5,249** |
| Sparse restored | 4,096 | 8,384,512 | `S_SPARSE` | **5,090** |

**Original verdict: `NOT_SUPPORTED_ON_THIS_HOST`.** Preallocation physically charged the blocks *and* changed the filesystem hole oracle to 0. It is therefore invalid to claim the `st_blocks` prefilter was *unnecessarily* rejecting `S_SPARSE` by comparison to this host's `SEEK_DATA`; the alternative explanation survived. Nonetheless, logical identity stayed constant while complete archive size increased **159 bytes**, demonstrating that O42's logical/typed corpus digest is not a comprehensive archive-serialization/physical-topology identity.

## Held-out Linux tmpfs: false-negative admission demonstrated

The *same unchanged five-arm Builder/Reader instrument* was run with input/results on `/dev/shm` (tmpfs), separately preserving original JSON. The original runner file state and tmpfs file state were not conflated.

| File state | Allocated bytes (`st_blocks*512`) | First `SEEK_DATA` | Actual r24 storage | Complete archive bytes |
|---|---:|---:|---|---:|
| Sparse | 4,096 | **8,384,512** | `S_SPARSE` | **5,090** |
| Sparse repeat | 4,096 | 8,384,512 | `S_SPARSE` | **5,090** |
| After `posix_fallocate` | **8,388,608** | **8,384,512 (unchanged)** | **`S_CDC`** | **5,249** |
| After writing all zero bytes | 8,388,608 | 0 | `S_CDC` | 5,249 |
| Sparse restored | 4,096 | 8,384,512 | `S_SPARSE` | **5,090** |

**Held-out verdict: `SUPPORTED_SAME_HOLE_TOPOLOGY_ALLOCATION_PROXY_FALSE_NEGATIVE`.** The Linux tmpfs `SEEK_DATA` oracle reports the same sparse physical-data start before/after preallocation, but the early `st_blocks` cutoff prevents the unchanged Builder from using sparse representation. Exact complete archive penalty in this illustrative highly compressible 8MiB case: **+159 bytes** (~3.12% over 5,090-byte baseline). This is a representation-admission gap, not proven practically important compression headroom.

Both independent audit steps recomputed classification from raw source SHA, cases, physical metrics, complete byte counts and original output SHA; they did not trust narrative flags alone. In all ten archived tests across the two filesystem environments, original CMPCT `verify()`, `read()` and `extractall()` were exact. Same-inode/path/mode/mtime/semantic digest checked within each environment; sparse/unchanged/restored full archive SHA identical.

## Stronger simpler control, alternatives and inherited negatives

The decisive alternative was that the host might report preallocated extents as data; the default hosted filesystem **did exactly that**, falsifying the universal interpretation. Only the held-out tmpfs satisfied the more specific same-`SEEK_DATA` causal fork. This host contrast is the key decision-changing evidence.

Although code reading isolates the early `st_blocks` prefilter as the mechanism, **no separate one-factor patched-Builder product ablation** was run. Do not claim an integrated product fix, release regression or full cross-platform guarantee. `lseek(2)` allows filesystem-dependent `SEEK_DATA/SEEK_HOLE` semantics; its data/hole mappings need not correspond one-for-one to real disk blocks. Source mutation occurred between separate builds, not during an adversarial concurrent scan, so this does not prove snapshot atomicity.

Both representations reconstruct the identical 8MiB logical stream. `S_SPARSE` vs `S_CDC` is a valid, potentially deliberate tradeoff when filesystem allocation behavior changes. Selecting an already sparse-looking representation is not automatically the right generic strategy on every filesystem.

## Whole-system accounting and decision

Directly measured per arm: full CMPCT stored bytes, logical size/hash, inode, `st_blocks`, `SEEK_DATA/HOLE`, physical storage kind, source witness, authentic Reader exactness, descriptive build wall (raw JSON). Not measured: reliable A/B CPU/RSS, additional admission `lseek` cost across large-file populations, page cache/I/O amplification, other input families, multi-platform semantics, cold installed-package performance, concurrency, crash recovery or official frozen-parity release comparison.

**Decision:** advance the *physical allocation vs sparse-reporting representation* science on Linux tmpfs, preserve the original-host negative unchanged, **do not promote a code change on a 159-byte illustrative gain**. The cheapest next engineering fork is a single-factor admission A/B on independent, realistically sparse/preallocated inputs *only if* broad profile confirms enough bytes/runtime headroom to outweigh extra `SEEK_DATA` calls and platform-specific behavior. Otherwise retire the family and prioritize conversion of validated Reader/Writer integration work into canonical product releases.

## Discovery and concurrency handoff

Primary O45 decision changed once via held-out structural perturbation. No collision detected with #396 (official semantic fingerprint owner), #398 (hardlink-heldout owner), #392 (hardlink product) or #240 (shared discovery state). No Discovery Engine policy lesson earned beyond the prospective ordinary requirement to test material physical-layout assumptions across different supported filesystems. No modification to `docs/discovery/STATE.json` or frozen evaluators. No merge or release authority implied.

**Research evidence:** positive only within tmpfs causal semantics. **Product evidence:** existing Builder/Reader operations exact on the synthetic controls; no shipped change. **Infrastructure:** genuine source-bound hosted workflow, independent audit and immutable artifacts. **Unmeasured:** broader speed, memory, portability, release conditions and generality.
