# ONE-G0.2 validated authenticated selective lifecycle — preregistration

Date: 2026-09-09  
Status: frozen before result-bearing execution

## Mission lock

Two promoted facts now need one systems-level falsifier:

1. authenticated native selective cones can reconstruct and authenticate Law-positive ranges without whole-root work; and
2. complete Program validity can be proven once and retained economically as a sealed immutable authority, with compact node-length proof state admitted only when it is actually smaller.

The next question is not whether either component works in isolation. It is whether the complete repeated-read lifecycle pays:

`open once -> full Program validation -> retain validation authority -> repeated authenticated selective cone reads`

without weakening ONE semantics or hiding one-time/open cost.

## Hypothesis

For repeated selective reads of the same immutable Program, one complete validation at open time plus a retained `ValidatedProgram` will amortize below the current raw-Program path that repeats full preflight per request, while preserving exact authenticated range semantics and cone-proportional data work.

Large unrelated-but-valid graph state should strengthen the candidate because repeated reads must not repay O(graph) validation. Tiny graphs and one-shot reads are the hostile economic controls: the candidate may not claim victory by ignoring its one-time compact/open overhead.

## Frozen candidate and comparator

Comparator:

`raw Program -> reconstruct_authenticated_native_range(...)` for every request.

This is the promoted authenticated native cone mechanism with complete per-request preflight.

Candidate:

`validate_program_snapshot_compact(program)` exactly once, then `reconstruct_validated_authenticated_native_range(...)` for every request.

The open timer includes complete shape/preflight validation plus any compact-certificate construction/admission. Authentication tree construction remains pre-existing persistent archive/index state for both arms; its stored bytes are reported equally and are not credited as zero-cost candidate work.

## Frozen matrix

- root size: 128 KiB;
- families: add8, xor, add8_crack, xor_crack, literal, fill, concat;
- total Program node counts: base graph, 64, 512, 2,048, 4,096 nodes by appending unreachable but valid one-byte Fill nodes;
- repeated requests per open: 1, 4, 16, 64;
- requests cycle across beginning, leaf boundary, middle-crossing and end ranges;
- authentication leaf size: 4 KiB;
- paired median timing rounds: 5.

Unreachable nodes are intentional. ONE validity is global, so they must be validated once even when no requested cone reaches them. They must not be revalidated on every request after a sealed authority exists.

## Hard semantic/safety gates

All must pass:

1. candidate and comparator return identical requested bytes for every request;
2. every returned range matches the full reference root slice;
3. authentication remains against the same expected AuthTree root;
4. no whole-root reconstruction/hash shortcut appears in positive requests;
5. candidate uses the sealed validated snapshot, not caller-mutable Program state;
6. >uint64-valid logical programs retain ordinary validation authority rather than narrowing semantics;
7. inherited malformed/authentication/resource failures remain fail-closed.

Any semantic/authentication failure is `INVALIDATE_VALIDATED_AUTHENTICATED_LIFECYCLE`, not HOLD.

## Frozen economic gates

The experiment reports complete lifecycle CPU as:

`open_once_cpu + sum(request_cpu)`

for the candidate versus:

`sum(raw_per_request_cpu)`

for the comparator.

Promotion requires:

- semantic/safety gates all pass;
- at 4,096 total nodes, retained validation proof state <= 0.40x ordinary preflight state;
- median candidate/comparator lifecycle CPU for request_count >= 4 <= **0.75x**;
- median candidate/comparator lifecycle CPU for request_count >= 16 <= **0.50x**;
- worst candidate/comparator lifecycle CPU for one-shot rows <= **1.30x**;
- every 4,096-node row with request_count >= 4 must be faster than comparator (<1.0x);
- authenticated cone/source/proof movement per request must remain identical to the promoted validated/raw cone semantics; validation amortization may remove CPU, not alter requested data work.

The gates are fixed before hosted execution. Do not relax them after seeing results.

## Interpretation law

`ADVANCE_VALIDATED_AUTHENTICATED_LIFECYCLE` means reusable full-Program validation has crossed the complete repeated-read economic boundary and may become the preferred shared-open research reader authority.

`HOLD_VALIDATED_AUTHENTICATED_LIFECYCLE` means semantics are exact but open/certificate/request economics do not yet satisfy the frozen lifecycle gates. The result must identify whether debt belongs to open proof construction, certificate lookup, native range planning, proof preparation, or verification.

No wire, Law, Surprise, integrity, recovery, resource or portability rule changes in this experiment.

## Next step after success

If this advances, stop benchmarking reusable validation in isolation. The next reader work is generic economic route admission: choose the native authenticated cone route only when its topology/request economics beat the simpler path, without workload names or Law-specific proof formats.
