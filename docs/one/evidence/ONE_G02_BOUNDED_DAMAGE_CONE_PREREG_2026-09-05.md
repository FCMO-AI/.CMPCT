# ONE-G0.2 — bounded damaged-relation cone preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Status: frozen before result-bearing execution

## Mission lock

The flat damaged-relation Law-expression compiler was falsified because a single generic `concat` exceeded ONE's existing 4,096-reference hard cap on the fragmented hostile path. The cap will not be raised. This Builder asks whether exactly the same Law + Surprise parts can be arranged as a bounded generic concat cone while preserving the original representation/resource gates.

## Non-tuned fanout law

The program envelope is `max_nodes=4096`. Set every generated concat node's maximum fanout to:

`isqrt(max_nodes) = 64`.

This value is derived from the declared global resource envelope, not from corpus timing, fragment spacing, or the first failing size. If more than 64 parts remain, group consecutive parts into concat nodes of at most 64 refs, then recursively group those nodes until one root remains. No reader-visible operation is added and the global 4,096-node, 64-depth, output, and work caps remain unchanged.

## Frozen corpus

Unchanged from the naive Law-expression preregistration:

- sizes: `4, 8, 16, 32, 64, 128, 256 KiB`;
- cases: `shift_plus1_damage_quarter`, `fragmented_every96`;
- previous version stored as Surprise;
- known `+1` predictive relation supplied by the already-proven adjacent relation context;
- maximal matching runs become ranged refs to the previous version;
- maximal mismatch islands remain Surprise.

## Falsifiable hypothesis and gates

The bounded cone must satisfy all original representation gates without weakening them:

1. byte-exact encode/decode/reconstruct on all 14 rows;
2. candidate wire smaller than literal two-version baseline on every row;
3. aggregate candidate wire `<= 0.75x` literal baseline;
4. incremental control/integrity debt `<= 25%` of bytes eliminated on every row;
5. reader reconstruction work `<= 1.75x` literal baseline on every row;
6. materialized bytes `<= 1.25x` literal baseline on every row;
7. total node count `<= max(8, ceil(relation_bytes / 64) + 8)` on every row;
8. every generated concat fanout `<=64`;
9. generated concat-tree depth `<=4`;
10. encoded program remains inside the unchanged 4,096-node hard envelope.

Reference-Python construction + wire-encoding timing is measured over the same 31 interleaved rounds as diagnosis only. It is not product-speed authority and cannot rescue a representation-gate failure.

## Disproof rule

Any gate failure holds this bounded-cone shape. Do not increase fanout, max_nodes, max_depth, or change fragmentation spacing after seeing the result. If control or work debt fails while hard-cap validity succeeds, investigate generic Law/control fusion rather than adding a relation opcode.

## Claim boundary

A pass would show that damaged adjacent relation structure can compile into the existing ONE grammar under current hard resource semantics. It would not establish automatic pair discovery, native creation speed, canonical format promotion, or superiority over v0.29/v0.30.
