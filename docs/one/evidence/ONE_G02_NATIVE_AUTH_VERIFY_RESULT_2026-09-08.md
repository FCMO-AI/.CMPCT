# ONE-G0.2 native authenticated-range verifier — exact result

**Date:** 2026-09-08  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`  
**Exact source:** `1e6a08a005f8fdb9e2b510b85752d1b229b12dd9`  
**Workflow run:** `34249225761`  
**Job:** `102139045779`  
**Artifact:** `10065687742` (`one-g02-native-auth-verify-1e6a08a005f8fdb9e2b510b85752d1b229b12dd9`)  
**Artifact digest:** `sha256:434a4d08070da60047d59cfa4314c7b0d01106dc6b771c4a55b53cacdf905da6`

## Mission lock

Hypothesis: moving the existing exact authenticated-range verification grammar into one native interval fold is sufficient, even while paying the current Python-to-ctypes proof-marshalling boundary, to beat the Python verifier by the preregistered material threshold across the 1 MiB selective-open matrix.

Disproof: any semantic/tamper mismatch invalidates; any row above `0.65x` on wall or CPU holds the candidate; fewer than 12/16 rows at or below `0.50x` on both wall and CPU also holds it.

## Exact verdict

`HOLD_NATIVE_AUTH_VERIFY`

The workflow failure is the benchmark's intended non-advance exit, not a semantic or infrastructure failure. Exact checkout/binding, the semantic/decision-law test gate, and evidence retention all passed. The result-bearing falsifier exited nonzero because the frozen performance contract was not met.

All 16 rows reported `semantic_ok=true` and `hostile_ok=true`. The native implementation therefore preserved the tested payload/root/sibling authentication behavior, but did not earn promotion as the charged wrapper shape.

## Decisive row evidence

The strongest evidence against simple promotion is the 192-byte-leaf family, where the native wrapper is slower than Python on three of four rows:

| leaf | request | wall ratio | CPU ratio |
|---:|---|---:|---:|
| 192 B | first 4 KiB | 1.162333x | 1.160854x |
| 192 B | middle 4 KiB | 1.109377x | 1.107282x |
| 192 B | final 4 KiB | 0.990317x | 0.991371x |
| 192 B | middle 64 KiB | 1.171155x | 1.167363x |

Finer leaves did show real implementation potential, but still missed the frozen all-row gate. Examples:

- 80 B / middle 4 KiB: `0.579603x` wall, `0.581719x` CPU;
- 80 B / final 4 KiB: `0.553228x` wall, `0.556072x` CPU;
- 96 B / middle 64 KiB: `0.614713x` wall, `0.615396x` CPU;
- 112 B / first 4 KiB: `0.886263x` wall, `0.887134x` CPU.

The native path therefore is not intrinsically noncompetitive, but its current charged boundary is not broadly superior.

## Causal interpretation

The candidate pays, inside every timed call, for work that a truly native selective-open boundary would not need to repeat in this form:

1. `b"".join(proof.leaf_payloads)`;
2. `from_buffer_copy` of the joined payload;
3. allocation and population of separate ctypes `levels`, `indices`, and packed hash arrays from Python sibling tuples;
4. expected-root copying;
5. native scratch allocation/free inside the verifier;
6. conversion of the native output back to Python `bytes`.

The 192-byte-leaf rows are especially diagnostic because verification has fewer leaf hashes and less Python reference work, so fixed boundary costs dominate sooner. This is a mechanism-level reason to test a packed/fused boundary rather than to retune the leaf-size matrix or relax thresholds.

This interpretation is still a hypothesis until the boundary is directly decomposed. The next experiment must therefore keep the exact hash grammar and hostile integrity checks while measuring whether prepacked proof state rehabilitates the same native kernel.

## Claim boundary

This result does **not** weaken authentication, change proof hash traffic, change stored ONE bytes, or change the reader-visible Law + Surprise representation. It is an implementation negative for one in-memory native wrapper shape.

OpenSSL/libcrypto remains research machinery only; no portability authority is granted.

## Next decisive experiment

Prepack the existing proof elements outside the verification hot call, retain the same payload bytes, sibling hashes, coordinates, expected root and C interval fold, and compare:

- Python reference verification;
- current fully charged native wrapper;
- prepacked native-kernel invocation.

If the prepacked kernel clears the original hard performance bar while the charged wrapper remains below it, the bottleneck is the Python/native proof boundary and the next design should fuse packed proof extraction with native verification. If the prepacked kernel also fails, further native verifier work should stop unless a different authentication algorithm/representation changes the cost model.
