# ONE-G0.2 general Law archive boundary — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: preregistered before result-bearing execution

## Mission Lock

Close the product-boundary gap between the complete authenticated Surprise-only archive seam and the known-relation authenticated Law archive. Build one deterministic arbitrary-tree archive surface that performs bounded encoder-only discovery and compiles accepted structure into the existing six-operation ONE grammar. The reader must see only ordinary ONE Law + Surprise plus persisted authentication metadata.

This is a **boundary-completeness experiment**, not the September 11 Genesis comparison and not a density/speed promotion claim.

## Baselines

- Complete general fallback: `experiments/one/authenticated_archive_envelope.py`.
- Known-relation composition proof: `experiments/one/authenticated_law_archive.py`.
- Reader ontology: `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8` only.

## Invariants

1. Accept an arbitrary supported source tree (regular files, directories, safe relative symlinks) under the existing archive caps.
2. Preserve canonical path/mode/symlink/file bytes and exact per-file SHA-256 roots.
3. Persist the same generic AuthTree metadata used by the authenticated archive seam; complete and selective reads must use the existing reader path.
4. No reader discovery and no reader-visible historical mechanism/codec opcode.
5. Deterministic build output for identical input.
6. Bounded discovery: this seed may inspect only the immediately preceding regular file as a cross-file predictor; negative candidates must be sample-gated before any exact proof scan.
7. Every accepted Law is exact-proofed by the encoder. A false sample match must fall back to Surprise rather than export a wrong Law.
8. Unsupported opportunity is not an error: Surprise is the universal fallback.
9. No Genesis 15-workload corpus may be consumed by this experiment on 2026-09-10.

## Falsifiable hypothesis

A complete arbitrary-tree authenticated ONE artifact can automatically select a small set of generic relationships — exact Ref reuse, Fill, whole-file ADD8 and whole-file XOR — while using Surprise for everything else, without adding any reader operation or weakening integrity/selective reconstruction semantics.

## Discovery policy under test

For each regular file in canonical path order:

1. SHA-256 is computed for the file root/integrity boundary.
2. Fill is nominated only when a bounded sample is constant, then exact-proofed over the complete file.
3. If the immediately preceding regular file has equal length:
   - identical digest permits exact Ref reuse;
   - ADD8(constant) is nominated from bounded samples, then exact-proofed;
   - XOR(constant) is nominated from bounded samples, then exact-proofed.
4. Otherwise emit ordinary Surprise chunks/Concat.

The one-predecessor limit is deliberate: it gives an O(1)-history seed and makes creation-memory/search cost explicit. It is not claimed to be the final discovery policy.

## Disproof tests

Hold/retire this seed if any of the following occurs:

- arbitrary-tree round trip is not byte exact;
- repeated builds of the same tree differ;
- emitted Program contains an operation outside the six-operation ONE grammar;
- a sample false positive can cause an incorrect Law root;
- authenticated selective read differs from source bytes;
- manifest/path/symlink semantics differ from the existing complete archive seam;
- Surprise fallback fails on incompressible/already-compressed-like bytes;
- node/resource caps are bypassed;
- discovery retains an unbounded file history or performs full proof scans after a failed cheap gate.

## Cost model

Record at least:

- complete wire bytes;
- logical file bytes;
- manifest/auth-index bytes;
- node count and root classification counts;
- bytes sampled for nominations;
- bytes exact-proofed after a positive nomination;
- maximum retained predictor bytes;
- source reread bytes attributable to authentication placement.

Timing/RSS claims require a later repeated transfer benchmark with common process boundaries. This first boundary experiment may not infer product speed from Python unit-test wall time.

## Independent evidence plan

- reconstruct through the existing authenticated archive reader, not through builder internals;
- compare extracted/read bytes against independently retained source bytes and SHA-256;
- hostile false-pattern fixture that passes the cheap ADD8/XOR sample but fails exact proof;
- deterministic wire equality across repeated builds;
- inspect every emitted node op against the frozen generic grammar;
- compare at least one Law-bearing archive against authenticated Surprise-only wire size as a causal sanity check, without treating that fixture as general superiority.

## Hostile envelope for this seed

Use transfer/synthetic inputs only: incompressible deterministic bytes, constant bytes, identical copies, ADD8 relationship, XOR relationship, a false-pattern sample adversary, tiny files, empty file, nested directories and safe symlink where supported.

## Promotion law

This experiment may only earn `ADVANCE_BOUNDARY_SEED` if all semantic, determinism, authentication, false-pattern and bounded-discovery tests pass. That decision means the surface is eligible for broader transfer profiling and deeper Law discovery; it does **not** certify it as the best Genesis candidate.

Any correctness/integrity failure is `RETIRE_OR_REPAIR` before further benchmarking. A clean but weak-density result is `HOLD_FOR_DISCOVERY_DEPTH`, not permission to cherry-pick the known ADD8 archive for Genesis.
