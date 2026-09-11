# ONE-G0.2 packed one-shot authentication-tree hashing — hosted negative

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `ec4740f963b6667c43146083c54fc51b490627d0`  
**Workflow run:** `34094333253`  
**Job:** `101654426825`  
**Artifact:** `10008069146`  
**Artifact digest:** `sha256:1fef7f372d16610b217b6c9d4f67a653ba530766929da91c564494af62503a21`  
**Decision:** `reject_packed_oneshot_auth_tree_hashing`

## Mission lock

The exact ONE research authentication tree uses SHA-256 over unchanged leaf, parent and root messages. Earlier native profiling showed the tree cost about 2.68x–5.07x one whole-root SHA pass while presenting only about 1.86x source-equivalent bytes at the balanced 112-byte leaf. The packed one-shot candidate attempted to remove repeated `SHA256_Update` calls by copying each exact message into bounded contiguous scratch and invoking `SHA256()` once per node.

The frozen gate required zero semantic/geometry mismatches, median candidate/baseline <=0.85x, both 112-byte rows <=0.90x, and no row >0.98x. No leaf-size, fanout, digest-width, proof, authentication, or reader-semantic change was allowed.

## Exact hosted result

The exact-head GitHub Actions run completed the semantic boundary, ran the frozen A/B, retained the raw artifact, and then failed only at the preregistered scientific-decision enforcement step. All candidate roots matched baseline and the independent oracle; the speed hypothesis failed decisively.

| Root | Leaf | Baseline median | Candidate median | Candidate / baseline | Explicit candidate staging / source |
|---:|---:|---:|---:|---:|---:|
| 64 KiB | 80 B | 232.449 us | 880.006 us | **3.7858x** | 2.2053x |
| 64 KiB | 96 B | 192.589 us | 734.820 us | **3.8155x** | 2.0058x |
| 64 KiB | **112 B** | 196.166 us | 648.675 us | **3.3068x** | 1.8648x |
| 64 KiB | 192 B | 130.848 us | 397.543 us | **3.0382x** | 1.5051x |
| 256 KiB | 80 B | 930.120 us | 3435.302 us | **3.6934x** | 2.2017x |
| 256 KiB | 96 B | 771.851 us | 2849.698 us | **3.6920x** | 2.0017x |
| 256 KiB | **112 B** | 787.186 us | 2609.301 us | **3.3147x** | 1.8595x |
| 256 KiB | 192 B | 524.728 us | 1601.650 us | **3.0523x** | 1.5016x |

Frozen aggregate diagnostics:

- median candidate/baseline: **3.503375504x**;
- maximum row ratio: **3.815482712x**;
- maximum balanced-112 ratio: **3.314719774x**;
- root/geometry mismatches: **0**;
- repetitions: **31 per row**.

## Causal interpretation

This result rejects the idea that the dominant cost can be removed merely by replacing several low-level update calls with one high-level one-shot hash call while preserving the same node granularity.

The candidate also materialized every tiny authenticated message into scratch, adding about 1.50x–2.21x source-equivalent explicit staging bytes over the matrix. That copied traffic is real writer work. More importantly, OpenSSL's high-level `SHA256()` wrapper does not act as a cheap substitute for the low-level streaming path at thousands of tiny messages; the measured result is roughly three to four times slower, not faster.

The mechanism-level conclusion is stronger than the earlier local diagnostic: **API-call count was a misleading proxy for fixed hashing cost.** The next candidate must amortize or parallelize the cryptographic compression work itself across independent nodes, or eliminate avoidable node work without weakening authenticated semantics. Repacking the same per-node work is retired.

## Hostile review / claim boundary

This is native creation microprofile evidence only. It does not establish end-to-end ingest throughput, authenticated selective-range performance, product memory traffic, release authority, or superiority over v0.29/v0.30. It changes no stored bytes and no reader semantics.

Do not reopen this exact packed-one-shot shape with leaf-size dispatch, digest truncation, weakened proofs, changed fanout, or corpus thresholds. A reopening requires a causally different implementation that attacks cryptographic compression amortization itself (for example true multi-buffer/vectorized hashing or another byte-identical batching strategy) and re-runs the exact semantic oracle.
