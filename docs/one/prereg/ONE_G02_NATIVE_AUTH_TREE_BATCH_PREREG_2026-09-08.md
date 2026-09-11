# ONE-G0.2 native auth-tree batch preregistration — 2026-09-08

## Mission lock

The exact-source shared-auth creation-cost audit on `research/cmpct1` showed that the already-feasible fine authenticated-range leaves export material creation debt: the current Python `AuthTree` builder is roughly 14–32x slower than one whole-root SHA-256 and presents about 1.50–2.21 source-bytes of input to SHA-256 through hundreds to thousands of independent invocations. This experiment asks what fraction of that bill is Python dispatch/object materialization versus the exact cryptographic work required by the current generic authentication grammar.

This is **not** a format or integrity change. The hash domains, little-endian metadata, odd-node duplication, leaf geometry, root commitment, stored-hash count, and resulting root digest are frozen to `experiments/one/auth_tree.py`.

## Falsifiable hypothesis

A single native level-batched builder that performs the same SHA-256 invocations in C and emits all tree-node hashes into one packed buffer will materially reduce creation time while preserving byte-exact roots.

### Candidate

`bytes -> one ctypes boundary -> native leaf/parent/root hashing -> packed node buffer + root digest`

### Control

Current `build_auth_tree()` Python implementation using the same input bytes and leaf size.

## Frozen matrix

- deterministic random roots: 64 KiB and 256 KiB;
- passing leaf sizes: 80, 96, 112, 192 bytes;
- 2 warmups + 15 alternating paired timed repetitions per row;
- native build/loader compilation is outside timed repetitions;
- conversion to a ctypes input view is charged inside the native candidate; Python reconstruction of an `AuthTree` object is **not** required on the hot candidate path because the intended writer sidecar is the packed hashes themselves.

## Semantic gate

Every row must prove:

1. candidate root digest equals `build_auth_tree(...).root` exactly;
2. candidate packed node count equals the exact sum of reference level widths;
3. every packed node digest equals the corresponding reference `levels` digest in level order;
4. stored-index byte accounting remains unchanged.

Any semantic disagreement yields `INVALIDATE_NATIVE_AUTH_TREE_BATCH` regardless of speed.

## Advancement gate

At 256 KiB:

- median candidate/control wall ratio must be <= 0.50 on **all four** leaf sizes;
- median candidate/control CPU ratio must be <= 0.50 on **all four** leaf sizes;
- no 64 KiB row may exceed 0.75x on either wall or CPU.

These thresholds intentionally require a large win: a native boundary is not justified for a cosmetic reduction.

Decision values:

- `ADVANCE_NATIVE_AUTH_TREE_BATCH`
- `HOLD_NATIVE_AUTH_TREE_BATCH`
- `INVALIDATE_NATIVE_AUTH_TREE_BATCH`

## Resource / claim boundary

The experiment reports packed-hash bytes and node counts but does not claim process RSS. It does not benchmark proof verification, archive placement, filesystem traversal, decoder throughput, or full product ingest. A green result only establishes a preferred creation primitive for the existing generic authenticated-range tree.

## Hostile-review questions frozen before result

- Is the candidate secretly changing the digest grammar or omitting hashes?
- Is native compilation being charged asymmetrically?
- Is Python teardown leaking into the next arm's clock?
- Does the packed representation merely defer an unavoidable Python object graph? (For the writer sidecar, no Python graph is semantically required; proof APIs may materialize views later.)
- Does OpenSSL availability make this only a hosted-Linux diagnostic? Yes: this experiment may use system `libcrypto` to falsify the boundary. Promotion beyond research requires a portable backend or a controlled dependency decision.
