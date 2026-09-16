# v0.30 r25 implicit contiguous membership mission — 2026-09-12

Status: **research-only Mission Lock**. No canonical-format, selector, version or ONE authority change.

## Evidence entering this mission

The frozen compact-control attribution proved that inherited v0.25 implicit micro-pack membership saves **16,162 B** on `01_developer_repository` and **33,278 B** on `08_many_tiny_files` while every physical payload byte remains identical and both authenticated metadata copies are charged. This is material but explains only a minority of the corresponding Genesis deficits.

Revision-25 already has `implicit-v4` filesystem control. That grammar removes redundant filesystem-semantic fields when the authenticated content graph already owns regular path/size/SHA identity. This mission is deliberately orthogonal: it asks whether **physical content-pack membership** can be represented implicitly without repeating one full `plain -> slice(pack, offset, length)` recipe per small regular file.

## Falsifiable hypothesis

A bounded `membership-v1` grammar that records one authenticated pack id plus ordered `[path,length]` members, derives offsets cumulatively, and builds an in-memory path->(pack,offset,length) map at metadata decode time can preserve exact membership semantics and resource bounds while retaining at least **75%** of the already-measured v0.25 compact-control stored-byte saving on both Developer and Tiny Files.

The 75% hurdle deliberately reserves 25% of the historical saving for product-specific framing/bounds instead of assuming CMPNX5 wire syntax transfers for free.

## Frozen grammar candidate

Research wire object:

```text
[1, groups]

group := [pack_id, [[path, length], ...]]
```

Rules:

- `1` is the research grammar version;
- `pack_id` is a bounded non-negative integer referring to an already-authenticated physical pack;
- paths are canonical unique relative paths under the existing r25 path policy;
- lengths are bounded non-negative integers;
- offsets are implicit prefix sums within one group;
- cumulative member length must equal the authenticated pack uncompressed size supplied by the owning content profile;
- no member may overlap another because offsets are derived monotonically;
- total groups, members, path bytes, logical bytes and decoded control bytes are bounded by reader policy;
- decoder constructs a path lookup map once while validating the authenticated control, so `read_member(path)` does not scan unrelated groups after open;
- duplicate paths, duplicate pack ids, unknown packs, overflow, malformed shape, over-limit declarations or size mismatch fail closed.

The research grammar does **not** encode codec, compressed offset, integrity hash or recovery pointers. Those remain owned by the authenticated pack table/content profile and must never be duplicated into membership-v1 merely to make the benchmark self-contained.

## Referee

On the same deterministic normalized Developer and Tiny-Files inputs used by the causal attribution:

1. build and strong-verify inherited v0.25 only as a source of exact pack/member relationships;
2. extract each implicit micro group and its authenticated physical pack uncompressed size;
3. encode `membership-v1` with MessagePack;
4. decode it under explicit resource ceilings and reconstruct exact per-path `(pack, offset, length)` recipes;
5. compare reconstructed recipes byte-for-semantics with the explicit counterfactual from the prior attribution;
6. compare compressed control bytes under the same Zstd-12 metadata codec;
7. charge primary+tail copies plus a fixed **16-byte grammar/framing reserve per copy** that is absent from CMPNX5, rather than granting a free product wrapper;
8. require strong tree identity of the source artifact and exact pack payload identity;
9. run malformed-control unit cases for duplicate path/pack, unknown pack, cumulative-size mismatch, integer/path/entry limits and trailing shape.

## Pass gate

For **both** workloads:

- semantic reconstruction: exact;
- hostile malformed cases: all fail closed;
- direct lookup map: complete and unique;
- payload packs: byte-identical;
- charged stored saving after the 32-byte total framing reserve: >= 75% of the prior measured implicit-micro saving.

Expected minimum retained savings:

- Developer: **12,121 B** (floor of 75% of 16,162 B);
- Tiny Files: **24,958 B** (floor of 75% of 33,278 B).

PASS verdict: `R25_IMPLICIT_MEMBERSHIP_WIRE_EARNED`.

FAIL verdict: `RETIRE_R25_IMPLICIT_MEMBERSHIP_WIRE`.

## Promotion boundary

PASS earns only a product-integration Builder. It does not modify `docs/FORMAT.md` or the canonical r25 reader by itself. Integration must then prove complete-artifact economics, authenticated head/tail recovery, <=8x selective access, update/delete/rename behavior, native/shared-reader parity, portability and exact r24 fallback.

No path extension, workload identity or benchmark hash may govern admission. The final product selector must compare exact complete candidate bytes and retain the existing form on ties/losses.
