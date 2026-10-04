# v0.30 compact-pack/control attribution result — 2026-09-12

Status: **positive mechanism attribution; research-only, no release/product score credit**.

Source head: `c63ec5783c7f613f98f2187f04fedd53891f1001`  
Hosted run: `34731896744`  
Hosted job: `103656103279`  
Artifact: `v030-compact-control-c63ec5783c7f613f98f2187f04fedd53891f1001` (`sha256:d94ddc853771311544e3af527bccddd344814952013f86a6022ced446fd24a0f`)  
Schema: `cmpct-v030-compact-pack-control-attribution-v1`

## Frozen question

The preregistered referee held every physical payload pack byte-identical and expanded only inherited v0.25 implicit micro-pack membership into the equivalent explicit per-file `plain -> slice(pack, offset, length)` recipes. Both authenticated metadata copies were charged with the same MessagePack + Zstd-12 encoding.

The mechanism was considered material only if implicit membership saved at least **8 KiB** on `01_developer_repository` and **32 KiB** on `08_many_tiny_files`, with strong tree identity preserved.

## Exact hosted result

### `01_developer_repository`

- actual inherited-v0.25 archive: **744,337 B**
- explicit-membership counterfactual: **760,499 B**
- exact stored saving from implicit membership: **16,162 B**
- compact metadata raw / compressed: **58,286 / 22,213 B**
- expanded metadata raw / compressed: **86,804 / 30,294 B**
- physical pack region: **699,795 B**, unchanged
- packs: **21**
- micro groups/files/logical bytes: **14 / 1,260 / 1,348,866 B**
- strong user tree: exact

The preregistered 8 KiB materiality floor passes by **7,970 B**.

### `08_many_tiny_files`

- actual inherited-v0.25 archive: **420,318 B**
- explicit-membership counterfactual: **453,596 B**
- exact stored saving from implicit membership: **33,278 B**
- compact metadata raw / compressed: **121,258 / 23,191 B**
- expanded metadata raw / compressed: **230,656 / 39,830 B**
- physical pack region: **373,820 B**, unchanged
- packs: **3**
- micro groups/files/logical bytes: **3 / 5,000 / 736,546 B**
- strong user tree: exact

The preregistered 32 KiB materiality floor passes by **510 B**.

## Verdict

**`COMPACT_CONTROL_MATERIAL`**.

All frozen gates passed:

- both materiality floors passed;
- both strongly verified user trees remained exact;
- payload and pack bytes were unchanged by construction;
- both primary and tail authenticated metadata copies were charged.

This establishes a causal result: a nontrivial part of the Developer/Tiny-Files Genesis density gap is metadata duplication caused by spelling every small-file membership relation explicitly. It does **not** establish that inherited CMPNX5 syntax should be copied into revision 25 or that the remaining gap is solved.

The attributable savings explain only part of the frozen Genesis deficits:

- Developer: **16,162 B** of the historical **126,265 B** deficit (~12.8%);
- Tiny Files: **33,278 B** of the historical **302,356 B** deficit (~11.0%).

The remaining majority therefore still belongs to payload grouping/context, other control structures, or product-specific overhead. Treating this positive as a complete explanation would be benchmark theater.

## Productization boundary

The next admissible step is a bounded revision-25 representation for **implicit contiguous small-file membership**, not wholesale CMPNX5 reuse. It must preserve the current r25 product contract:

1. exact user-tree and filesystem semantics;
2. authenticated primary/tail recovery;
3. direct path lookup without scanning unrelated groups;
4. bounded group/file/path/count declarations and max decode unit;
5. <=8x selective-read accounting;
6. deterministic encoding and exact economic fallback when the compact form does not win;
7. native/shared-reader parity and update semantics before release credit;
8. no workload/path/extension identity in admission policy.

The existing r25 `implicit-v4` filesystem control solves a different redundancy class: filesystem-semantic metadata relative to authenticated graph-owned regular identities. This new result concerns **content-pack membership recipes**. They must remain separate ownership layers unless a measured one-artifact ablation justifies combining them.

## Strongest self-critique

The Tiny-Files pass clears its preregistered floor by only **510 B**. That is enough to preserve the hypothesis exactly as written, but not enough to justify a loose new wire primitive. Descriptor framing, path-lookup support, auth/recovery duplication, or native-reader complexity can erase the threshold margin quickly.

Therefore the next referee must price the proposed r25 compact membership as a complete authenticated control representation, including direct lookup and recovery duplication, against the current explicit r25 form. A metadata-only theoretical saving is insufficient for promotion.

No aggregate v0.30 score changes. `research/cmpct1`, ONE Genesis, accepted v0.29 and the current Analytics/Office research adjudications remain untouched.
