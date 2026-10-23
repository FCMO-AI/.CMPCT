# v0.31 O0 sparse-Merkle proof economics — exact-head research outcome

**Decision: O0_HEADROOM_NARROW.** This is a new candidate logical commitment model, NOT r24 flat SHA-256 equivalence or a product improvement. Shipped v0.30.0/revision24, correctness gates, and PR #270's failed sparse-extract gate remain unchanged.

Preregistered before results at commit `2c103e509af791ad0c79f5f80e55a912d1df19b3`. Hosted HEAD `f759bd8abb9c7745ebf46986971ec7ebef42b7dd`; [SUCCESS run 40001726462](https://github.com/FCMO-AI/.CMPCT/actions/runs/40001726462); [artifact 12522576430](https://github.com/FCMO-AI/.CMPCT/actions/runs/40001726462/artifacts/12522576430); artifact SHA256 `16954bfb434946038bd17ea448c43fb7d3501d7cc08a7c2663552a370c79184d`.

Raw O0 JSON SHA256 `075bb243ea21c6680212576ad55a69d2883c1606a44a43a3c4748ece6e89474d`; independent full-array differential JSON SHA256 `13a6424b9b4370d11ac2ba3c91304727099ad8b622342e551960e30339d781f1`. Hosted 640/640 cross-checks passed (320 small logical shapes x 2 leaf sizes). Source Git blobs `9938ac962611b41a20f32f8179d51e5a0e249aa5` and `0a411e7ba1785564ed87b1b9f190818d5dfbd2ba`.

## Alternating hosted timing and fully charged metadata

Five wall/CPU repetitions per case; table contains median wall milliseconds and candidate extra index bytes `48 + 40k` where k is data-touched 64KiB leaves. All raw observations are in the artifact.

| Synthetic source | Flat SHA ms | Merkle ms | Extra index | k | Decision |
|---|---:|---:|---:|---:|---|
| 128MiB, 4MiB clustered data | 64.883 | 5.381 | 2,608B | 64 | Headroom |
| Same extents shifted | 65.110 | 5.633 | 2,688B | 66 | Perturbation survives |
| 128MiB all holes | 64.022 | 1.049 | 48B | 0 | Headroom |
| 128MiB plus partial tail | 64.334 | 2.280 | 1,328B | 32 | Headroom |
| 128MiB with 1 byte/64KiB | **67.570** | 77.586 | **81,968B** | 2,048 | **LOSER** |
| 16MiB dense | **8.023** | 10.558 | 10,288B | 256 | **LOSER** |

The positive case is ~12.1x faster in this detached SHA model only. Distributed data is ~14.8% slower and incurs ~40x its 2,048 physical payload bytes as extra index. Strong negatives preserved. No CMPCT Builder/Reader archive bytes, extraction or release benchmark was executed by this oracle.

## Structural generality and proof limits

Merkle root uses explicit domain separation, file length binding, leaf hashes and sibling proofs. Hole positions were gifted by the source generator, not discovered. Logical SHA-256 and Merkle root are **different cryptographic identifiers**. Changing data, offsets, length, digest map or proof siblings is rejected by the controlled checks. This is integrity consistency, NOT cryptographic origin authentication; it also does not independently authenticate the physical hole-allocation map.

The present O0 candidate caches all touched-leaf buffers and constructs O(n) tree nodes, where `n=ceil(logical_size/leaf_size)`. At 1TiB logical size and 64KiB leaves this is 16,777,216 leaves, >1 GiB of raw 32-byte node digest storage including both levels, before Python object overhead. This **falsifies unbounded general product use** without collapsed zero subtrees and streaming bounded memory.

A cheap prospective disproof before algorithm implementation: assess occupied-leaf fraction `k/n` and charge `48+40k` bytes against source payload and full stored artifact. If `k≈n`, no bulk hash-byte saving is available. Do not pick a policy by fixture identity. Existing r24 still requires its real logical SHA commitment.

The mature [Linux fs-verity documentation](https://docs.kernel.org/filesystems/fsverity.html) describes size-bound Merkle descriptors, verified block reads and caching. It is relevant prior art, not this implementation's independent product comparator.

## Next decision

A distinct O1 collapsed-empty-subtree/streaming proof with explicit cold-index bytes, peak RSS, adversarial offsets, native readers and completely charged creation/extraction. No release/format change before full correctness, portability, recovery and benchmark evidence. PR #255/#270/#273/#274 owners retain their work; this scientific branch changes none of their sources and does not overwrite Discovery STATE. No policy change earned.
