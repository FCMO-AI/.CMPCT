# ONE-G0.2 packed one-shot auth-tree hashing — local diagnostic negative

**Status:** diagnostic negative; not hosted promotion authority  
**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Frozen hypothesis:** packing every authenticated node message contiguously and replacing the baseline multi-`SHA256_Update` construction with one `SHA256()` call per node would reduce auth-tree creation time enough to pass the preregistered gate.  
**Disproof rule:** any row above 0.98x, balanced 112-byte rows above 0.90x, or all-row median above 0.85x rejects the candidate.

## Why this diagnostic was run

The exact-source GitHub workflow had still not appeared after an explicit path-matching retrigger, while the current execution container could compile OpenSSL C but could not resolve `github.com` for a repository checkout. Rather than leave the Builder hypothesis unchallenged, a local causal reproduction was constructed from the committed semantics and timed on the same frozen 8-row size/leaf matrix.

This note is deliberately weaker than an exact-source hosted workflow artifact. It is strong enough to warn against promotion and to direct the next experiment; it is **not** a substitute for the repository's exact-head CI receipt.

## Preserved semantics

The diagnostic retained:

- SHA-256, 32-byte commitments;
- `ONE-L\0 || le64(index) || le64(total) || leaf_payload`;
- `ONE-P\0 || le32(level) || left_digest || right_digest`;
- `ONE-R\0 || le64(total) || le32(leaf_width) || tree_root`;
- identical binary-tree geometry and duplicate-right rule;
- identical deterministic source bytes;
- root equality check between baseline and candidate before accepting timings.

Only the hashing call shape differed:

- baseline: `SHA256_Init` + multiple `SHA256_Update` calls + `SHA256_Final`;
- candidate: contiguous scratch message + one high-level `SHA256(message, len, out)` call.

## Local measurement

Compiler command: `gcc -O3 -march=native ... -lcrypto`  
Timing clock: `CLOCK_MONOTONIC_RAW`  
Repetitions: 31 per row after warm-up  
Environment fact: system OpenSSL headers expose OpenSSL 3 deprecation warnings for the low-level SHA256 context API.

| Root bytes | Leaf bytes | Baseline median ns | Candidate median ns | Candidate / baseline |
|---:|---:|---:|---:|---:|
| 65,536 | 80 | 167,078 | 518,421 | **3.102868x** |
| 65,536 | 96 | 137,935 | 433,945 | **3.146011x** |
| 65,536 | 112 | 143,303 | 392,233 | **2.737089x** |
| 65,536 | 192 | 95,122 | 240,837 | **2.531875x** |
| 262,144 | 80 | 677,417 | 2,061,043 | **3.042503x** |
| 262,144 | 96 | 569,556 | 1,747,337 | **3.067893x** |
| 262,144 | 112 | 598,078 | 1,588,190 | **2.655490x** |
| 262,144 | 192 | 407,976 | 1,031,653 | **2.528710x** |

All roots matched exactly.

Median ratio across rows is roughly **2.90x**. The candidate missed the preregistered acceptance envelope by a very large margin on every row; even the best row was ~2.53x baseline.

## Causal interpretation

The attempted optimization attacked the wrong fixed cost for this OpenSSL 3 environment. The high-level `SHA256()` one-shot entry point appears to carry substantially more per-call overhead than a stack-resident low-level SHA256 context with several `Update` calls. Packing also adds explicit message copies. The combination overwhelms any reduction in `Update` call count for these tiny node messages.

This is a mechanism-level negative, not a leaf-size tuning problem. No post-result leaf threshold should be introduced to rescue it.

## Hostile review / limitations

- This was a locally reconstructed causal harness, not a checkout of the exact repository source; therefore exact-source hosted CI remains the stronger authority.
- The timing loop is sufficient to expose a multi-x regression but should not be used for small percentage claims.
- A different crypto library/provider implementation could change the magnitude. That possibility does not justify promotion: the current candidate must first pass the exact configured runner.
- Explicit staging bytes remain an additional cost even if another provider makes `SHA256()` cheaper.

## Decision

**Do not advance packed high-level one-shot SHA256 as the preferred auth-tree implementation on this evidence.** Preserve the Builder and await the exact workflow only as confirmation/falsification of environment dependence.

The next causally distinct auth-tree compute direction should avoid the high-level one-shot wrapper and instead test true amortization of per-node fixed work: e.g. level-wise/multi-buffer hashing, a reusable initialized hash state after fixed domain-prefix material where semantically safe, or a native batch primitive that preserves every authenticated byte while reducing context setup/finalization and message-copy traffic.
