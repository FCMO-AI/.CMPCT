# v0.30 r25 compact membership product-integration mission — 2026-09-12

Status: **Mission Lock / research-only**. Parent evidence: `V030_R25_IMPLICIT_MEMBERSHIP_WIRE_RESULT_2026-09-12.md`.

## Observation

The independent `membership-v1` wire retained 99.64% / 99.78% of the inherited-v0.25 compact membership saving after fresh framing. But the strongest current r25 product candidate already has a separate authenticated compact path table (`C25CC01`). Repeating each path inside a new membership object would therefore double-own information that r25 already authenticates.

Current r24 S_PACK membership is explicit in each file storage row as `[S_PACK, pack_id, offset, length]`. For a contiguous pack, `offset` is the prefix sum of prior member lengths. The compact control already owns file order and logical paths.

## Falsifiable product hypothesis

On the current locality-bounded r24 physical payload, an r25 compact-control variant can replace explicit per-row S_PACK membership with an authenticated group table:

```text
group := [pack_id, [[file_index, length], ...]]
```

where offsets are cumulative and `file_index` refers to the compact control's already-authenticated file/path table.

This should reduce the **complete two-copy authenticated artifact**, not merely an isolated metadata object, while preserving exact expansion to the mature r24 semantic index and inheriting the same physical payload/locality.

## Frozen construction

For each source:

1. build the strongest current locality-bounded canonical r24 physical artifact;
2. build the existing C25CC01 compact-control profile as the direct r25 control baseline;
3. produce the candidate from the *same r24 source artifact* and keep its entire physical data span byte-identical;
4. start from the existing compact-control object;
5. for S_PACK file rows only, remove explicit `[S_PACK, pack, offset, length]` storage and add one `g` group per owning physical pack containing ordered `[file_index,length]` members;
6. admit a group only when the source offsets are exactly contiguous from zero and cumulative member length equals the owning authenticated blob usize; otherwise leave those rows explicit;
7. compress the whole authenticated control with the same frozen compact-control level portfolio;
8. store two identical authenticated copies using the same header/footer charge as C25CC01;
9. independently expand the candidate back to the exact mature r24 index before mature-reader strong verification.

No path, extension, workload id or benchmark identity may govern group admission. Group eligibility comes only from the authenticated physical S_PACK geometry.

## Workloads / disproof

Use the deterministic normalized `01_developer_repository` and `08_many_tiny_files` inputs already used by the attribution chain.

The hypothesis is disproved if either workload:

- cannot form valid bounded groups from current r24 S_PACK geometry;
- fails exact semantic-index reconstruction or mature-reader strong verification;
- changes one byte of the physical data span;
- weakens current S_PACK locality (<=8x member amplification and existing decode-unit ceiling);
- loses or ties the existing complete C25CC01 artifact;
- fails primary-control corruption recovery through the tail copy.

## Materiality gate

Because C25CC01 already compresses paths/rows and may overlap part of the independent-wire saving, require the *complete artifact* to retain at least half of the independent-wire saving:

- Developer: >= **8,052 B** smaller than C25CC01;
- Tiny Files: >= **16,602 B** smaller than C25CC01.

These floors are frozen before execution and are not to be tuned after observing the result.

PASS: `R25_MEMBERSHIP_COMPLETE_ARTIFACT_EARNED`.

FAIL: `RETIRE_OR_REDESIGN_R25_MEMBERSHIP_INTEGRATION`.

## Evidence required

The receipt must report baseline/candidate complete stored bytes, control raw/compressed bytes, exact saving, pack/group/member counts, source/candidate data-span hashes, semantic-index equality, strong tree identity, primary-corruption tail recovery, S_PACK max member amplification/decode unit, create transform CPU/wall and control-open/expand CPU/wall. RSS is diagnostic unless isolated fresh-process measurement is added; no RSS claim may be inferred from process-global `ru_maxrss` deltas.

PASS remains research-only. It earns a real format/native/update integration task, not a release number.
