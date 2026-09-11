# ONE-G0.2 — minimal-overflow damaged-relation cone preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Status: frozen before result-bearing execution

## Mission lock

The 64-way bounded cone repaired the reader hard-cap failure and achieved `0.59953x` aggregate wire, but failed reader-resource gates because it introduced hierarchy even when the flat relation already fit within ONE's existing 4,096-reference concat envelope. This Builder minimizes hierarchy itself rather than changing any reader limit or density/resource gate.

## Generic minimal-overflow law

Let `C` be the existing concat reference hard cap, equal to the program's unchanged `max_nodes=4096` envelope.

For an ordered list of Law + Surprise parts:

1. if `len(parts) <= C`, emit one ordinary flat concat;
2. otherwise the parent must reduce its child count by exactly `r = len(parts) - C` or more;
3. replacing one contiguous window of `k` parts by one child reduces parent count by `k-1`, so the minimum hierarchy that makes the parent valid uses `k = r + 1`;
4. among all contiguous windows of that exact length, select the window with minimum reconstructed byte length; tie-break by lowest start index;
5. compile only that window into one generic concat child and keep all other refs direct in the parent;
6. if any generated child itself exceeds `C`, apply the same rule recursively inside that child.

This is an exact optimization objective: minimum number of grouped refs first, minimum added materialized bytes second. It contains no corpus-sized threshold and does not change the 4,096-node, work, output, or depth caps.

## Frozen corpus and representation

Unchanged from the two prior damaged-relation gates:

- sizes `4, 8, 16, 32, 64, 128, 256 KiB`;
- cases `shift_plus1_damage_quarter` and `fragmented_every96`;
- source stored as Surprise;
- maximal `+1` matching runs as ranged refs into source;
- mismatch islands as Surprise;
- current root reconstructed only by existing generic concat semantics.

## Frozen gates

All prior representation/resource gates remain unchanged:

- byte-exact encode/decode/reconstruct on all 14 rows;
- every candidate row smaller than literal two-version storage;
- aggregate candidate wire `<=0.75x` literal;
- incremental control/integrity debt `<=25%` of bytes eliminated on every row;
- reader work `<=1.75x` literal on every row;
- materialized bytes `<=1.25x` literal on every row;
- total nodes `<= max(8, ceil(relation_bytes/64)+8)` and `<=4096`;
- generated concat fanout never exceeds `C=4096`;
- generated hierarchy depth `<=4`.

Additionally report per row: number of grouped overflow parts, grouped reconstructed bytes, total concat refs traversed, and hierarchy depth. Reference-Python 31-round build+encode timing remains diagnostic only.

## Disproof

Any gate failure holds this compiler shape. Do not raise `C`, change the corpus, relax materialization/work limits, or select a different grouping objective after result. If this passes resource semantics but Python construction is expensive, the next step is native/fused implementation. If it still fails reader resources, the representation needs stronger Law fusion rather than a looser cap.

## Claim boundary

A pass establishes only that the already-proven damaged adjacent relation can compile into existing ONE grammar with bounded reader resources and useful complete-wire density. Automatic pair discovery, product creation speed, canonical format promotion, and v0.29/v0.30 superiority remain outside scope.
