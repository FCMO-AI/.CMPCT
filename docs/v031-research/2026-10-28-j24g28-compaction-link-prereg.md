# J24G28 prereg — compaction of valid symlink-target bytes

**Pre-experiment source:** `main@80c358f8824ec1b20d349c92ed94c898090969b0`, `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, `src/cmpct/transactions.py` blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Product source unchanged, v0.30.0/r24. The actual physical result is not yet known. [Issue #718](https://github.com/FCMO-AI/.CMPCT/issues/718) contains the source-level prediction and independent owner check.

## PARETOBONK and decision

#496/#500 already own the strict tree-topology scientific question, so the independent J24G27b API candidate #717 was closed without merge. This **different** new question concerns valid archived symlink semantics during `compact_archive`. Alternatives: change published extractor default (unsafe), silently ignore unsupported links (not exact), implement a new no-materialization compact engine before proof (too expensive), or build a physical falsifier on an authentic Builder archive with a strong valid safe-symlink control (chosen).

## Prediction, controls and kill

P1: Builder accepts and Reader reads/verifies a source archive with a `K_SYMLINK` to an absolute target or a parent-relative `..` target. P2: `compact_archive` on those genuine archives raises `IOError` because it calls `extractall` with default `safe_symlinks=True`; it must not mutate the external target. P3: compaction of a safe-relative symlink succeeds, preserving target bytes and ordinary file bytes. P4: original archive remains unchanged and valid regardless of compaction failure.

**Falsifier:** Builder/read already rejects those targets; compaction succeeds with exact symlink bytes despite extraction gate; or safe-relative case fails equally for unrelated cause. If true, the issue is a source/prod feature gap, not evidence of an attack or a valid general fix. No promotion/benchmark claim until a separate owned implementation establishes safe restoration and resource/metadata economics.

## Evidence tier and scope

Dedicated source-bound first-party Builder+Reader roundtrip witness with raw JSON/pytest original results is a direct product-baseline reproduction. This is not a source-independent golden; it cannot prove full r24 semantics. Hold source IDs, archive SHA, original unchanged input bytes and external sentinel. Code change is tests/research/CI only; `src/`, native core, normative release/frozen benchmarks and Discovery STATE unchanged. Record fail and skips honestly, including Windows symlink-privilege limitations.