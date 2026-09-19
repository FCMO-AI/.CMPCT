# v0.30 compact-pack/control attribution mission — 2026-09-12

Status: **research-only read-only attribution** for the second-tier Genesis loss lane. No format, selector, release or ONE authority changes.

## Why this lane

The frozen Genesis deficit map separates the six v0.30 density losses into two causal families. Office/Analytics are dominated by stream-federation/representation work. `08_many_tiny_files` and `01_developer_repository` have **zero stream pool** in inherited v0.25 and instead show compact packing/control structure:

- many tiny files: v0.29 **420,318 B**, frozen v0.30 **722,674 B**, deficit **302,356 B**; inherited v0.25 stats `packs=4`, `micro_groups=3`;
- developer repository: v0.29 **744,337 B**, frozen v0.30 **870,602 B**, deficit **126,265 B**; inherited v0.25 stats `packs=22`, `micro_groups=15`.

v0.25's implicit micro-pack index omits redundant `plain/slice/pack/offset` recipes when a pack is exactly the concatenation of independently named small files. The first question is how many real stored bytes that representation saves, independently of payload compression.

## Falsifiable hypothesis

On the exact normalized neutral-hostile developer and many-tiny workloads, expanding every v0.25 implicit micro-pack entry into the equivalent explicit per-file `plain -> slice(pack,offset,length)` metadata, while leaving every physical pack and payload unchanged, will materially increase authenticated stored bytes.

The mechanism is considered **material** only if the compact micro index saves at least:

- **32 KiB** on `08_many_tiny_files`, and
- **8 KiB** on `01_developer_repository`.

These are deliberately far below the full Genesis deficits; passing means the control representation owns a measurable component worth productizing, not that it explains the entire gap.

## Referee contract

1. Generate the exact deterministic neutral-hostile corpus and normalize it with the repository's frozen repair hooks.
2. Build inherited CMPNX5/v0.25 separately for `01_developer_repository` and `08_many_tiny_files` with its existing writer. Strong-verify and tree-hash each artifact.
3. Read the authenticated metadata from the built artifact without modifying payload packs.
4. Construct a counterfactual metadata object by replacing every `micro` entry with the exact explicit `files` recipe it implies: `['plain', [['slice', pack_index, offset, length]], length]`. Preserve all other metadata fields byte-for-semantics unchanged.
5. Re-encode both metadata objects with the same msgpack settings and Zstd level 12. Because CMPNX5 stores authenticated primary and tail metadata copies, charge the exact archive counterfactual as `actual_archive_bytes + 2 * (expanded_meta_comp - compact_meta_comp)`. Header/footer and all payload bytes remain identical.
6. Report micro groups, micro file count/logical bytes, compact/expanded raw+compressed metadata bytes, exact head+tail stored saving, pack/payload bytes and verified tree identity.
7. No path/extension/workload identity may change representation choices; workload names exist only to select the two frozen diagnostic inputs.
8. This is attribution only. Passing does not authorize copying CMPNX5 wholesale into r25.

## Decision

- **PASS — `COMPACT_CONTROL_MATERIAL`:** both workload-specific preregistered savings floors pass. Next step is a bounded r25 representation proposal for implicit contiguous small-file membership, with direct-path lookup, authenticated metadata, recovery, native parity and update semantics paid explicitly.
- **FAIL — `MICRO_INDEX_NOT_PRIMARY_ENOUGH`:** either floor fails. Preserve the exact negative and attribute the remaining tiny/developer gap to payload grouping/context or another control structure before implementing a new reader-visible primitive.

This lane is independent of the Analytics BytePlane work and does not alter `research/cmpct1` or the frozen ONE Genesis result.
