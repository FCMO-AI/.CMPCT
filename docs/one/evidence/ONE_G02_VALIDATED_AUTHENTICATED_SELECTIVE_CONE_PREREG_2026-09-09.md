# ONE-G0.2 — validated authenticated selective-cone preregistration

Date: 2026-09-09  
Branch: `research/cmpct1`  
Experimental version: `ONE-G0.2`  
Status: preregistered; execution is contingent on reusable validated-Program evidence

## Mission Lock / Referee

The fixed-cone preflight diagnostic demonstrated that the current raw-Program selective APIs pay whole-graph validation on every request even when the requested byte cone is fixed. That is a real control-plane locality cost, but it creates a benchmark fairness trap: a native candidate must not receive reusable validation while a generic incumbent repeats full preflight.

### Hypothesis

After one exact full-Program validation/open step shared by both readers, generic authenticated range reconstruction and native authenticated cone reconstruction can be compared at the true repeated-request boundary. The native path should reduce cone execution CPU and data movement without borrowing any integrity, validation, resource, or authentication work from the comparator.

### Hard invariants

- Both arms consume the same sealed immutable `ValidatedProgram` snapshot created by one ordinary full `validate_shape + _preflight` boundary.
- The one-time validation/open CPU is disclosed separately and identically shared; it is not counted as a per-request differentiator.
- Both arms consume the same persisted generic `AuthTree` and expected auth root.
- Both arms reconstruct exactly the same Merkle-leaf-aligned dependency cone and must authenticate the requested bytes against the same root commitment.
- No whole-root reconstruction or whole-root hash may appear in a positive selective read.
- Raw-Program APIs retain their current fail-closed full-preflight behavior.
- Unsupported ONE topology remains explicit fallback/rejection; no Law-family reader opcode is added.

## Frozen comparison boundary

### Incumbent repeated-read arm

`ValidatedProgram -> RangeEvaluator.from_validated -> reconstruct aligned cone -> generic leaf proof preparation -> verify_range -> requested bytes`

### Candidate repeated-read arm

`ValidatedProgram -> compile_validated_native_law_range_plan -> native cone execution -> identical generic leaf proof preparation -> verify_range -> requested bytes`

Authentication proof preparation and verification are charged in both arms. The candidate may not claim their cost as zero simply because the native reconstruction stage is faster.

## Matrix

Reuse the authenticated-native-selective-cone families and request geometry after the reusable-validation gate is admissible:

- add8, XOR;
- sparse Surprise cracks;
- mixed Fill/Literal/Concat/Law topology supported by the candidate;
- tiny, head, middle, tail, and auth-leaf-boundary-crossing requests;
- at least 128 KiB, 512 KiB, and 4 MiB roots;
- fixed requested cone while unrelated valid Program nodes grow;
- corrupt expected commitment, sibling hash, proof coordinate/payload, malformed Program, resource over-budget, and unsupported topology controls.

## Required measurements

Report separately:

- one-time immutable Program validation/open CPU and retained certificate bytes;
- generic cone reconstruction CPU/wall, work, materialized bytes, nodes touched;
- native plan CPU/wall, command count, source reads, plan writes, packed source bytes;
- native execution CPU/wall and sink writes;
- proof-payload preparation CPU/wall and bytes;
- sibling-proof preparation CPU/wall and hash bytes;
- verification CPU/wall;
- requested bytes, cone bytes, persistent auth-index bytes, peak temporary state;
- complete per-request CPU/wall and modeled movement for both arms.

## Frozen promotion law

Do not weaken the predecessor authenticated-cone semantics/resource gates. In addition:

1. exact requested-byte parity and successful authentication on every valid row;
2. 100% hostile corruption/resource rejection;
3. no positive row performs whole-root reconstruction/hash;
4. fixed-cone repeated-read CPU for both arms must remain <=2.0x from 0 to 4096 unrelated valid nodes after shared open;
5. every native-positive repeated-read CPU <=1.10x the validated generic incumbent;
6. median native-positive repeated-read CPU <1.0x incumbent;
7. median candidate modeled data movement <=0.75x incumbent;
8. temporary state remains cone/proof-bounded rather than root-sized;
9. one-time open cost is reported and an amortization table for request counts 1, 4, 16, 64 is retained so repeated-read speed is not presented as a free first-open speedup.

## Disproof / HOLD

HOLD if shared-open validation fails to remove graph-size sensitivity, if proof preparation dominates enough to erase the native cone gain, if any hostile case weakens, or if the native path wins only because accounting differs between arms.

A HOLD should name the measured stage owner; thresholds do not move.
