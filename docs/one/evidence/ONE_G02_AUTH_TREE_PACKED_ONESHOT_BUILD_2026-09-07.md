# ONE-G0.2 packed one-shot auth-tree hashing — build handoff

**Status:** `BUILT / NOT YET RESULT-BEARING`  
**Experimental line:** `ONE-G0.2`  
**Preregistration:** `docs/one/prereg/ONE_G02_AUTH_TREE_PACKED_ONESHOT_PREREG_2026-09-07.md`  
**Current Builder source:** `benchmarks/one/native/one_g02_auth_tree_packed_oneshot.c`  
**Independent-oracle harness:** `benchmarks/one/one_g02_auth_tree_packed_oneshot.py`  
**Workflow:** `.github/workflows/cmpct1-one-g02-auth-tree-packed-oneshot.yml`

## Why this lane exists

The exact native auth-tree creation profile established that ONE's existing SHA-256 tree grammar costs about 2.68x–5.07x one whole-root SHA pass, with the balanced 112-byte leaf at about 4.10x–4.20x. The same receipt shows only ~1.86x source-equivalent bytes are presented to SHA at 112 B, implicating per-node initialization/finalization and tiny-message API overhead rather than raw SHA traffic alone.

The present Builder tests the smallest causal intervention named by that receipt: retain every authenticated byte and every tree/proof rule, but pack each exact node message contiguously and replace multiple `SHA256_Update` calls with one one-shot `SHA256` call per node.

## Frozen semantics

Baseline and candidate retain exactly:

- SHA-256 at 32-byte commitment width;
- leaf domain `ONE-L\\0`, index, total length and exact leaf payload;
- parent domain `ONE-P\\0`, level and exact left/right commitments;
- root domain `ONE-R\\0`, total length, leaf width and exact tree root;
- binary tree geometry, duplicate-right behavior and explicit root commitment.

The Python harness independently reconstructs the deterministic input and requires both native roots to equal `experiments.one.auth_tree.build_auth_tree` before timing can carry authority.

## Carrying-cost accounting added during Hostile Review

Packing is not free. On the frozen matrix the candidate explicitly stages a contiguous message before every SHA call. The harness now reports:

- leaf count;
- parent count;
- baseline `SHA256_Update` call count;
- candidate SHA call count;
- explicit candidate staging bytes;
- explicit staging/source-byte ratio.

Analytically, the candidate reduces roughly **3.5 Update calls per authenticated node to one SHA call per node**, but explicit staging is substantial:

| Root | Leaf | Candidate explicit staging / source |
|---:|---:|---:|
| 64 KiB | 80 B | ~2.205x |
| 64 KiB | 96 B | ~2.006x |
| 64 KiB | 112 B | ~1.865x |
| 64 KiB | 192 B | ~1.505x |
| 256 KiB | 80 B | ~2.202x |
| 256 KiB | 96 B | ~2.002x |
| 256 KiB | 112 B | ~1.859x |
| 256 KiB | 192 B | ~1.502x |

These are accounting bytes copied into explicit message scratch, **not measured physical memory traffic**. The experiment therefore directly falsifies whether the removed API/control overhead is worth this extra explicit staging.

Maximum bounded leaf scratch is 214 B; parent scratch is 74 B; root scratch is 50 B. No persistent state is added.

## Frozen gate

Advance only if:

- zero root/geometry mismatches;
- median candidate/baseline across all 8 rows <= 0.85x;
- both balanced 112-byte rows <= 0.90x;
- no row > 0.98x.

No post-result leaf thresholds, digest truncation, fanout changes or size dispatch are permitted.

## Execution truth

The workflow was committed and subsequently retriggered after it existed on the branch, but commits produced through the current connector have not generated an exact workflow run for this new workflow. A local diagnostic checkout was also attempted and failed before execution because the container could not resolve `github.com`.

Therefore there is **no timing result, PASS, FAIL, artifact or promotion authority yet**. Existing unrelated PR/push workflows must not be substituted for this experiment.

## Next action

Obtain one exact-source execution of the frozen workflow. If it passes, move the same hashing call shape into a broader authenticated-placement/ingest gate. If it fails, preserve the negative and do not tune leaf width or authentication semantics to rescue it; the next causally distinct auth-tree compute direction would need true level/multi-buffer batching or another way to amortize per-node fixed cost without changing authenticated bytes.
