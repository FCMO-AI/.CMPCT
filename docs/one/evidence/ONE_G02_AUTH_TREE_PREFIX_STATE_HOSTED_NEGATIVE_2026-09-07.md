# ONE-G0.2 authentication-tree SHA prefix-state amortization — hosted negative

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `a969b5f3fdaa08c10a8dcdf18f8d1994ae9b2cdf`  
**Workflow run:** `34099706738`  
**Job:** `101671072074`  
**Artifact:** `10010011997`  
**Artifact digest:** `sha256:702cf7b3d85b6282bc24f4af7db68f8ba800b93332eb58e34f5a66574b3b397d`  
**Decision:** `reject_auth_tree_prefix_state_amortization`

## Mission lock

The prior packed one-shot experiment proved that fewer API calls plus complete-message staging is strongly counterproductive. This causally different candidate instead preserved the existing low-level SHA-256 streaming path but initialized invariant prefix state only once per tree / tree level and cloned that bounded `SHA256_CTX` state for each node.

Authenticated bytes, SHA-256, binary-tree geometry, proof semantics, commitment width and reader representation were unchanged. The candidate added exactly **0 bytes** of payload/message staging.

Frozen gate:

- zero semantic/accounting mismatches;
- candidate explicit payload staging = 0 B;
- median candidate/baseline across all eight rows <= 0.96x;
- both 112-byte rows <= 0.98x;
- no row > 1.00x.

## Exact hosted result

All roots matched the independent Python oracle and all accounting checks passed. The performance gate failed.

| Root | Leaf | Baseline median | Candidate median | Candidate / baseline | Baseline SHA inits | Candidate seed inits | Context clones |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 KiB | 80 B | 217.372 us | 214.948 us | **0.988849x** | 1,644 | 12 | 1,644 |
| 64 KiB | 96 B | 175.871 us | 180.077 us | **1.023915x** | 1,371 | 12 | 1,371 |
| 64 KiB | **112 B** | 229.720 us | 226.626 us | **0.986531x** | 1,178 | 12 | 1,178 |
| 64 KiB | 192 B | 125.596 us | 119.297 us | **0.949847x** | 688 | 11 | 688 |
| 256 KiB | 80 B | 884.362 us | 857.000 us | **0.969060x** | 6,560 | 14 | 6,560 |
| 256 KiB | 96 B | 713.108 us | 692.437 us | **0.971013x** | 5,468 | 14 | 5,468 |
| 256 KiB | **112 B** | 733.707 us | 719.287 us | **0.980346x** | 4,690 | 14 | 4,690 |
| 256 KiB | 192 B | 484.708 us | 477.268 us | **0.984651x** | 2,737 | 13 | 2,737 |

Aggregate decision quantities:

- median candidate/baseline: **0.982498465x** (~1.75% lower elapsed);
- maximum row ratio: **1.023915256x**;
- maximum balanced-112 ratio: **0.986531430x**;
- semantic/accounting mismatches: **0**;
- candidate payload/message staging: **0 B**;
- repetitions: **31 per row**.

## Causal interpretation

Prefix-state reuse is real but too small and unstable to carry as the new auth-tree research baseline. It reduces thousands of `SHA256_Init` calls to roughly one seed initialization per structural level, yet every node still requires a full SHA context copy, node-specific updates, finalization and scalar compression. Those remaining costs dominate enough that the broad median gain is only ~1.75%, and one frozen row regresses by ~2.39%.

This closes a useful ambiguity: **per-node prefix initialization is not the main remaining owner.** Together with the packed-one-shot rejection, the scalar API surface has now been falsified from both directions:

1. staging complete messages and calling a high-level one-shot API is dramatically worse;
2. reusing low-level prefix state is only a small, noisy improvement.

The next credible speed mechanism must amortize cryptographic compression work across independent nodes (true multi-buffer/vectorized hashing), exploit parallel independent tree work with CPU as well as wall-time accounting, or change authenticated placement so fewer node hashes are required without weakening proof locality/security.

## Hostile review / claim boundary

This is exact-tree native creation microprofile evidence only. It does not establish end-to-end ingest, product-native portability, authenticated selective-read performance, or v0.29/v0.30 superiority. `SHA256_CTX` is OpenSSL-specific implementation state and was never granted format/ABI authority.

Do not reopen scalar context-cloning via leaf-size dispatch or corpus thresholds. A reopening requires a causally different hashing kernel or authenticated-placement representation and must preserve exact roots/proofs or explicitly preregister any representation change with complete security/access/storage accounting.
