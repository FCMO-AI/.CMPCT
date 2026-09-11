# ONE-G0.2 authentication-tree true multi-buffer SHA-256 — hosted positive

**Experimental line:** `ONE-G0.2`  
**Result-bearing ONE source:** `defa1d89ad41fc35df4a66aba7ceacfef68e28df`  
**External research oracle:** Intel Multi-Buffer Crypto for IPsec v2.0 at exact commit `4f808234a91e87147a4f26167df40f3fd7c7f0c6`  
**Workflow run:** `34100358726`  
**Job:** `101673154749`  
**Artifact:** `10010366880`  
**Artifact digest:** `sha256:5114a7eb51847e8840619a01092b4f76b4d840d227cfb104f747689efbca0752`  
**Decision:** `advance_multibuffer_auth_tree_hashing_mechanism`

## Mission lock

Earlier exact hosted tests rejected two scalar API-shape hypotheses:

1. complete-message staging plus OpenSSL's high-level one-shot `SHA256()` regressed to 3.5034x median candidate/baseline;
2. cloning pre-seeded scalar `SHA256_CTX` state improved median elapsed only ~1.75% and regressed one row.

Those negatives isolated the next falsifiable mechanism: exploit the independence of same-level authentication nodes by executing SHA-256 compression work in parallel lanes rather than merely changing scalar API calls.

This experiment used Intel Multi-Buffer only as a mature external research oracle/prototype. It is not a CMPCT dependency, format requirement, reader requirement, portability authority, or release component.

## Frozen gate

The candidate had to preserve every authenticated byte, exact binary-tree geometry, 32-byte SHA-256 commitments, proof semantics and independent Python roots. All message materialization, per-tree arena/job allocations, job setup, burst submission and output handling were inside the candidate timer.

Frozen matrix: 64 KiB and 256 KiB roots x leaf widths 80, 96, 112 and 192 bytes, 31 alternating repetitions per row.

Advance only if:

- zero root/geometry/accounting mismatches;
- median candidate/baseline <= **0.80x**;
- both 112-byte rows <= **0.85x**;
- no row > **0.95x**.

## Exact hosted result

All exact-root/oracle/accounting checks passed. Scientific exit code was 0 and the preregistered enforcement step passed.

| Root | Leaf | Baseline median | Candidate median | Candidate / baseline | Candidate staging / source |
|---:|---:|---:|---:|---:|---:|
| 64 KiB | 80 B | 233.720 us | 220.295 us | **0.942559x** | 2.2053x |
| 64 KiB | 96 B | 182.008 us | 150.549 us | **0.827156x** | 2.0058x |
| 64 KiB | **112 B** | 154.394 us | 118.120 us | **0.765056x** | 1.8648x |
| 64 KiB | 192 B | 105.044 us | 78.576 us | **0.748029x** | 1.5051x |
| 256 KiB | 80 B | 753.692 us | 599.728 us | **0.795720x** | 2.2017x |
| 256 KiB | 96 B | 609.317 us | 492.643 us | **0.808517x** | 2.0017x |
| 256 KiB | **112 B** | 621.828 us | 465.387 us | **0.748418x** | 1.8595x |
| 256 KiB | 192 B | 429.702 us | 324.562 us | **0.755319x** | 1.5016x |

Frozen aggregate diagnostics:

- median candidate/baseline: **0.7803879525x** (~21.96% lower elapsed);
- maximum row ratio: **0.942559473x**;
- maximum balanced-112 ratio: **0.765055637x**;
- root/accounting mismatches: **0**;
- burst capacity reported by the prototype: **128 jobs**;
- external prototype commit exactly matched the frozen pin;
- all per-tree staging remained charged to elapsed time.

At the balanced 112-byte leaf, exact creation elapsed improved by ~23.49% at 64 KiB and ~25.16% at 256 KiB while still materializing ~1.86 source-equivalents of authenticated messages.

## Causal interpretation

This is the first auth-tree speed experiment in the current sequence to attack the dominant mechanism rather than its call surface. The result shows that **same-level cryptographic lane batching is causally useful**: it survives substantial explicit staging traffic and still clears a hard 20% median speed gate.

The contrast among the three experiments is informative:

- packed scalar one-shot: ~3.50x median — catastrophic;
- scalar prefix-state cloning: ~0.9825x median — real but immaterial/noisy;
- true multi-buffer SHA: ~0.7804x median — material and gate-clean.

Therefore the useful structure is not “fewer SHA calls”; it is **parallel execution of independent cryptographic reconstruction/authentication cones**. That principle belongs naturally in ONE's native writer architecture.

## What this does not solve

This positive repairs writer compute only. It does **not** solve the separate authenticated-placement storage/access economics. Existing negative evidence still shows that widening the reconstructed-root Merkle fanout does not clear the repair-factor target and that a 32-byte commitment-width tree remains above the desired storage factor. Faster hashing cannot make those stored proof/index bytes disappear.

It also does not authorize Intel Multi-Buffer as a permanent dependency. The prototype requires architecture-specific native support and a public burst API that forces complete authenticated-message staging. Product authority requires ONE's own optional hashing-dispatch boundary, scalar fallback, CPU-time and explicit memory accounting, feature detection, non-x86 strategy, semantic vectors, and broader end-to-end ingest measurements.

## Hostile review / next falsifier

The strongest self-critique is that wall-time speed alone can hide resource tradeoffs. Although this prototype appears to use SIMD/multi-buffer work rather than worker threads, this receipt does not yet measure process CPU time, peak resident memory, energy, or whole ingest. It also stages 1.50x–2.21x source-equivalent bytes, which is contrary to ONE's fused-observation/memory-traffic law even though elapsed time wins.

The next decisive experiment is therefore not another threshold sweep. Build a narrow ONE-owned hash-batch abstraction with a scalar exact-root fallback and instrument **elapsed time + process CPU + explicit writer workspace/staging bytes**. First use the proven external kernel behind that abstraction to establish the architecture boundary; then test whether scatter/gather or pre-seeded lane input can eliminate full-message staging while preserving the multi-lane gain. Promotion into the broader ingest path requires that resource-aware evidence, not this microprofile alone.
