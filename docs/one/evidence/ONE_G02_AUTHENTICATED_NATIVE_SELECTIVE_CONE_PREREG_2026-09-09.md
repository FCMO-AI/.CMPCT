# ONE-G0.2 Authenticated Native Selective Cone — preregistration

Date: 2026-09-09
Experimental version: `ONE-G0.2`
Status: **PREREGISTERED — NO RESULT YET**

## Mission lock

Test whether the promoted generic ONE Law reader can answer an authenticated requested range without reconstructing or hashing the complete root, while keeping the same reader-visible Law + Surprise grammar, the existing authenticated-range hash grammar, deterministic resource semantics, and fail-closed behavior.

This is a reader-systems experiment, not a new Law, codec, opcode, or product-format proposal.

The candidate boundary is:

`requested range -> exact dependency cone -> bounded native/generic terminal execution for only the required cone -> charged proof preparation from the existing authenticated tree -> proof verification/root verdict -> requested bytes`

The incumbent boundary is the current generic range evaluator plus the current authenticated selective-open path under the same requested range and authentication semantics.

The candidate must not materialize a complete root merely to authenticate a small range.

## Prior evidence that constrains this gate

1. `ADVANCE_NATIVE_LAW_TERMINAL_READER_V2` establishes that eligible whole-root Law execution is no longer the hot reader bottleneck. At its frozen 21-row gate, median eligible native/reference CPU was `0.01165033595932275x`, worst eligible was `0.019931932834506394x`, median controls were `1.0071253954775798x`, and median eligible modeled traffic/reference VM work was `0.5500324291328068x`.
2. The generic `RangeEvaluator` reconstructs exact requested slices but is intentionally unauthenticated under the single whole-root SHA. It cannot claim authenticated random access by itself.
3. The existing authenticated selective-open stage-owner work explicitly charges proof extraction/preparation. Prior native-verifier work does **not** authorize treating verifier-kernel speed as end-to-end selective-open speed. Proof preparation, payload materialization, proof-coordinate handling, and hashes read remain part of the bill.
4. The existing `AuthTree`/`NativeAuthTree` grammar remains the authentication substrate for this experiment. No second proof format is introduced.

## Falsifiable hypothesis

For ordinary ONE Programs whose requested output range intersects bounded Law/Surprise cones, the reader can reconstruct and authenticate only the required cone with total CPU and data movement proportional to the requested cone/proof footprint rather than full-root size, while preserving exact bytes, authentication, resource rejection, and failure behavior.

## Disproof conditions

Any of the following is a HOLD or INVALIDATE, never a reason to move the benchmark:

- requested bytes differ from the reference whole-root reconstruction slice;
- an invalid/mutated payload, sibling hash, proof coordinate, root, or malformed Program is accepted;
- a small-range candidate reconstructs or hashes the complete root as a hidden authentication shortcut;
- unsupported graph topology silently falls back inside the timed candidate without being reported as fallback;
- deterministic depth/output/work/range/resource rejection weakens;
- authenticated-unit or source-byte amplification grows with full root size for a fixed cone on a family where the dependency cone itself is fixed;
- the candidate only wins because auth-tree creation, proof preparation, payload materialization, proof-coordinate handling, or required source reads are outside the charged boundary;
- candidate peak temporary state exceeds the bytes needed for the requested cone + authenticated proof payload by an unbounded full-root-sized allocation;
- the candidate is slower than the incumbent authenticated selective-open path on the promoted Law-positive median after warm-up, unless a separately frozen resource reduction is large enough to justify a HOLD for rehabilitation rather than an ADVANCE.

## Frozen accounting law

The timed selective-open candidate must charge, where applicable:

1. dependency-cone planning;
2. source-plan/slice preparation;
3. native/generic cone execution;
4. authenticated leaf-payload preparation;
5. sibling-proof extraction / coordinate preparation;
6. verification and root rebuild;
7. requested-output materialization.

Auth-tree construction may remain outside the timed open operation only because it is persistent index creation, but its **stored bytes** must be reported and cannot disappear from storage economics.

For every row report at minimum:

- logical root bytes;
- requested `(start, length)`;
- exact cone bytes / reconstruction-work bytes;
- physical source bytes touched or modeled source traffic;
- authenticated leaf payload bytes;
- sibling hashes read;
- proof-coordinate bytes/objects where represented;
- stored auth-index bytes;
- candidate and incumbent CPU + wall;
- peak temporary bytes;
- full-root bytes avoided;
- exact semantic/authentication verdict;
- fallback reason, if any.

## Matrix requirements

Use at least three root scales and multiple request sizes/placements per scale. The matrix must include:

- exact add8 Law roots;
- exact xor Law roots;
- sparse-crack add8/xor roots where Surprise intersects and avoids the requested range;
- Fill/Repeat/Literal/Concat mixtures through the same generic reader surface;
- requests wholly inside one Law span;
- requests crossing Law/Surprise and Concat boundaries;
- tiny requests near beginning, middle, end, and exact leaf boundaries;
- a fixed-size request/cone repeated across growing root sizes to test non-scaling behavior;
- unsupported/fusion-ineligible topology that must fail closed or take the explicitly measured incumbent path;
- corrupted payload, sibling digest, proof coordinate, expected root, and malformed/over-budget Program controls.

## Frozen promotion requirements

`ADVANCE_AUTHENTICATED_NATIVE_SELECTIVE_CONE` requires all of the following:

- 100% semantic parity with independent whole-root reference slices on valid rows;
- 100% rejection of hostile authentication/resource controls;
- no whole-root reconstruction or whole-root hash work for sub-root requests in candidate-positive rows;
- fixed requested cone/proof cases do not show source/authenticated-unit work scaling with unrelated root growth;
- median candidate authenticated-open CPU on Law-positive rows is strictly below incumbent authenticated selective-open CPU;
- no individual candidate-positive row exceeds incumbent CPU by more than `1.10x`;
- median physical/modeled data movement on candidate-positive rows is at most `0.75x` incumbent;
- peak temporary state remains bounded by requested-cone/proof needs rather than full-root length;
- stored authentication-index bytes and selective-read amplification are reported, not hidden.

If semantic and locality/resource laws pass but CPU misses, verdict is `HOLD_AUTHENTICATED_NATIVE_SELECTIVE_CONE` and the measured stage owner controls rehabilitation. If integrity/resource semantics fail, verdict is `INVALIDATE_AUTHENTICATED_NATIVE_SELECTIVE_CONE`.

## Hostile-review constraints

Do **not** claim success from the native verifier alone. That causal path has already been shown insufficient because proof preparation can dominate end-to-end selective-open cost.

Do **not** create add8/xor-specific proof or range opcodes. Law-family knowledge may guide cone planning only through ordinary Program topology; authentication remains generic.

Do **not** reuse the whole-root V2 hot-loop benchmark as selective-read authority. Whole-root and authenticated-range economics are different contracts.

Do **not** silently exclude persistent auth-index bytes, payload reads, sibling reads, or proof construction from the resource story.

## Next builder action

Implement one end-to-end benchmark adapter that composes the existing generic `RangeEvaluator` / Program topology, promoted native terminal execution where the exact requested cone is eligible, and existing `AuthTree`/`NativeAuthTree` proof grammar. First preserve byte-identical proof semantics and hostile rejection. Only then optimize preparation/data movement.

The most promising causal optimization target is **interval/cone-proportional preparation**: avoid Python set/object expansion and avoid packing source bytes outside the requested dependency cone. A native verifier is useful only after that preparation bill is also charged and reduced.
