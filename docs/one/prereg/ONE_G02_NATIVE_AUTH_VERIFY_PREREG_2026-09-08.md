# ONE-G0.2 native authenticated selective verifier — preregistration

Date: 2026-09-08
Branch authority: `research/cmpct1`
Experimental version: `ONE-G0.2`

## Mission lock / Referee

Exact-source stage-owner evidence from run `34247338432` at `b70f592f440b7ffe0a1fa28cfc858d8da8b964ca` returned `OWNER_AUTH_VERIFY`. Verification owns at least 60% of both wall and CPU stage time on at least 12/16 decisive 1 MiB rows in both the materialized-reference and packed-interval proof pipelines. Further proof-extraction tuning is therefore out of budget until verification is attacked.

## Hypothesis

The current Python verifier spends avoidable time constructing a `(level,index)->digest` dictionary, repeated parent sets, Python hash-input objects and intermediate joined payload state. The exact existing authenticated-tree grammar can be verified through contiguous interval arithmetic in one native boundary while preserving every leaf, parent and root SHA-256 semantic.

A native interval verifier should materially reduce in-memory authenticated selective-open cost without changing proof bytes, requested/touched data, root identity, reader-visible grammar or failure behavior.

## Candidate

Control: `experiments.one.auth_tree.verify_range`.

Candidate: a research-only C/OpenSSL verifier reached through ctypes. It consumes the existing `RangeProof`, derives the same contiguous selected-leaf interval and sibling positions, hashes the same domain-separated leaf/parent/root messages, rejects malformed/incomplete proofs, compares the same expected root, and returns exactly the requested bytes.

The candidate may use compact native scratch buffers. It may not change the proof, omit any hash, weaken root checking, increase requested/touched bytes, or require discovery at read time.

## Frozen semantics / hostile gates

Before timing, for every matrix row:

- Python and native outputs equal the exact requested source bytes;
- native output equals Python output;
- tampered payload fails;
- tampered sibling digest fails whenever a sibling exists;
- tampered expected root fails;
- malformed sibling coordinates/order fail closed;
- invalid request bounds fail closed.

Any semantic disagreement => `INVALIDATE_NATIVE_AUTH_VERIFY` regardless of speed.

## Frozen matrix

Deterministic 1 MiB source, existing authenticated leaf sizes `80, 96, 112, 192` bytes, requests:

- first 4 KiB;
- middle 4 KiB;
- final 4 KiB;
- middle 64 KiB.

16 decisive rows total. Use the already-promoted packed-interval proof generator so proof extraction is not inside verifier timing. Repetitions: 21 paired alternating after 2 warmups.

## Performance gate

The native verifier introduces a native subsystem and must earn that complexity.

Advance only if:

- all 16 decisive rows have native/control median wall <= `0.65x`;
- all 16 decisive rows have native/control median CPU <= `0.65x`;
- at least 12/16 rows have wall <= `0.50x` AND CPU <= `0.50x`;
- no proof/data traffic changes;
- exact semantics and hostile gates pass.

Otherwise `HOLD_NATIVE_AUTH_VERIFY`. Missing/duplicate matrix rows invalidate.

The 0.65 worst-row cap prevents a large average from hiding a weak selective shape. The 0.50 majority target demands a real architectural payoff rather than native complexity for a marginal gain.

## Claim boundary

A green result establishes only an in-memory implementation win for the existing exact authenticated-tree verification grammar on the frozen matrix. It does not canonize OpenSSL, change the ONE format, solve persistent authentication-index density, prove product I/O/RSS/portability, or authorize weaker selective integrity.

## Disproof / retirement

Retire this candidate if exact semantics cannot be maintained, malformed proofs cannot be rejected equivalently, or the frozen timing gate fails. If it holds despite semantic correctness, treat verification cost as dominated by unavoidable hash/payload work or ctypes/marshalling at this boundary and investigate a fused packed-proof/native-open representation rather than threshold tuning.
