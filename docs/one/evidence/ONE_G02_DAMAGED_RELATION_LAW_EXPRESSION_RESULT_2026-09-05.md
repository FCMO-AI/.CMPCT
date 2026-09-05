# ONE-G0.2 — naive damaged-relation Law-expression result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **FALSIFIED before density/resource gate completion**

## Evidence identity

- branch head under test: `9e02a6b3249bf513afc280374168e744ced98a2a`
- PR merge SHA executed by Actions: `eba70fa9643a3b918a280b830d98867c01d43402`
- workflow run: `33980311746`
- job: `101344256447`
- artifact: `9973552402`
- artifact SHA-256: `0a673bb3d83f794766a7c529f5e1537ebbbff051fc53ad6cc22ba880296baa60`
- ONE semantic/hostile suite before the benchmark: `83 passed in 0.80s`

## Falsification

The naive compiler expressed every maximal matching run as a ranged `Ref`, every mismatch island as Surprise, and placed every resulting part under one `concat` node. The reader rejected the emitted program during `decode_program` with:

`experiments.one.ir.OneError: concat reference count exceeds hard cap`

The current ONE experimental wire bounds a concat reference count by the program's declared `max_nodes`; this experiment uses the existing `max_nodes=4096` envelope. The failed representation therefore attempted to make one node own more than 4,096 children on the hostile fragmented path.

This is not permission to raise the reader cap. The resource limit is part of the semantics/hardening contract. The naive flat-concat compiler is retired in this form.

## CI integrity finding

The workflow initially appeared green even though Python raised an exception because the command was piped through `tee` without shell `pipefail`. The artifact was only 204 bytes and contained no valid JSON result. Job-log inspection exposed the traceback.

The workflow has been hardened with `set -o pipefail` so benchmark process failure now fails the CI step. A green badge from the original run is explicitly **not** admissible scientific evidence.

## Causal interpretation

The relation Law itself is not falsified. The failure identifies **flat control fanout** as the immediate representation owner. Fragment-local structure can still be expressed by the same generic ONE grammar if the concat cone is hierarchically bounded rather than concentrated in one reader node.

The next Builder is therefore a bounded-fanout concat tree using only existing `concat`, ranged `Ref`, and Surprise semantics. Its fanout is derived from the resource envelope (`sqrt(4096)=64`) rather than fitted to this corpus. The hard 4,096-node envelope remains unchanged.

## Claim boundary

No density, speed, or reader-efficiency result can be claimed from the aborted run. The only valid result is the flat-concat falsification plus the CI integrity defect and its repair.
