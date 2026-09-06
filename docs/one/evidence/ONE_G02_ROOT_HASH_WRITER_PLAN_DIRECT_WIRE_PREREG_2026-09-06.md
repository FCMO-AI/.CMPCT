# ONE-G0.2 root-hash writer plan-direct canonical wire — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission Lock

The coarse root-hash-charged writer attribution found no single universal >=25% phase owner, but exposed a stable causal split by structure. Simple/rejected relations become root-hash dominated as size grows, damage-heavy accepted relations are segmentation-heavy, while `fragmented_every96` spends roughly three quarters of its measured post-hash/post-admission time across Program object construction, repeated shape validation, and canonical emission. These three costs all scale with one common cause: materializing thousands of Python `Node`/`Ref` objects only to serialize them immediately.

Hypothesis: for the already-authoritative adjacent-version research writer, compiling the validated native segment plan **directly into the exact canonical ONE0 wire** can remove writer-side object amplification without changing the ONE representation, reader, roots, admission, segmentation, Law/Surprise meaning, locality, or failure semantics. The candidate must produce byte-identical canonical wire to the current `Program -> validate_shape -> growable prevalidated emit` path on every frozen row.

This is not a new opcode and not a hidden codec. It is a writer compiler optimization: the same generic `surprise` and `concat` nodes, same node numbering, same bounded concat hierarchy, same roots and same canonical bytes are emitted without first materializing the equivalent immutable Python IR objects.

## Referee / disproof test

Baseline, fully charged:

`SHA-256 roots -> amortization-safe admission -> native one-pass plan -> Program/Node/Ref construction -> Program.validate_shape -> growable canonical emit`

Candidate, fully charged:

`SHA-256 roots -> identical admission -> identical native one-pass plan -> explicit plan/root structural validation -> direct byte-identical canonical emit`

The candidate is falsified if any wire byte, `WireStats`, root, admission decision, best shift, exact-proof count, plan/oracle result, decoded output, reader work/materialization result, or resource bound differs.

The candidate direct compiler must reject malformed plan state before emission by checking at minimum: non-negative/bounded segment offsets and lengths, exact target coverage, Surprise payload length equality, source reference range bounds, node-count <= `Limits.max_nodes`, bounded concat hierarchy/fanout, root digest shape, and canonical root/reference bounds. Independent `decode_program()` plus `evaluate()` remains mandatory after emission. The ordinary baseline `Program.validate_shape()` remains unchanged.

## Frozen representation algorithm

The candidate must compile exactly the node layout produced by `_program_from_plan` / `_literal_program`:

1. node 0 = previous/source Surprise;
2. one Surprise node, in plan order, for each surprise segment;
3. reference segments point into node 0 using the same offsets/lengths;
4. if the final concat level exceeds `Limits.max_nodes`, add concat hierarchy chunks in the same order and with the same declared lengths as `_program_from_plan`;
5. append the same final concat node for an accepted relation, or the same two-literal-node layout for rejected relations;
6. encode the same default Limits, sorted roots, refs, lengths and SHA-256 digests using the canonical growable wire primitives.

No alternate sparse opcode, bitmap, periodic Law, threshold classifier, changed fanout, changed plan, changed digest, or changed reader behavior is allowed in this experiment.

## Frozen matrix and timing

Reuse `SIZES`, `PRODUCTIVE`, `CONTROLS`, `_relation_cases`, native admission and native one-pass segment plan from `one_g02_end_to_end_direct_emitter_writer.py` exactly.

- sizes: 4/8/16/32/64/128/256 KiB;
- 31 paired rounds;
- alternating A/B-B/A order;
- GC disabled during timing;
- root hashing, admission and segmentation occur inside both timed arms;
- mature performance authority: rows >=16 KiB;
- 4/8 KiB retained as hostile/tiny diagnostics.

## Frozen promotion gates

All semantic/oracle/resource gates must pass, plus:

1. mature productive median candidate/baseline full-writer elapsed <= **0.85x**;
2. at least 12 mature productive rows <= **0.90x**;
3. no mature productive row > **1.03x**;
4. mature control median <= **1.03x**;
5. no control row > **1.08x**;
6. exact canonical bytes and stats on every row;
7. ONE semantic/hostile suite green in exact-source CI.

The 0.85x gate is intentionally material: this experiment duplicates canonical compiler logic and therefore must buy enough whole-writer speed to justify the extra writer implementation surface. A small 2-5% win is a rejection, not a reason to weaken the threshold.

If semantics/resource checks fail: `invalidate_plan_direct_wire_writer`.
If exact but performance gates fail: `reject_plan_direct_wire_writer`.
If all gates pass: `advance_plan_direct_wire_writer` for further native-transfer/hardening only; it does not establish product-native writer authority or v0.29/v0.30 supremacy.

## Hostile Reviewer pre-commit critique

The most serious risk is validation drift: byte identity on known rows is not sufficient if the direct compiler accepts malformed internal state that `Program.validate_shape()` would reject. Therefore explicit structural validation and deliberately malformed-plan unit probes are required in the Builder, not optional hardening after a speed result. The second risk is merely moving allocations from dataclasses to ad-hoc tuples/lists; full-writer elapsed, not object counts, decides promotion. The third risk is optimizing a Python research boundary that later disappears in a native writer. Any win remains scoped until native transfer.

No post-result workload classifier, special case for `fragmented_every96`, relaxed validation, changed canonical wire, or threshold tuning is permitted.
