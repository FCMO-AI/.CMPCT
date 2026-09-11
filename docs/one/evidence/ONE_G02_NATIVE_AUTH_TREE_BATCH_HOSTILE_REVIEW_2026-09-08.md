# ONE-G0.2 native auth-tree batch hostile review — 2026-09-08

## Mission Lock / Referee

Authority remains the ONE canon and Engineering Grid. This lane rehabilitates creation cost for the already-feasible generic authenticated-range tree; it does not add a new representation mechanism or relax integrity/selective-read requirements.

Frozen hypothesis and thresholds live in `docs/one/prereg/ONE_G02_NATIVE_AUTH_TREE_BATCH_PREREG_2026-09-08.md`.

## Builder review

The candidate preserves the exact existing grammar:

- `ONE-L\0 || <QQ little-endian> || payload` for leaves;
- `ONE-P\0 || <I little-endian> || left || right` for parents;
- odd parent inputs duplicate the left digest exactly as the Python reference does;
- `ONE-R\0 || <QI little-endian> || tree_root` for the committed root.

Every tree digest is emitted in level order into one packed buffer, including the one-node tree root. The root commitment remains separate. No hash is skipped.

Native compilation/loading occurs before timed repetitions. The candidate's bytes->ctypes input copy and packed-output conversion are charged. The control charges its existing Python tuple/bytes object construction. This asymmetry is intentional because a writer sidecar can consume the packed native hashes directly; requiring the candidate to reconstruct the control's Python object forest would reintroduce the boundary this experiment is testing.

## Hostile Reviewer

### Semantic attack

`tests/one/test_native_auth_tree.py` compares roots, every level digest, node count, and stored-index byte accounting across empty/tail/uneven roots and all four passing leaf sizes. Any mismatch invalidates the result.

### Falsifier attack

`tests/one/test_native_auth_tree_batch.py` proves that:

- a complete green matrix advances;
- 0.501x on either large-row wall or CPU blocks advancement;
- 0.751x on a small-row wall blocks advancement;
- semantic disagreement invalidates;
- a missing row cannot exploit vacuous `all()` behavior;
- the 64 KiB / 256 KiB sizes and 80/96/112/192 leaves are frozen.

### Timing attack

Paired arms alternate first position. The previous result reference is cleared before either next arm's clocks start, and the current result is retained until both clocks stop, preventing teardown from being charged to the opposite arm.

### Portability attack

The C kernel currently uses system OpenSSL/libcrypto. This is **research-only causal evidence**, not a portability promotion. A green result proves that Python dispatch/object overhead is avoidable while preserving the grammar. Product adoption still requires a portable backend/dependency decision and broader resource evidence.

### Memory attack

Packed node bytes are reported, but process RSS is not measured. No RSS claim is permitted from this lane.

### Scope attack

This lane does not time proof construction/verification, archive placement, filesystem traversal, decode, or full product ingest. It only decides whether native level batching is a worthwhile creation primitive for the existing generic authentication tree.

## Strongest pre-result concern

OpenSSL's deprecated low-level SHA256 API may emit compiler warnings and could eventually disappear from a future dependency configuration. That is acceptable for this falsifier because exact semantics are independently checked and compilation failure is a clean experimental failure, but it is not an acceptable long-term portability story.

No result from before this hostile review should be used to move thresholds or claim promotion.
